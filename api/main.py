"""Barb API."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if os.getenv("ENV") == "production":
    import json as json_lib

    class _JSONFormatter(logging.Formatter):
        def format(self, record):
            return json_lib.dumps({
                "ts": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
            })

    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.root.handlers = [handler]
    logging.root.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

log = logging.getLogger(__name__)

app = FastAPI(title="Barb", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}
