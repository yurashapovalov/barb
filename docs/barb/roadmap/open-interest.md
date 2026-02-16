# Open Interest

## Что

Сейчас OI дропается при ingest daily данных (`scripts/update_data.py` — `KEEP_COLS` не включает `oi`). Provider (FirstRateData) отдаёт OI в daily CSV, но мы его выбрасываем.

## Зачем

OI — третья ось данных после price и volume. Классический анализ:

- Растущая цена + растущий OI → сильный тренд (новые деньги входят)
- Растущая цена + падающий OI → слабый рост (short covering)
- Падающая цена + растущий OI → сильное давление на продажу
- Падающая цена + падающий OI → лонги выходят, давление слабеет

Также: ликвидность контракта, отслеживание ролловера, подтверждение volume сигналов.

## Что нужно

1. Добавить `oi` в `KEEP_COLS` в `scripts/update_data.py`
2. Пересобрать все daily parquet: `python scripts/update_data.py --type futures --period full --force`
3. Добавить `oi` в `load_data()` select list (`barb/data.py:27`)
4. Добавить функции: `oi()`, `oi_change()`, возможно `oi_ratio(n)`
5. OI есть только в daily данных — minute parquet не затрагивается
