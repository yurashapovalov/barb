"""E2E test scenarios for Barb.

Each scenario is a dict with:
- name: descriptive name
- instrument: symbol (default: "NQ")
- messages: list of user messages (conversation turns)
- expect_tool: whether tool calls are expected
- expect_data: whether data blocks are expected
"""

SCENARIOS = [
    {
        "name": "Gap fade — стоит ли торговать закрытие гэпа",
        "messages": [
            "Какой процент гэпов на открытии закрывается в тот же день?",
            "да, только считай гэпы больше 20 пунктов",
            "а отдельно для гэпов вверх и вниз?",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Пятничный bias — стоит ли держать позицию",
        "messages": [
            "какой средний range последнего часа торгов по пятницам за 2024 год по сравнению с другими днями?",
            "давай",
            "а в какой процент пятниц цена закрытия была ниже цены на 15:00?",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "ORB — когда формируется хай дня",
        "messages": [
            "In what percentage of days is the high or low of the RTH session set within the first 30 minutes?",
            "yes",
            "show me by quarter for 2024",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Volatility clustering — чего ждать завтра",
        "messages": [
            "после дней с range больше 300 пунктов какой средний range на следующий день?",
            "да, RTH",
            "покажи эти дни и что было на следующий день",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Сезонность объёма — когда не торговать",
        "messages": [
            "покажи средний дневной объём по месяцам за последние 2 года",
            "давай, только ETH сессию используй",
            "а по дням недели?",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Inside day breakout — стоит ли ждать движение",
        "messages": [
            "сколько inside days было за 2024-2025?",
            "да, RTH",
            "какой средний range на следующий день после inside day?",
            "покажи топ-10 самых сильных движений после inside day",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Торговые дни — count",
        "messages": [
            "сколько торговых дней в марте 2025?",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Торговые дни — покажи",
        "messages": [
            "покажи торговые дни в марте 2025",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Knowledge — NR7",
        "messages": [
            "What is NR7?",
        ],
        "expect_tool": False,
        "expect_data": False,
    },
    {
        "name": "Большие падения — фильтр с контекстом",
        "messages": [
            "собери за 2024-2025 год все дни когда котировки понизились на 2.5% и более",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Backtest — RSI mean reversion",
        "messages": [
            "протестируй стратегию: покупай когда RSI ниже 30, стоп 2%, тейк 3%, максимум 5 дней",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Backtest — hammer after selloff, multi-turn",
        "messages": [
            "протестируй стратегию: лонг после 3 дней падения подряд если закрытие в верхней половине диапазона дня. стоп 1.5%, тейк 3%, максимум 5 дней, проскальзывание 0.5. RTH, вся история",
            "а теперь прогони только на 2022-2025 чтобы проверить out-of-sample",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Затишье перед бурей — squeeze detection",
        "messages": [
            "бывает что рынок затихает а потом резко двигается? как часто это происходит?",
            "за последние 2 года покажи",
            "какие самые сильные движения были после затишья?",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Backtest — breakeven after 2 days",
        "messages": [
            "протестируй лонг после 3 красных дней, стоп 2%, тейк 4%, но если через 2 дня в плюсе — перенеси стоп на вход. RTH, 2023-2025",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Backtest — trailing stop trend following",
        "messages": [
            "протестируй стратегию: лонг когда цена закрылась выше 20-дневного максимума, трейлинг стоп 2%, максимум 10 дней. RTH, 2023-2025",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Backtest — gap fill with RSI filter",
        "messages": [
            "Покупай когда гэп вниз больше 1% и вчерашний RSI был выше 50. Таргет — закрытие гэпа (prev(close)). Стоп 1.5%. Максимум 1 день. Только RTH.",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Session high/low by hour — ETH time distribution",
        "instrument": "CL",
        "messages": [
            "Using the latest 56000 minute bars, find which hour most often marks the high or low of the ETH trading session",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Backtest limitation — intraday entry timing",
        "instrument": "CL",
        "messages": [
            "During the last 50 ETH sessions, what is the optimal time to enter if stop loss is 50 points and target is 100 points, breakeven 20 min after entry?",
        ],
        "expect_tool": True,
        "expect_data": True,
    },
    {
        "name": "Honesty — unknown indicator",
        "instrument": "CL",
        "messages": [
            "Show me TD Sequential countdown signals on daily chart for the last 6 months",
        ],
        "expect_tool": False,
        "expect_data": False,
    },
    {
        "name": "Honesty — unsupported backtest features",
        "messages": [
            "Backtest a strategy: enter long at 10:00 AM each day, trailing stop 1%, move stop to breakeven after 15 minutes, scale out 50% at +1% and hold rest to +2%",
        ],
        "expect_tool": False,
        "expect_data": False,
    },
    {
        "name": "Hallucination — don't list unseen dates (long conversation)",
        "messages": [
            "last fifty sessions, between 6am and into the close — at what time is the high or low of the session typically set? show by hour",
            "yes, ETH",
            "now show the top 20 exact minutes of RTH when high or low occurs most often, last 50 sessions",
            "on last 22 ETH sessions what exact time (up to minute) was the session high and low? show by frequency descending",
            "good. now group it into 10 minute intervals, descending frequency",
            "over last 22 sessions: on which days did the session low occur between 9:45 and 10:15 AM? and what was the move from that low to session close?",
            "same but for session high between 10:15 and 10:45 AM",
        ],
        "expect_tool": True,
        "expect_data": True,
        "no_date_list": True,
    },
]
