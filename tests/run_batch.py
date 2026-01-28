"""Batch test runner for domain knowledge questions."""

import json
from datetime import datetime
from pathlib import Path

from api.barb import Barb

QUESTIONS = [
    # Instrument
    "What is NQ?",
    "На какой бирже торгуется NQ?",
    "What's the tick size for NQ?",
    "Какой таймзон у данных?",
    # Data
    "За какой период есть данные?",
    "What columns are in the data?",
    "Сколько лет данных доступно?",
    # Sessions
    "When is RTH session?",
    "Что такое OVERNIGHT сессия?",
    "What sessions are available?",
    "Когда азиатская сессия?",
    # Holidays
    "Когда рынок закрыт в 2026?",
    "Are there any early close days?",
    "Рынок открыт на Рождество?",
    # Events
    "When is NFP?",
    "Когда FOMC?",
    "What high-impact events affect NQ?",
    "Когда экспирация опционов?",
]


def run_batch():
    barb = Barb()
    results = []
    total_cost = 0.0

    for q in QUESTIONS:
        print(f"Q: {q}")
        resp = barb.ask(q)
        print(f"A: {resp.answer[:100]}...")
        print(f"Cost: ${resp.cost.total_cost:.6f}\n")

        results.append({
            "question": q,
            "answer": resp.answer,
            "cost": resp.cost.model_dump(),
        })
        total_cost += resp.cost.total_cost

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": timestamp,
        "total_questions": len(QUESTIONS),
        "total_cost": total_cost,
        "results": results,
    }

    path = Path(__file__).parent / "results" / f"batch_{timestamp}.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nTotal cost: ${total_cost:.6f}")
    print(f"Saved to: {path}")


if __name__ == "__main__":
    run_batch()
