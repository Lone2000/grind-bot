import os
import re
import time
import html as html_lib
from typing import Optional, Dict, Tuple

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# =========================
# ENV
# =========================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

VERIFIED_ROLE_NAME = os.getenv("VERIFIED_ROLE_NAME", "✅・Verified").strip()
TOTAL_KARMA_THRESHOLD = int(os.getenv("TOTAL_KARMA_THRESHOLD", "800"))
COMMENT_KARMA_THRESHOLD = int(os.getenv("COMMENT_KARMA_THRESHOLD", "200"))

LOG_CHANNEL_NAME = os.getenv("LOG_CHANNEL_NAME", "logs").strip()

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")
if not GUILD_ID:
    raise RuntimeError("Missing GUILD_ID in .env")

# =========================
# DISCORD
# =========================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")


async def send_logs(guild: discord.Guild, message: str) -> None:
    if not LOG_CHANNEL_NAME:
        return
    ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if ch is None:
        return
    try:
        await ch.send(message, allowed_mentions=discord.AllowedMentions.none())
    except Exception:
        pass


# =========================
# REDDIT KARMA (JSON first, HTML fallback)
# =========================
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    "discord-karma-verifier/1.0 (contact: admin@example.com)"
).strip()

REDDIT_PROXY_URL = os.getenv("REDDIT_PROXY_URL", "").strip()
REDDIT_PROXY_USERNAME = os.getenv("REDDIT_PROXY_USERNAME", "").strip()
REDDIT_PROXY_PASSWORD = os.getenv("REDDIT_PROXY_PASSWORD", "").strip()

_REDDIT_PROXY = None
if REDDIT_PROXY_URL and REDDIT_PROXY_USERNAME and REDDIT_PROXY_PASSWORD:
    from urllib.parse import quote
    encoded_user = quote(REDDIT_PROXY_USERNAME, safe="")
    encoded_pass = quote(REDDIT_PROXY_PASSWORD, safe="")
    _REDDIT_PROXY = REDDIT_PROXY_URL.replace("http://", f"http://{encoded_user}:{encoded_pass}@")

_REDDIT_CACHE: Dict[str, Tuple[int, int, int, int]] = {}
_REDDIT_CACHE_TTL = 300


async def fetch_reddit_karma(username: str) -> tuple[int, int, int]:
    """returns (link_karma, comment_karma, total)"""
    u = username.strip()

    now = int(time.time())
    cached = _REDDIT_CACHE.get(u.lower())
    if cached and now < cached[3]:
        return cached[0], cached[1], cached[2]

    headers = {
        "User-Agent": REDDIT_USER_AGENT,
        "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
    }

    async def _try_about_json(url: str) -> Optional[tuple[int, int, int]]:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, proxy=_REDDIT_PROXY) as resp:
                if resp.status == 404:
                    raise ValueError("reddit user not found")
                if resp.status == 429:
                    raise ValueError("rate limited by reddit, try again soon")

                if resp.status == 200:
                    data = await resp.json()
                    payload = data.get("data", {}) if isinstance(data, dict) else {}
                    if payload.get("is_suspended") is True:
                        raise ValueError("reddit account is suspended")
                    link_karma = int(payload.get("link_karma", 0))
                    comment_karma = int(payload.get("comment_karma", 0))
                    return link_karma, comment_karma, link_karma + comment_karma

                if resp.status in (401, 403):
                    return None

                txt = await resp.text()
                raise ValueError(f"reddit error http {resp.status}: {txt[:120]}")

    for url in (
        f"https://www.reddit.com/user/{u}/about.json",
        f"https://old.reddit.com/user/{u}/about.json",
    ):
        got = await _try_about_json(url)
        if got:
            link_karma, comment_karma, total = got
            _REDDIT_CACHE[u.lower()] = (link_karma, comment_karma, total, now + _REDDIT_CACHE_TTL)
            return got

    html_url = f"https://old.reddit.com/user/{u}/"
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(html_url, headers=headers, proxy=_REDDIT_PROXY) as resp:
            if resp.status == 404:
                raise ValueError("reddit user not found")
            if resp.status == 429:
                raise ValueError("rate limited by reddit, try again soon")
            if resp.status in (401, 403):
                raise ValueError("reddit blocked this server ip (403). html fallback also blocked.")
            if resp.status != 200:
                txt = await resp.text()
                raise ValueError(f"reddit error http {resp.status}: {txt[:120]}")
            html = await resp.text()

    if "account has been suspended" in html.lower():
        raise ValueError("reddit account is suspended")

    link_m = re.search(r'class="karma"[^>]*>\s*([\d,]+)\s*<', html)
    com_m = re.search(r'class="karma comment-karma"[^>]*>\s*([\d,]+)\s*<', html)

    if not link_m or not com_m:
        clean = html_lib.unescape(re.sub(r"<[^>]+>", " ", html))
        link_m = re.search(r"(\d[\d,]*)\s+(?:link|post)\s+karma", clean, flags=re.IGNORECASE)
        com_m = re.search(r"(\d[\d,]*)\s+comment\s+karma", clean, flags=re.IGNORECASE)

    if not link_m or not com_m:
        snippet = html[:500].replace("\n", " ")
        print(f"[reddit_verify] parse failed for {u!r} — first 500 chars: {snippet}")
        raise ValueError("could not parse karma from profile page (layout changed or blocked).")

    link_karma = int(link_m.group(1).replace(",", ""))
    comment_karma = int(com_m.group(1).replace(",", ""))
    total = link_karma + comment_karma

    _REDDIT_CACHE[u.lower()] = (link_karma, comment_karma, total, now + _REDDIT_CACHE_TTL)
    return link_karma, comment_karma, total


