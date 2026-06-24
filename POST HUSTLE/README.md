# Post Hustle Bot

Verification-only Discord bot for the Post Hustle server. Currently exposes a single slash command:

- `/reddit_verify_yourself <username>` — fetches the user's Reddit karma and grants the Verified role if they pass the thresholds.

## Setup

1. Create venv and install deps:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Fill in `.env` (token + guild ID are already set).

3. Make sure the Discord server has:
   - A role named `✅・Verified` (or update `VERIFIED_ROLE_NAME` in `.env`)
   - A channel named `📄︱logs` (or update `LOG_CHANNEL_NAME` in `.env`)
   - The bot role placed **above** the Verified role in the role list (or it can't grant it)

4. Run:
   ```
   python bot.py
   ```

## Thresholds

Pass requires **both**:
- total karma > 800
- comment karma > 200

Edit `TOTAL_KARMA_THRESHOLD` / `COMMENT_KARMA_THRESHOLD` in `.env` to change.
