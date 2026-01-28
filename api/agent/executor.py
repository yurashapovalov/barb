"""Safe code executor for running generated analysis code."""

import polars as pl
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from api.config import get_settings


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: Any
    error: str | None = None


class CodeExecutor:
    """Execute generated Python/Polars code safely."""

    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)

    def _get_safe_globals(self) -> dict:
        """Create a restricted global namespace for code execution."""
        return {
            "__builtins__": {
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "reversed": reversed,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "print": print,
                "isinstance": isinstance,
                "type": type,
            },
            "pl": pl,
            "Path": Path,
            "DATA_DIR": self.data_dir,
        }

    def _get_safe_locals(self) -> dict:
        """Create local namespace with pre-loaded data."""
        locals_dict = {}

        # Pre-load all parquet files as lazy frames
        for parquet_file in self.data_dir.glob("*.parquet"):
            instrument = parquet_file.stem
            locals_dict[f"df_{instrument.lower()}"] = pl.scan_parquet(parquet_file)

        # Convenience: if only NQ exists, also expose as just 'df'
        if "df_nq" in locals_dict and len(locals_dict) == 1:
            locals_dict["df"] = locals_dict["df_nq"]

        return locals_dict

    def execute(self, code: str) -> ExecutionResult:
        """Execute code and return result."""
        try:
            safe_globals = self._get_safe_globals()
            safe_locals = self._get_safe_locals()

            # Execute the code
            exec(code, safe_globals, safe_locals)

            # Look for 'result' variable in locals
            if "result" in safe_locals:
                output = safe_locals["result"]

                # Convert Polars DataFrame to dict for JSON serialization
                if isinstance(output, pl.DataFrame):
                    output = output.to_dicts()
                elif isinstance(output, pl.LazyFrame):
                    output = output.collect().to_dicts()

                return ExecutionResult(success=True, output=output)

            return ExecutionResult(
                success=False,
                output=None,
                error="No 'result' variable found in code output"
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                output=None,
                error=f"{type(e).__name__}: {str(e)}"
            )