# =========================
# EVENTS
# =========================
@bot.event
async def on_ready() -> None:
    guild_obj = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild_obj)
    await bot.tree.sync(guild=guild_obj)
    print(f"Logged in as {bot.user} | commands synced to guild {GUILD_ID}")


# =========================
# COMMAND: reddit verify
# =========================
@bot.tree.command(
    name="reddit_verify_yourself",
    description="Check Reddit karma and grant the verified role when eligible.",
)
@app_commands.describe(username="Reddit username (without /u/)")
async def reddit_verify_yourself(interaction: discord.Interaction, username: str) -> None:
    await interaction.response.defer(ephemeral=True)

    username = username.strip()
    if not USERNAME_RE.match(username):
        await interaction.followup.send("invalid reddit username format.", ephemeral=True)
        return

    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.followup.send("run this inside the server (not dms).", ephemeral=True)
        return

    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
    if role is None:
        await interaction.followup.send(
            f"role '{VERIFIED_ROLE_NAME}' not found. create it or update VERIFIED_ROLE_NAME in .env.",
            ephemeral=True,
        )
        return

    try:
        link_karma, comment_karma, total = await fetch_reddit_karma(username)
    except ValueError as e:
        await interaction.followup.send(f"could not verify: {e}", ephemeral=True)
        return
    except Exception:
        await interaction.followup.send("unexpected error while contacting reddit.", ephemeral=True)
        return

    if not (total > TOTAL_KARMA_THRESHOLD and comment_karma > COMMENT_KARMA_THRESHOLD):
        await interaction.followup.send(
            f"not eligible. u/{username} has {total} total ({link_karma} post / {comment_karma} comment). "
            f"need > {TOTAL_KARMA_THRESHOLD} total and > {COMMENT_KARMA_THRESHOLD} comment karma.",
            ephemeral=True,
        )
        return

    member: discord.Member = interaction.user
    if role in member.roles:
        await interaction.followup.send("already verified.", ephemeral=True)
        return

    try:
        await member.add_roles(role, reason=f"reddit karma gate: u/{username} total={total}, comment={comment_karma}")
    except discord.Forbidden:
        await interaction.followup.send(
            "missing permission to add that role. move the bot role above verified + grant manage roles.",
            ephemeral=True,
        )
        return

    try:
        await send_logs(
            interaction.guild,
            "✅ **verified granted**\n"
            f"- discord: {member.mention} (`{member.id}`)\n"
            f"- reddit: u/{username}\n"
            f"- karma: total={total}, comment={comment_karma}, post={link_karma}\n"
            f"- rule: total > {TOTAL_KARMA_THRESHOLD} and comment > {COMMENT_KARMA_THRESHOLD}",
        )
    except Exception:
        pass

    await interaction.followup.send("✅ verified role granted.", ephemeral=True)


# =========================
# RUN
# =========================
bot.run(DISCORD_TOKEN)
