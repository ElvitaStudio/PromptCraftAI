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

### Library and productivity

- Ready-made Business, Code, Images and Video templates
- Favorite prompts with quick reopening
- Prompt history with source request, result, category, target AI, language
  and creation date
- TXT and Markdown exports

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
