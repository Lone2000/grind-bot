# Grind Bot - Features & Capabilities

A Discord bot for task delegation with Reddit karma verification. Ideal for communities, teams, and servers that need to distribute work fairly with karma-based access control.

---

## 📋 Table of Contents

1. [Core Features](#core-features)
2. [Commands](#commands)
3. [Examples & Scenarios](#examples--scenarios)
4. [Setup & Configuration](#setup--configuration)
5. [Data Storage](#data-storage)
6. [Advanced Features](#advanced-features)

---

## 🎯 Core Features

### 1. **Reddit Karma Verification**
Verifies Discord users against their Reddit account to ensure they meet minimum karma thresholds.

**What it does:**
- Users run `/reddit_verify_yourself` with their Reddit username
- Bot fetches their Reddit karma (post + comment)
- If they meet the thresholds, they get the "Verified" role
- Falls back to HTML parsing if JSON endpoints are blocked

**Thresholds (configurable):**
- Total Karma: > 800 (default)
- Comment Karma: > 500 (default)

**Example:**
```
User: /reddit_verify_yourself username:GrindMaster2000
Bot: ✅ verified role granted.
    → u/GrindMaster2000 has 1200 total (600 post / 600 comment)
    → Role "✅・Verified" added
```

---

### 2. **Task Delegation System**
Automatically assigns tasks from a spreadsheet to Discord users in order.

**What it does:**
- Reads tasks from a Google Sheet or Excel file
- Posts tasks one at a time to an announcement channel
- Users react with ✅ to claim within a time window (default 30s)
- Automatically assigns the task in the spreadsheet
- Enforces cooldown periods between task claims

**Flow:**
1. Admin runs `/create_task number_of_tasks:10`
2. Bot reads first unassigned task from sheet
3. Posts in announcement channel: "task available: **#1234** react ✅ within **30s** to claim"
4. First user to react gets the task
5. Bot writes their Discord username to Column E of the sheet
6. User receives DM with task details
7. Process repeats for next task

---

### 3. **Cooldown Management**
Prevents the same user from claiming tasks too frequently.

**What it does:**
- Applies a cooldown "role/tag" when user claims a task
- User cannot claim another task while the role is active
- Cooldown duration is configurable (e.g., 2 hours)
- Automatically removes the role when cooldown expires
- Runs a background sweeper every 30 seconds

**Example Timeline:**
```
14:00 - User claims Task #1
      → Gets cooldown role (e.g., "🔴・Task Holder")
      → Can't claim another task

16:00 - 2 hours pass
      → Bot auto-removes cooldown role
      → User can claim Task #2 again
```

---

### 4. **Configuration System**
Guild admins can fully customize the bot's behavior per-server.

**Configurable Options:**
- `announce_channel` - Where tasks are posted
- `logs_channel` - Where all bot actions are logged
- `reaction_time_sec` - Time window to claim tasks (5-3600 seconds)
- `ping_role` - Role pinged for each task (optional)
- `cooldown_role` - Role applied when task is claimed
- `cooldown_duration` - Duration of cooldown (e.g., "2h", "120m", "7200s")
- `google_sheet_url` - Google Sheet or local .xlsx path for task list

---

### 5. **Logging System**
All significant events are logged to a designated channel.

**Logged Events:**
- ✅ Task assignments (with Discord ID, Reddit username, karma details)
- ✅ Verification grants (with user, Reddit name, karma breakdown)
- ⚠️ Errors (sheet read/write failures, missing config, etc.)
- 🛑 Task run cancellations/stops
- ⏸️ Task run pauses/resumes

**Example Log Message:**
```
✅ **task assigned**
- task: #4567 (row 12)
- discord: @UserName (`987654321`)
- wrote col E: UserName
- dm: sent
- cooldown role applied: yes
- cooldown: 7200s
```

---

### 6. **Pause/Resume/Cancel Controls**
Manage active task runs without losing progress.

**Capabilities:**
- **Pause** - Stops the timer and task posting (continues when resumed)
- **Resume** - Restarts the paused run
- **Cancel** - Stops the run completely (can start new one)

**Use Cases:**
```
Scenario 1: Staff meeting
  /pause_task_run   → Pauses task delegation
  [Meeting happens]
  /resume_task_run  → Resumes where it left off

Scenario 2: Need to restart
  /cancel_task_run  → Stops current run
  /create_task number_of_tasks:50  → Start fresh
```

---

## 🎮 Commands

### User Commands

#### `/reddit_verify_yourself`
Verify your Reddit account and get the Verified role.

**Parameters:**
- `username` (required) - Your Reddit username (without /u/ prefix)

**Example:**
```
/reddit_verify_yourself username:MyRedditName
```

**Response:**
- ✅ "verified role granted" → You passed the karma check
- ❌ "not eligible" → Your karma doesn't meet minimum thresholds
- ❌ "could not verify" → User not found, suspended, or rate-limited
- ❌ "role not found" → Server admin hasn't set up the Verified role

---

### Admin Commands (require Manage Guild permission)

#### `/config_settings`
Configure the bot for your server.

**Parameters:**
- `announce_channel` (required) - Channel for task posts
- `logs_channel` (required) - Channel for bot logs
- `reaction_time_sec` (required) - Claim window in seconds (5-3600)
- `cooldown_role` (required) - Role to apply during cooldown
- `cooldown_duration` (required) - Duration like "2h", "120m", "7200s"
- `ping_role` (optional) - Role to ping for each task
- `google_sheet_url` (optional) - Google Sheet URL or local .xlsx path

**Example:**
```
/config_settings
  announce_channel: #tasks
  logs_channel: #logs
  reaction_time_sec: 30
  cooldown_role: 🔴・Task Holder
  cooldown_duration: 2h
  ping_role: @Grinders
  google_sheet_url: https://docs.google.com/spreadsheets/d/...
```

---

#### `/create_task`
Start the task delegation process.

**Parameters:**
- `number_of_tasks` (required) - How many tasks to assign (1-500)

**Example:**
```
/create_task number_of_tasks:50
```

**Response:**
```
✅ starting task delegation for 50 tasks.
[Bot begins posting tasks one at a time]
```

---

#### `/pause_task_run`
Pause the active task run.

**Effect:**
- ⏸️ Timer stops (doesn't count down during pause)
- Task posting halts
- Can resume later with exact same state

**Example:**
```
/pause_task_run
→ ⏸️ task run paused.
```

---

#### `/resume_task_run`
Resume a paused task run.

**Effect:**
- ▶️ Timer continues from where it paused
- Task posting resumes

**Example:**
```
/resume_task_run
→ ▶️ task run resumed.
```

---

#### `/cancel_task_run` (or `/stop_create_task`)
Cancel the active task run completely.

**Effect:**
- 🛑 Task run stops
- Progress is lost (must restart)
- Can start a new run afterward

**Example:**
```
/cancel_task_run
→ 🛑 task run cancelled.
```

---

#### `/show_config`
Display the current server configuration.

**Example Output:**
```
current config:
- announce: #tasks
- logs: #logs
- reaction_time_sec: 30
- ping_role: Grinders
- cooldown_role: 🔴・Task Holder
- cooldown_seconds: 7200
- sheet_url: https://docs.google.com/spreadsheets/d/...
```

---

## 📝 Examples & Scenarios

### Scenario 1: Setting Up Task Delegation for a 50-Task Event

**Step 1: Create the Verified role**
```
Server Settings → Roles → Create Role "✅・Verified"
Make sure bot role is ABOVE "✅・Verified"
```

**Step 2: Create a Google Sheet**
```
Column A: Task Numbers (1, 2, 3, 4, ...)
Column B: Task Descriptions
Column E: (leave empty for assignments)
```

**Step 3: Configure the bot**
```
/config_settings
  announce_channel: #tasks
  logs_channel: #logs
  reaction_time_sec: 45
  cooldown_role: 🔴・Task Holder
  cooldown_duration: 3h
  ping_role: @Everyone
  google_sheet_url: https://docs.google.com/spreadsheets/d/ABC123/
```

**Step 4: Start delegating**
```
/create_task number_of_tasks:50
```

**Step 5: Monitor**
```
Watch #logs for assignment confirmations and errors
Use /pause_task_run if you need to stop
Use /resume_task_run to continue later
```

---

### Scenario 2: Handling Verification Failures

**Situation:** User tries to verify but gets rejected.

**Possible Causes & Solutions:**

| Error | Cause | Fix |
|-------|-------|-----|
| "not eligible. needs > 800 total and > 500 comment" | Low karma | User needs to build more Reddit karma |
| "reddit user not found" | Wrong username or banned | Check username spelling, user may be suspended |
| "rate limited by reddit" | Too many bot requests | Wait a few minutes, Reddit blocks requests temporarily |
| "blocked by 403" | Server IP blocked by Reddit | May affect multiple users; contact admins |

**Example:**
```
User: /reddit_verify_yourself username:NewRedditUser
Bot: not eligible. u/NewRedditUser has 300 total (150 post / 150 comment).
     need > 800 total and > 500 comment karma.

→ User knows they need more karma
→ User can try again later
```

---

### Scenario 3: Cooldown Expiry

**Timeline:**
```
14:00 - UserA claims Task #1
        Gets role: 🔴・Task Holder
        Cooldown set to 3 hours

14:05 - UserA tries to claim Task #2
        Reaction removed, task reposted
        Bot logs: "User on cooldown"

17:00 - Cooldown expires (3h passed)
        Bot auto-removes: 🔴・Task Holder
        State cleaned up

17:05 - UserA claims Task #50
        Allowed! Gets new cooldown role
```

---

### Scenario 4: Pause & Resume During Staff Meeting

**Timeline:**
```
13:00 - Event starts, tasks being assigned
        /create_task number_of_tasks:100

14:00 - Important server meeting announced
        /pause_task_run
        ⏸️ Timer paused, task posting stops
        Example: Task #42 was posted at 13:58,
                 user has 2 remaining seconds when paused

14:45 - Meeting ends
        /resume_task_run
        ▶️ Timer resumes
        Task #42's 2-second claim window resumes exactly where it left off
        If someone claimed, moves to Task #43
```

---

### Scenario 5: Excel Fallback (Local Testing)

**For testing without Google Sheets:**

```
1. Create tasks.xlsx with:
   - Column A: Task Numbers (1, 2, 3, ...)
   - Column B: Task Names
   - Column E: (empty for bot to fill)

2. Configure with local path:
   /config_settings
     google_sheet_url: /path/to/tasks.xlsx
     [other settings...]

3. Bot reads from Excel instead of Google Sheets
   (useful if you don't have Google credentials set up)
```

---

## 🔧 Setup & Configuration

### Initial Setup

**1. Prerequisites**
- Python 3.10+
- Discord bot token with permissions: `bot`, `applications.commands`
- `Manage Guild` permission for admins
- Bot role must be ABOVE the "Verified" role

**2. Installation**
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**3. Environment Variables** (`.env` file)
```
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_server_id_here

# Verification settings
VERIFIED_ROLE_NAME=✅・Verified
TOTAL_KARMA_THRESHOLD=800
COMMENT_KARMA_THRESHOLD=500

# Optional: Google Sheets
GOOGLE_CREDS_JSON=service_account.json

# Reddit user agent (identify your bot to Reddit)
REDDIT_USER_AGENT=discord-karma-verifier/1.0 (contact: you@example.com)

# Logging fallback (if logs_channel_id not set)
LOG_CHANNEL_NAME=logs
```

**4. Run the Bot**
```bash
python bot.py
```

---

## 💾 Data Storage

### File Structure

```
data/
├── config_{guild_id}.json     # Guild settings (channels, roles, cooldown)
└── state_{guild_id}.json      # Runtime state (cooldowns, expiry timestamps)
```

### Config File Example

```json
{
  "announce_channel_id": 123456789,
  "logs_channel_id": 987654321,
  "reaction_time_sec": 30,
  "ping_role_id": 456789123,
  "cooldown_role_id": 789123456,
  "cooldown_seconds": 7200,
  "sheet_url": "https://docs.google.com/spreadsheets/d/ABC123/"
}
```

### State File Example

```json
{
  "cooldowns": {
    "987654321": 1704067200,
    "123456789": 1704070800
  }
}
```

---

## 🚀 Advanced Features

### 1. **In-Memory Reddit Cache**
To reduce API hits to Reddit:
- Caches user karma for 5 minutes
- Same user verified multiple times gets cached result
- Cache clears automatically after TTL

**Effect:** Faster verifications, fewer rate limits

---

### 2. **HTML Fallback Parsing**
If Reddit's JSON API is blocked by your server's IP:
- Bot falls back to parsing old.reddit.com HTML
- Extracts karma from page content
- Works when JSON endpoints return 403/401

**Graceful Degradation:** Users can still verify even if one method fails

---

### 3. **Sheet Access Methods**
**Google Sheets:**
- Requires `service_account.json` credentials
- Real-time updates
- Collaborative access

**Local Excel (.xlsx):**
- For testing/development
- No credentials needed
- Useful for small runs

**Auto-detection:** Bot detects if URL is Google Sheets vs local path

---

### 4. **Duration Parsing**
Cooldown duration accepts multiple formats:

```
"2h"       → 2 hours
"2hr"      → 2 hours
"120m"     → 120 minutes
"120min"   → 120 minutes
"7200s"    → 7200 seconds
"7200sec"  → 7200 seconds
"120"      → 120 minutes (plain number)
```

---

### 5. **Background Tasks**
**Cooldown Sweeper** (runs every 30 seconds):
- Checks all expired cooldowns
- Removes cooldown roles automatically
- Cleans up stale state data
- Ensures users aren't stuck with roles

**Benefit:** Reliable, hands-off cooldown management

---

### 6. **Error Handling & Logging**
All errors are logged with context:

```
⚠️ sheet read failed: [connection error]
⚠️ sheet write failed for task #1234 row 5: [permission denied]
⚠️ failed to post task #5: [channel deleted]
⚠️ create_task failed: announce channel not configured.
```

Allows admins to diagnose and fix issues quickly.

---

## 🎓 Use Cases

### 1. **Community Bounty System**
- Verify Discord members via Reddit karma
- Assign bounty tasks from a spreadsheet
- Prevent one person from hogging all bounties (cooldown)

### 2. **Team Task Distribution**
- Fairly assign work to team members
- Ensure reasonable break time between assignments (cooldown)
- Track all assignments in one sheet

### 3. **Event Task Delegation**
- Run 100+ tasks during an event
- Pause for announcements/breaks
- Resume without losing progress
- Full audit trail in logs

### 4. **Role-Based Access Control**
- Require Reddit account age/karma to participate
- Grant roles based on verification
- Restrict channels to verified members only

---

## 📊 Metrics & Monitoring

Check logs channel for:
- Total tasks assigned
- Successful verifications
- Failed attempts (with reasons)
- Cooldown expirations
- Pause/resume events

Example daily summary:
```
Today's Activity:
- 50 tasks assigned ✅
- 12 verifications granted ✅
- 3 verification failures
- 0 sheet errors
- Total cooldowns active: 8
```

---

## ❓ FAQ

**Q: What if a user doesn't get their DM notification?**
A: Bot still assigns the task in the sheet. User should check the announcement channel.

**Q: Can I change thresholds without restarting the bot?**
A: No, thresholds are set in `.env`. Restart after changes.

**Q: What happens if the sheet is deleted?**
A: Bot will error and log failure. Admin can fix the URL with `/config_settings`.

**Q: Can I use multiple sheets?**
A: Not simultaneously. Configure one URL at a time.

**Q: Does the bot work in multiple servers?**
A: Only the server specified by `GUILD_ID`. Use multiple bot instances for other servers.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "role not found" | Create the role specified in `.env` VERIFIED_ROLE_NAME |
| Bot can't assign roles | Move bot role above the target role in Server Settings |
| Tasks not posting | Check announce channel exists and bot has Send Messages permission |
| Logs not showing | Check logs channel exists; fallback is channel named "logs" |
| Sheet not updating | Verify Google credentials JSON is valid; test with Excel first |
| Cooldown not removing | Check bot has Manage Roles permission; restart if stuck |

---

## 📄 License & Credits

Grind Bot - Task delegation + Reddit karma verification for Discord

Built for community-driven task distribution with fairness mechanisms.

