# PromptCraft AI

AI-powered Telegram bot for creating and improving prompts for leading
generative AI tools.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3-2CA5E0?logo=telegram&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

PromptCraft AI turns a short description of a task into a structured,
ready-to-use prompt. Choose a category, select the target AI, describe the
result you need, and receive a polished prompt in Russian or English.

## Supported AI tools

- ChatGPT
- Claude
- Gemini
- Grok
- Midjourney
- GPT Image
- Flux
- Kling
- Veo
- Runway
- Cursor
- Claude Code
- Codex

## Features

- Prompt generation for text, images, video, code, marketing, business and
  study tasks
- Prompt improvement, shortening, expansion, translation and alternative
  variants
- Simple, Advanced and Premium-only Expert difficulty levels
- Short, Detailed, Professional and Expert response styles
- Create Prompt and Optimize My Prompt workflows
- Professional coding prompts for Claude Code, Codex and Cursor
- Dedicated developer modes for refactoring, debugging, architecture, review,
  tests, documentation and popular stacks
- Saved AI, category, difficulty and response-style preferences
- Bilingual Prompt of the Day
- Ready-made prompt templates
- Favorite prompts
- Plan-based prompt history
- TXT export
- Markdown export
- Personal referral links and rewards
- Telegram Stars payments
- Russian and English interface
- Inline main menu for generation, history, plans and settings
- Admin panel with analytics, user search, subscriptions and blocking
- Premium Expert mode with multiple prompt variants
- Prompt Chat requirements wizard for complex project ideas
- Admin broadcasts with audience targeting, previews and delivery statistics
- Localized news feed generated from confirmed broadcasts
- Premium Plus AI Workspace with isolated GPT and Claude assistants
- One-time 24-hour Premium Plus Trial with 15 shared AI requests

## Prompt templates

The bilingual template library includes:

| Category | Templates |
| --- | --- |
| Business | Commercial proposal, Email, Marketing |
| Code | Python, React, SQL |
| Images | Midjourney, Flux, GPT Image |
| Video | Kling, Veo, Runway |

Open the library with `/templates`. After selecting a template, the bot asks
for the task and applies the appropriate prompt structure automatically.

## Plans

| Plan | Requests | History | Features |
| --- | ---: | ---: | --- |
| Free | 5/day | 5 | 1 variant, Simple and Advanced |
| Pro — 199 Stars | 100/day | 30 | 2 variants, all categories, templates |
| Premium — 399 Stars | Unlimited | 100 | Expert mode, 3 variants, all tools |
| Premium Plus — 2499 Stars | Unlimited | 100 | Premium features plus GPT and Claude assistants |

Pro, Premium and Premium Plus subscriptions are issued for 30 days.

## Main menu

The bilingual inline menu provides direct access to:

- Create Prompt
- Optimize Prompt
- Prompt history
- Favorites
- Templates
- Prompt of the Day
- Premium plans
- Settings
- Prompt Chat

## Prompt history

History is paginated according to the active plan. Every entry stores the
original request, final prompt, category, target AI, language and creation
date. Users can reopen prompts, reuse clean prompt text, add prompts to
favorites and export them.

## Settings

Settings are saved in SQLite and reused during future generations:

- Russian or English interface;
- Professional, Detailed, Concise or Creative response style;
- Simple, Advanced or Premium-only Expert generation level;
- default AI from all 13 core AI tools;
- TXT or Markdown default export format.

Existing specialized generation flows retain their Short and Expert styles.

## Prompt Chat

Prompt Chat is a bilingual requirements wizard. It starts with a rough idea
and asks focused questions about the project language, audience, features,
design, monetization, technologies and constraints.

The completed interview becomes a structured professional prompt with
architecture, testing, error handling, security, documentation and acceptance
criteria.

Prompt Chat supports Claude Code, Codex, Cursor, ChatGPT, Gemini and DeepSeek.

## Premium Plus AI Workspace

Premium Plus is the first step toward turning PromptCraft AI into an AI
Workspace. It costs `2499 Stars` and is activated for 30 days. A new payment
extends an active Premium Plus subscription by another 30 days.

The main menu includes **AI Assistants**:

- GPT Assistant
- Claude Assistant

Each assistant has an isolated workspace with:

- multiple saved chats;
- new and continued conversations;
- persistent message history and context;
- search by chat title or message content;
- chat deletion.

Users listed in `ADMIN_IDS` can access GPT and Claude assistants without an
active Premium Plus subscription for testing and administration.

## Premium Plus Trial

Every account receives Premium Plus Trial once:

- duration: 24 hours;
- shared allowance: 15 model calls;
- full Premium and Premium Plus feature access;
- GPT Assistant, Claude Assistant, Prompt Chat, Create Prompt and Optimize
  Prompt consume the shared allowance;
- history, search, exports, templates, favorites, settings, news and
  navigation do not consume it.

New users receive Trial during their first `/start`. Existing accounts receive
it on their next bot interaction. Trial activation and notification are
persisted so the offer can never be granted automatically a second time.

