"""Test semantic understanding of data analysis questions."""

import json
from datetime import datetime
from pathlib import Path

from api.barb import Barb

QUESTIONS = [
    # Агент должен понять сессию
    "Какой был объем утром в понедельник?",
    "Покажи хай лоу за ночную торговлю вчера",
    "Что было на открытии в пятницу?",
    "Средний рейндж перед закрытием",

    # Агент должен понять период
    "Как торговали на прошлой неделе?",
    "Объемы за последний месяц",
    "Волатильность в январе",

    # Агент должен учесть праздники/события
    "Покажи объемы в день NFP",
    "Как вел себя рынок перед FOMC?",
    "Сравни обычные пятницы и экспирации",

    # Агент должен понять метрику
    "Насколько большие были движения?",
    "Какая была активность утром?",
    "Покажи разброс цен за день",
]


def run_test():
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
        "test_type": "semantic_understanding",
        "total_questions": len(QUESTIONS),
        "total_cost": total_cost,
        "results": results,
    }

    path = Path(__file__).parent / "results" / f"semantic_{timestamp}.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nTotal cost: ${total_cost:.6f}")
    print(f"Saved to: {path}")


if __name__ == "__main__":
    run_test()
