# ADR-003: Gemini как LLM

## Контекст

Нужно было выбрать LLM провайдер для аналитического ассистента. Основные кандидаты: Gemini, OpenAI (GPT), Anthropic (Claude).

## Решение

Google Gemini. Сейчас gemini-2.5-flash-lite как дефолт, gemini-3-flash для сложных задач.

## Почему так

- 1M контекстное окно — не нужно сложных стратегий управления контекстом
- Implicit caching — автоматически кэширует повторяющийся system prompt, экономит токены
- Цена: flash-lite $0.10/1M input — в разы дешевле GPT-4o и Claude
- Thinking tokens для сложных аналитических задач
- Хороший function calling для tool use

## Альтернативы

- OpenAI GPT-4o — дороже, 128K контекст, лучше экосистема
- Anthropic Claude — дороже, 200K контекст, лучше reasoning
- Self-hosted (Llama) — бесплатно, но нужна инфра и качество хуже

## Последствия

- Vendor lock-in на Google AI SDK (`google-genai`)
- Если Gemini деградирует — миграция потребует переписать assistant/chat.py
- Pricing может измениться
