# Discord Reddit Karma Verifier

Slash command:
- /reddit_verify_yourself username:<reddit_username>

Rule:
- total_karma must be > 800
- comment_karma must be > 500

## Setup

1) Create a Discord role named `verified`
2) Put the bot's role ABOVE `verified` in Server Settings → Roles
3) Invite the bot with:
   - scopes: bot, applications.commands
   - permission: Manage Roles

## Install

python -m venv .venv

Windows:
.venv\Scripts\activate

Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt

## Config

Copy `.env.example` to `.env` and fill values:
- DISCORD_TOKEN
- GUILD_ID
- VERIFIED_ROLE_NAME
- TOTAL_KARMA_THRESHOLD
- COMMENT_KARMA_THRESHOLD

## Run

python bot.py
