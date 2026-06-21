from __future__ import annotations

from datetime import date


PROMPTS_OF_THE_DAY = {
    "ru": (
        (
            "Ты — стратегический аналитик и эксперт по принятию решений.\n\n"
            "Цель: помоги мне принять обоснованное решение по задаче: "
            "[ОПИШИТЕ ЗАДАЧУ].\n\n"
            "Контекст: [КОНТЕКСТ].\n"
            "Ограничения: [БЮДЖЕТ, СРОКИ, РЕСУРСЫ].\n\n"
            "Сначала задай до 5 критически важных уточняющих вопросов. Затем "
            "предложи 3 реалистичных варианта, сравни их по выгоде, риску, "
            "стоимости и скорости, назови скрытые допущения и дай итоговую "
            "рекомендацию с пошаговым планом действий."
        ),
        (
            "Ты — senior product manager и исследователь пользователей. "
            "Проведи глубокий разбор идеи: [ИДЕЯ]. Определи целевую аудиторию, "
            "главную проблему, ценностное предложение, риски, конкурентов и "
            "минимальный проверяемый MVP. Сформируй гипотезы, метрики успеха, "
            "план интервью и эксперименты на ближайшие 14 дней. Не выдумывай "
            "данные; явно отмечай предположения."
        ),
    ),
    "en": (
        (
            "You are a strategic analyst and decision-making expert.\n\n"
            "Goal: help me make a well-supported decision about: [TASK].\n\n"
            "Context: [CONTEXT].\n"
            "Constraints: [BUDGET, DEADLINE, RESOURCES].\n\n"
            "First ask up to five critical clarifying questions. Then propose "
            "three realistic options, compare benefit, risk, cost and speed, "
            "surface hidden assumptions, and provide a final recommendation "
            "with a step-by-step action plan."
        ),
        (
            "You are a senior product manager and user researcher. Analyze "
            "this idea deeply: [IDEA]. Define the target audience, core "
            "problem, value proposition, risks, competitors and smallest "
            "testable MVP. Produce hypotheses, success metrics, an interview "
            "plan and experiments for the next 14 days. Do not invent data; "
            "label every assumption explicitly."
        ),
    ),
}


def prompt_of_the_day(language: str, today: date | None = None) -> str:
    selected_language = "en" if language == "en" else "ru"
    prompts = PROMPTS_OF_THE_DAY[selected_language]
    current = today or date.today()
    return prompts[current.toordinal() % len(prompts)]
