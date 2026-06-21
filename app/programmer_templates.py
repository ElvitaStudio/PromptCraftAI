from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProgrammerTemplate:
    code: str
    title_ru: str
    title_en: str
    structure_ru: str
    structure_en: str

    def title(self, language: str) -> str:
        return self.title_en if language == "en" else self.title_ru

    def structure(self, language: str) -> str:
        return self.structure_en if language == "en" else self.structure_ru


def _template(
    code: str,
    title: str,
    focus_ru: str,
    focus_en: str,
) -> ProgrammerTemplate:
    return ProgrammerTemplate(
        code=code,
        title_ru=title,
        title_en=title,
        structure_ru=(
            f"Режим разработчика: {focus_ru}. Обязательно уточни роль, цель, "
            "стек и версии, требования, структуру проекта, ограничения, "
            "формат ответа, тесты, обработку ошибок и документацию."
        ),
        structure_en=(
            f"Developer mode: {focus_en}. Explicitly define the role, goal, "
            "stack and versions, requirements, project structure, constraints, "
            "response format, tests, error handling and documentation."
        ),
    )


PROGRAMMER_TEMPLATES = {
    item.code: item
    for item in (
        _template(
            "refactor",
            "Refactor code",
            "безопасный рефакторинг с сохранением поведения",
            "safe refactoring with behavior preservation",
        ),
        _template(
            "debug",
            "Debug",
            "поиск первопричины, воспроизведение и проверка исправления",
            "root-cause analysis, reproduction and fix verification",
        ),
        _template(
            "architecture",
            "Architecture",
            "проектирование компонентов, границ и потоков данных",
            "component, boundary and data-flow design",
        ),
        _template(
            "review",
            "Review",
            "ревью корректности, безопасности, качества и производительности",
            "correctness, security, quality and performance review",
        ),
        _template(
            "tests",
            "Tests",
            "стратегия unit, integration и edge-case тестирования",
            "unit, integration and edge-case testing strategy",
        ),
        _template(
            "documentation",
            "Documentation",
            "README, API-документация, примеры и инструкции запуска",
            "README, API documentation, examples and run instructions",
        ),
        _template(
            "fastapi",
            "FastAPI",
            "production-ready FastAPI, Pydantic, async I/O и OpenAPI",
            "production-ready FastAPI, Pydantic, async I/O and OpenAPI",
        ),
        _template(
            "nextjs",
            "Next.js",
            "Next.js App Router, Server Components, данные и deployment",
            "Next.js App Router, Server Components, data and deployment",
        ),
        _template(
            "react",
            "React",
            "компоненты, состояние, доступность и производительность React",
            "React components, state, accessibility and performance",
        ),
        _template(
            "python",
            "Python",
            "типизированный Python, архитектура, зависимости и pytest",
            "typed Python, architecture, dependencies and pytest",
        ),
        _template(
            "sql",
            "SQL",
            "схема, запросы, индексы, транзакции и план выполнения",
            "schema, queries, indexes, transactions and execution plans",
        ),
        _template(
            "telegram_bot",
            "Telegram Bot",
            "aiogram 3, FSM, middleware, callbacks, платежи и deployment",
            "aiogram 3, FSM, middleware, callbacks, payments and deployment",
        ),
        _template(
            "telegram_mini_app",
            "Telegram Mini App",
            "Telegram WebApp API, init data, backend и безопасная авторизация",
            "Telegram WebApp API, init data, backend and secure authentication",
        ),
    )
}
