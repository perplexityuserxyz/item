# GitHub Setup Guide

How to safely push this bot to GitHub and deploy to VPS.

## Before Pushing to GitHub

### 1. Verify .gitignore

Ensure these files are in `.gitignore`:
```
config.py
.env
*.db
```

Check:
```bash
cat .gitignore
```

### 2. Remove sensitive data

```bash
# Check what will be committed
git status

# Make sure config.py and .env are NOT in the list
```

### 3. Verify files to commit

**Should be committed:**
- ✅ bot.py
- ✅ database.py
- ✅ api_handlers.py
- ✅ config.example.py (template with placeholders)
- ✅ .env.example (template)
- ✅ .gitignore
- ✅ README.md
- ✅ DEPLOYMENT.md

**Should NOT be committed:**
- ❌ config.py (your actual config)
- ❌ .env (contains bot token)
- ❌ osint_bot.db (database)
- ❌ __pycache__/ (Python cache)

## Pushing to GitHub

### Create new repository

1. Go to GitHub.com
2. Click "New Repository"
3. Name: `osint-bot` (or your choice)
4. Make it **Private** (recommended for bots)
5. Don't initialize with README (we have one)
6. Create repository

### Push code

```bash
cd /path/to/your/bot

# Initialize git (if not already)
git init

# Add all files
git add .

# Check what's staged (verify config.py is NOT there)
git status

# First commit
git commit -m "Initial commit: DataTrace OSINT Bot"

# Add remote
git remote add origin https://github.com/yourusername/osint-bot.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Deploy to VPS

### 1. SSH into VPS
```bash
ssh user@your-vps-ip
```

### 2. Clone repository
```bash
cd /home/youruser
git clone https://github.com/yourusername/osint-bot.git
cd osint-bot
```

### 3. Setup environment
```bash
# Copy example files
cp .env.example .env
cp config.example.py config.py

# Edit .env with your bot token
nano .env
```

Add:
```
BOT_TOKEN=your_actual_bot_token_here
```

### 4. Install & Run

Follow steps in [DEPLOYMENT.md](DEPLOYMENT.md)

## Updating Bot

### On local machine:
```bash
# Make changes
git add .
git commit -m "Update: description of changes"
git push
```

### On VPS:
```bash
cd /home/youruser/osint-bot

# Stop bot
sudo systemctl stop osint-bot

# Pull updates
git pull

# Restart bot
sudo systemctl start osint-bot
```

## Security Checklist

Before pushing to GitHub, verify:

- [ ] `.gitignore` includes `config.py` and `.env`
- [ ] No bot token in any committed file
- [ ] `config.example.py` has placeholder tokens only
- [ ] Database file not committed
- [ ] Repository is set to Private (if sensitive)
- [ ] All API keys in config.example.py are placeholders

## Common Mistakes to Avoid

❌ **DON'T:**
- Push config.py with real tokens
- Commit .env file
- Make repo public with real credentials
- Hardcode tokens in code

✅ **DO:**
- Use .env for secrets
- Keep .gitignore updated
- Use config.example.py for templates
- Document setup in README

## Token Leaked?

If you accidentally pushed your bot token:

1. **Immediately revoke it:**
   - Message @BotFather
   - Use `/mybots` → Select bot → Revoke token

2. **Remove from git history:**
   ```bash
   # WARNING: This rewrites history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch config.py" \
     --prune-empty --tag-name-filter cat -- --all
   
   git push --force
   ```

3. **Get new token:**
   - Get new token from @BotFather
   - Update .env locally and on VPS

## Backup Strategy

### Backup database before updates:
```bash
# On VPS
cd /home/youruser/osint-bot
cp osint_bot.db backups/osint_bot_$(date +%Y%m%d_%H%M%S).db
```

### Automated backup:
```bash
# Add to crontab
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * cd /home/youruser/osint-bot && cp osint_bot.db backups/osint_bot_$(date +\%Y\%m\%d).db
```

## Questions?

- Read: [README.md](README.md)
- Deploy: [DEPLOYMENT.md](DEPLOYMENT.md)
- Support: @DataTraceSupport
