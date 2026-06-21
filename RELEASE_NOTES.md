# Release Notes

## PromptCraft AI v1.0

The first public release of PromptCraft AI.

### Prompt creation

- Prompt generation for seven task categories
- Support for ChatGPT, Claude, Gemini, Grok, Midjourney, GPT Image, Flux,
  Kling, Veo, Runway, Cursor, Claude Code and Codex
- Russian and English onboarding and interface
- Standard and Premium Expert generation modes
- Multiple prompt variants for Premium users
- Improve, shorten, expand, translate and regenerate actions
- Simple, Advanced and Premium-only Expert difficulty levels
- Short, Detailed, Professional and Expert response styles
- Create and Optimize workflows
- Professional software-engineering prompt structures for Claude Code, Codex
  and Cursor
- Thirteen developer templates, including refactoring, debugging, FastAPI,
  Next.js, React, SQL and Telegram applications
- Saved generation preferences and bilingual Prompt of the Day

### Library and productivity

- Ready-made Business, Code, Images and Video templates
- Favorite prompts with quick reopening
- Prompt history with source request, result, category, target AI, language
  and creation date
- TXT and Markdown exports
- Paginated history with prompt cards, reuse, favorites and export
- Saved default AI and TXT/Markdown export preference

### Prompt Chat

- Guided Russian and English requirements interview
- Audience, features, design, monetization and technology questions
- Claude Code, Codex, Cursor, ChatGPT, Gemini and DeepSeek targets
- Professional output with architecture, testing, error handling, security,
  documentation and acceptance criteria

### Interface and settings

- New bilingual inline main menu
- Dedicated Settings section
- Professional, Detailed, Concise and Creative saved styles
- Simple, Advanced and Premium-only Expert saved levels
- Default AI selection across all 13 core AI tools
- Redesigned bilingual Free, Pro and Premium presentation
- Free, Pro and Premium variants set to 1, 2 and 3 respectively

### Plans and payments

- Free, Pro and Premium usage limits
- Telegram Stars invoices in `XTR`
- Idempotent payment processing
- Personal referral links
- Three-day Premium referral rewards

### Administration

- User, plan, growth and revenue statistics
- Paginated user list
- Search by Telegram ID and username
- Plan assignment and temporary Premium rewards
- User blocking and unblocking
- Referral reports
- Broadcast wizard with audience targeting
- Text, photo, document and video broadcasts
- Preview and confirmation before delivery
- Delivery, error and blocked-user statistics
- Automatic blocked-user marking
- Localized news archive and `/news`

### Engineering

- Async architecture based on aiogram 3
- SQLite storage with automatic migrations
- OpenAI API integration
- Python 3.10+ compatibility
- Unit test coverage for core user, payment, referral and admin flows

## Upgrade notes

- Copy new variables from `.env.example` into your deployment environment
  when required.
- Do not replace an existing `.env` file during deployment.
- Database schema updates are applied automatically during startup.
