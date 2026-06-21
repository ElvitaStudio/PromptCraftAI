from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    code: str
    group: str
    category: str
    target_ai: str
    title_ru: str
    title_en: str
    structure_ru: str
    structure_en: str

    def title(self, language: str) -> str:
        return self.title_en if language == "en" else self.title_ru

    def structure(self, language: str) -> str:
        return self.structure_en if language == "en" else self.structure_ru


TEMPLATE_GROUPS = {
    "business": ("💼 Бизнес", "💼 Business"),
    "code": ("💻 Код", "💻 Code"),
    "images": ("🎨 Изображения", "🎨 Images"),
    "video": ("🎬 Видео", "🎬 Video"),
}


TEMPLATES = {
    "business_offer": PromptTemplate(
        "business_offer", "business", "business", "chatgpt",
        "Коммерческое предложение", "Commercial proposal",
        "Структура: роль, клиент и его проблема, ценностное предложение, "
        "выгоды, доказательства, условия, следующий шаг.",
        "Structure: role, client and problem, value proposition, benefits, "
        "proof, terms and next step.",
    ),
    "business_email": PromptTemplate(
        "business_email", "business", "business", "claude",
        "Email", "Email",
        "Структура: цель письма, получатель, контекст, тон, ключевые пункты, "
        "призыв к действию и формат темы.",
        "Structure: email goal, recipient, context, tone, key points, "
        "call to action and subject format.",
    ),
    "business_marketing": PromptTemplate(
        "business_marketing", "business", "marketing", "chatgpt",
        "Маркетинг", "Marketing",
        "Структура: продукт, аудитория, оффер, канал, этап воронки, "
        "ограничения, метрики и формат результата.",
        "Structure: product, audience, offer, channel, funnel stage, "
        "constraints, metrics and output format.",
    ),
    "code_python": PromptTemplate(
        "code_python", "code", "code", "codex",
        "Python", "Python",
        "Структура: роль Python-разработчика, задача, окружение, входные "
        "данные, ограничения, тесты, формат кода и критерии готовности.",
        "Structure: Python developer role, task, environment, inputs, "
        "constraints, tests, code format and acceptance criteria.",
    ),
    "code_react": PromptTemplate(
        "code_react", "code", "code", "cursor",
        "React", "React",
        "Структура: версия React, UI-задача, компоненты, состояние, API, "
        "адаптивность, доступность, тесты и формат ответа.",
        "Structure: React version, UI task, components, state, API, "
        "responsiveness, accessibility, tests and output format.",
    ),
    "code_sql": PromptTemplate(
        "code_sql", "code", "code", "claude_code",
        "SQL", "SQL",
        "Структура: СУБД, схема, цель запроса, объём данных, индексы, "
        "ограничения производительности и ожидаемый результат.",
        "Structure: database engine, schema, query goal, data volume, "
        "indexes, performance constraints and expected result.",
    ),
    "image_midjourney": PromptTemplate(
        "image_midjourney", "images", "images", "midjourney",
        "Midjourney", "Midjourney",
        "Структура: главный объект, окружение, композиция, стиль, свет, "
        "цвет, камера, настроение, детали и параметры Midjourney.",
        "Structure: subject, environment, composition, style, lighting, "
        "color, camera, mood, details and Midjourney parameters.",
    ),
    "image_flux": PromptTemplate(
        "image_flux", "images", "images", "flux",
        "Flux", "Flux",
        "Структура: сцена, объект, визуальный стиль, материалы, свет, "
        "палитра, перспектива, качество и negative constraints.",
        "Structure: scene, subject, visual style, materials, lighting, "
        "palette, perspective, quality and negative constraints.",
    ),
    "image_gpt": PromptTemplate(
        "image_gpt", "images", "images", "gpt_image",
        "GPT Image", "GPT Image",
        "Структура: цель изображения, содержимое, точный текст в кадре, "
        "композиция, стиль, бренд-ограничения и формат.",
        "Structure: image goal, content, exact in-image text, composition, "
        "style, brand constraints and format.",
    ),
    "video_kling": PromptTemplate(
        "video_kling", "video", "video", "kling",
        "Kling", "Kling",
        "Структура: стартовый кадр, действие, движение камеры, персонажи, "
        "свет, длительность, темп и ограничения артефактов.",
        "Structure: opening frame, action, camera motion, characters, "
        "lighting, duration, pacing and artifact constraints.",
    ),
    "video_veo": PromptTemplate(
        "video_veo", "video", "video", "veo",
        "Veo", "Veo",
        "Структура: сюжет, сцены, кинематография, движение, звук, реплики, "
        "длительность, формат кадра и continuity.",
        "Structure: story, scenes, cinematography, motion, sound, dialogue, "
        "duration, aspect ratio and continuity.",
    ),
    "video_runway": PromptTemplate(
        "video_runway", "video", "video", "runway",
        "Runway", "Runway",
        "Структура: объект, движение, камера, трансформация, стиль, "
        "тайминг, фон, качество и что исключить.",
        "Structure: subject, motion, camera, transformation, style, "
        "timing, background, quality and exclusions.",
    ),
}


def templates_for_group(group: str) -> list[PromptTemplate]:
    return [item for item in TEMPLATES.values() if item.group == group]
