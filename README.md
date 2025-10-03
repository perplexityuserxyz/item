# DataTrace OSINT Bot

Advanced Telegram OSINT Bot with referral system and credit-based lookups.

## Features

- 🔍 **7 OSINT APIs**: UPI, Phone Number, IP, Telegram, Pakistan CNIC, Aadhar, Aadhar Family
- 📞 **Call History**: Premium feature for sudo users
- 🎁 **Referral System**: 1 free credit per referral, 30% commission
- 💳 **Credit System**: Pay-as-you-go with cheap pricing
- 🆓 **Free Usage**: Unlimited in support group @DataTraceOSINTSupport
- ⚙️ **Admin Panel**: User management, broadcasting, statistics
- 🔒 **Protected Numbers**: Owner-only access to sensitive numbers
- 📊 **Logging**: Automatic logging to channels

## Setup Instructions

### 1. Get Bot Token

1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token

### 2. Configure Bot

**Option 1: Using .env file (Recommended)**
```bash
cp .env.example .env
nano .env  # Edit and add your bot token
```

**Option 2: Using environment variable**
```bash
export BOT_TOKEN='YOUR_BOT_TOKEN_HERE'
```

**Option 3: Copy config template**
```bash
cp config.example.py config.py
nano config.py  # Update BOT_TOKEN
```

**⚠️ IMPORTANT:** Never commit `config.py` or `.env` to GitHub! They're already in `.gitignore`.

### 3. Install Dependencies

```bash
pip install python-telegram-bot[all] aiohttp requests python-dotenv
```

Or using uv:
```bash
uv add python-telegram-bot[all] aiohttp requests python-dotenv
```

### 4. Run the Bot

```bash
python bot.py
```

## Configuration

### Admin Settings (config.py)

- `OWNER_ID`: Main owner ID (7924074157)
- `SUDO_USERS`: List of sudo user IDs with full access
- `REQUIRED_CHANNELS`: Channels users must join
- `START_LOG_CHANNEL`: Channel for start events (-1002765060940)
- `SEARCH_LOG_CHANNEL`: Channel for search logs (-1003066524164)

### Credit Pricing

Edit `CREDIT_PRICES` in `config.py`:
```python
CREDIT_PRICES = [
    {'credits': 100, 'inr': 30, 'usdt': 0.35},
    {'credits': 200, 'inr': 55, 'usdt': 0.65},
    ...
]
```

## Commands

### User Commands
- `/start` - Start the bot
- `/help` - Show help message
- `/credits` - Check credits
- `/refer` - Get referral link
- `/buydb` - Buy database
- `/buyapi` - Buy API access

### Lookup Commands
- `/num [number]` - Indian number lookup
- `/upi [upi_id]` - UPI details
- `/ip [ip]` - IP address info
- `/pak [number]` - Pakistan CNIC lookup
- `/aadhar [number]` - Aadhar details
- `/aadhar2fam [number]` - Aadhar family
- `/tg [username]` - Telegram user stats
- `/callhis [number]` - Call history (₹600 for users, FREE for admins)

### Admin Commands (Sudo Only)
- `/addcredits [user_id] [amount]` - Add credits
- `/removecredits [user_id] [amount]` - Remove credits
- `/ban [user_id]` - Ban user
- `/unban [user_id]` - Unban user
- `/stats` - Bot statistics
- `/gcast [message]` - Broadcast message

### Owner Commands
- `/protected` - View protected numbers

## Direct Input

Users can send data directly without commands:
- Phone numbers: `9876543210` or `+919876543210`
- Pakistan numbers: `+923001234567` or `923001234567`
- UPI IDs: `example@upi`
- IP addresses: `8.8.8.8`
- Aadhar numbers: `123456789012`

## Group Mode

In groups, the bot only responds when:
1. Tagged: `@YourBotUsername 9876543210`
2. Command used: `/num 9876543210`
3. Direct number sent in support group

## File Structure

```
.
├── bot.py              # Main bot file
├── database.py         # SQLite database management
├── api_handlers.py     # OSINT API integrations
├── config.example.py   # Configuration template (for GitHub)
├── config.py           # Your actual config (NOT in git)
├── .env.example        # Environment template
├── .env                # Your environment (NOT in git)
├── .gitignore          # Git ignore file
├── README.md           # This file
└── osint_bot.db        # SQLite database (auto-created)
```

**Files to commit to GitHub:**
- ✅ bot.py, database.py, api_handlers.py
- ✅ config.example.py, .env.example
- ✅ .gitignore, README.md

**Files to NEVER commit:**
- ❌ config.py (contains your bot token)
- ❌ .env (contains secrets)
- ❌ osint_bot.db (database with user data)

## Database

SQLite database automatically created on first run with tables:
- `users` - User data, credits, referrals
- `referrals` - Referral tracking
- `protected_numbers` - Protected numbers list
- `blacklist` - Blacklisted identifiers
- `search_logs` - Search history

## Deployment

### VPS Deployment

1. Upload all files to VPS
2. Install Python 3.11+
3. Install dependencies
4. Update bot token in `config.py`
5. Run with screen/tmux:
   ```bash
   screen -S osint_bot
   python bot.py
   ```
   Press `Ctrl+A` then `D` to detach

### Keep Running

Use systemd service or PM2:

**Using systemd:**
```bash
sudo nano /etc/systemd/system/osint_bot.service
```

```ini
[Unit]
Description=DataTrace OSINT Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable osint_bot
sudo systemctl start osint_bot
```

## Support

- Support Group: @DataTraceOSINTSupport
- Updates Channel: @DataTraceUpdates
- Admin Contact: @DataTraceSupport

## License

Private use only. All rights reserved.