GPT uses the existing OpenAI API configuration. Claude uses the Anthropic
Messages API. Assistant history is stored separately from regular PromptCraft
prompt history. A missing Anthropic key produces a localized configuration
message without losing the user's saved message.

## Referral system

The `/invite` command creates a personal Telegram deep link. When a new user
starts the bot through that link for the first time, the inviter receives
Premium for three days.

Self-referrals, repeated rewards and rewards for existing users are rejected.

## Telegram Stars payments

Digital subscriptions are sold through Telegram Stars:

- Pro: `199 XTR`
- Premium: `399 XTR`
- Premium Plus: `2499 XTR`
- Currency: `XTR`
- Provider token: empty, as required for Telegram digital goods

The bot validates pre-checkout payloads, stores successful payments and
prevents repeated subscription activation for the same Telegram charge.
Premium Plus payments activate the AI Workspace for 30 days or extend an
existing Premium Plus subscription by 30 days.
Payment support is available through `/paysupport`.

## Admin panel

The `/admin` command is available only to Telegram IDs configured in
`ADMIN_IDS`.

Administrators can:

- view total users, 24-hour growth and Stars revenue;
- view Free, Pro, Premium and Premium Plus totals and sales;
- browse users with pagination;
- search by Telegram ID or username;
- grant Free, Pro, Premium or Premium Plus;
- add three days of Premium;
- block and unblock users;
- inspect referral statistics and relationships.
- create broadcasts for all, Free, paid or Premium users;
- review the latest published news.

## Broadcasts and news

Administrators listed in `ADMIN_IDS` can start `/broadcast`, select an
audience and send text, a photo, document or video with an optional caption.
The bot shows a preview before sending.

Broadcast delivery:

- excludes users marked as blocked;
- catches Telegram delivery errors without stopping the campaign;
- marks users blocked when Telegram reports that the bot was blocked;
- reports sent, failed, blocked and total recipient counts.

Every confirmed broadcast is saved as a localized news item. Users can open
the latest 20 items with `/news` and use the Try, Premium and Feedback inline
buttons.

## Tech stack

- Python 3.10+
- aiogram 3
- SQLite with aiosqlite
- OpenAI API
- python-dotenv

## Installation

```bash
git clone <your-repository-url>
cd PromptCraftAI

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

## Environment variables

Create `.env` from `.env.example` and provide your own credentials:

```dotenv
TELEGRAM_BOT_TOKEN=
OPENAI_API_KEY=
OPENAI_GENERATION_MODEL=gpt-4.1-mini
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
ADMIN_IDS=123456789,987654321
SUPPORT_USERNAME=PromptCraftSupport
```

| Variable | Description |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token received from BotFather |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_GENERATION_MODEL` | Model used for prompt generation |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude Assistant |
| `ANTHROPIC_MODEL` | Claude model used by Claude Assistant |
| `ADMIN_IDS` | Comma-separated Telegram IDs with admin access |
| `SUPPORT_USERNAME` | Telegram username for payment support |

Never commit `.env`. It is excluded by `.gitignore`.

## Run locally

```bash
python3 main.py
```

## Tests

Run the complete unit test suite:

```bash
python3 -m unittest discover -s tests -v
```

## Bot commands

| Command | Description |
| --- | --- |
| `/start` | Start the bot and select a language |
| `/new` | Create a new prompt |
| `/templates` | Open the prompt template library |
| `/favorites` | View saved prompts |
| `/history` | View prompt history |
| `/chat` | Start the Prompt Chat wizard |
| `/settings` | Open generation and export settings |
| `/news` | View the latest 20 localized updates |
| `/limits` | View current plan limits |
| `/premium` | View plans and purchase a subscription |
| `/invite` | Open the referral program |
| `/language` | Change interface language |
| `/paysupport` | Get payment support details |
| `/help` | View help |
| `/admin` | Open the admin panel |
| `/broadcast` | Create an admin broadcast |

## Project structure

```text
PromptCraftAI/
├── app/
│   ├── handlers/       # Telegram command and callback handlers
│   ├── services/       # OpenAI integration
│   ├── assistant_workspace.py
│   ├── assistant_keyboards.py
│   ├── database.py     # SQLite storage and migrations
│   ├── keyboards.py    # User inline keyboards
│   ├── templates.py    # Prompt template library
│   └── ...
├── docs/screenshots/   # Public screenshot placeholders
├── tests/              # Unit tests
├── main.py             # Application entry point
└── requirements.txt
```

## Screenshots

Screenshots will be added in a future release. See
[docs/screenshots/README.md](docs/screenshots/README.md) for the planned
gallery.

## Roadmap

- Prompt template marketplace
- Favorite folders and tags
- Category and AI analytics
- Team workspaces
- Additional interface languages

## Security

Secrets, local databases, virtual environments, logs, caches and SQLite
WAL/SHM files are excluded from version control. Review `.env.example` when
deploying and keep real credentials only in `.env` or your hosting platform's
secret manager.

## License

PromptCraft AI is available under the [MIT License](LICENSE).
