-- holiday_calendar is redundant with exchange — holidays are exchange-level
alter table public.instruments drop column holiday_calendar;
