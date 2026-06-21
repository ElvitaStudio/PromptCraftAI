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
- Admin panel with analytics, user search, subscriptions and blocking
- Premium Expert mode with multiple prompt variants

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
| Free | 5/day | 5 | 1 prompt improvement/day |
| Pro — 199 Stars | 100/day | 30 | All standard prompt tools |
| Premium — 399 Stars | Unlimited | 100 | Expert mode and multiple variants |

Pro and Premium subscriptions are issued for 30 days.

## Referral system

The `/invite` command creates a personal Telegram deep link. When a new user
starts the bot through that link for the first time, the inviter receives
Premium for three days.

Self-referrals, repeated rewards and rewards for existing users are rejected.

## Telegram Stars payments

Digital subscriptions are sold through Telegram Stars:

- Pro: `199 XTR`
- Premium: `399 XTR`
- Currency: `XTR`
- Provider token: empty, as required for Telegram digital goods

The bot validates pre-checkout payloads, stores successful payments and
prevents repeated subscription activation for the same Telegram charge.
Payment support is available through `/paysupport`.

## Admin panel

The `/admin` command is available only to Telegram IDs configured in
`ADMIN_IDS`.

Administrators can:

- view total users, 24-hour growth and Stars revenue;
- view Free, Pro and Premium totals;
- browse users with pagination;
- search by Telegram ID or username;
- grant Free, Pro or Premium;
- add three days of Premium;
- block and unblock users;
- inspect referral statistics and relationships.

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
ADMIN_IDS=123456789,987654321
SUPPORT_USERNAME=PromptCraftSupport
```

| Variable | Description |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token received from BotFather |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_GENERATION_MODEL` | Model used for prompt generation |
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
| `/limits` | View current plan limits |
| `/premium` | View plans and purchase a subscription |
| `/invite` | Open the referral program |
| `/language` | Change interface language |
| `/paysupport` | Get payment support details |
| `/help` | View help |
| `/admin` | Open the admin panel |

## Project structure

```text
PromptCraftAI/
├── app/
│   ├── handlers/       # Telegram command and callback handlers
│   ├── services/       # OpenAI integration
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
