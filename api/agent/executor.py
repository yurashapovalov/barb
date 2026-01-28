"""Safe code executor."""

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
    """Execute generated Polars code safely."""

    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)

    def execute(self, code: str) -> ExecutionResult:
        """Execute code and return result."""
        try:
            # Safe globals - minimal builtins
            safe_globals = {
                "__builtins__": {
                    "len": len, "range": range, "enumerate": enumerate,
                    "zip": zip, "map": map, "filter": filter,
                    "sorted": sorted, "min": min, "max": max, "sum": sum,
                    "abs": abs, "round": round,
                    "int": int, "float": float, "str": str, "bool": bool,
                    "list": list, "dict": dict, "tuple": tuple, "set": set,
                    "print": print,
                },
                "pl": pl,
            }

            # Load data
            safe_locals = {}
            for parquet_file in self.data_dir.glob("*.parquet"):
                instrument = parquet_file.stem.lower()
                safe_locals[f"df_{instrument}"] = pl.scan_parquet(parquet_file)

            # Shortcut: df = df_nq if only one instrument
            if len(safe_locals) == 1:
                safe_locals["df"] = list(safe_locals.values())[0]

            exec(code, safe_globals, safe_locals)

            if "result" not in safe_locals:
                return ExecutionResult(False, None, "No 'result' variable")

            output = safe_locals["result"]
            if isinstance(output, pl.DataFrame):
                output = output.to_dicts()
            elif isinstance(output, pl.LazyFrame):
                output = output.collect().to_dicts()

            return ExecutionResult(True, output)

        except Exception as e:
            return ExecutionResult(False, None, f"{type(e).__name__}: {e}")
