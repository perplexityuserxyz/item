import os
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: Replace with your actual bot token from @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

OWNER_ID = 7924074157
SUDO_USERS = [7924074157, 5294360309, 7905267752]

REQUIRED_CHANNELS = [
    {'id': '@DataTraceUpdates', 'name': 'DataTrace Updates'},
    {'id': '@DataTraceOSINTSupport', 'name': 'DataTrace OSINT Support'}
]

START_LOG_CHANNEL = -1002765060940
SEARCH_LOG_CHANNEL = -1003066524164

ADMIN_CONTACT = '@DataTraceSupport'
CHANNEL_LINK_1 = 'https://t.me/DataTraceUpdates'
CHANNEL_LINK_2 = 'https://t.me/DataTraceOSINTSupport'

FREE_CREDITS_ON_START = 2
FREE_CREDITS_ON_REFERRAL = 1
REFERRAL_COMMISSION_RATE = 0.30

CALL_HISTORY_COST = 600

CREDIT_PRICES = [
    {'credits': 100, 'inr': 30, 'usdt': 0.35},
    {'credits': 200, 'inr': 55, 'usdt': 0.65},
    {'credits': 500, 'inr': 130, 'usdt': 1.55},
    {'credits': 1000, 'inr': 250, 'usdt': 3.0},
    {'credits': 2000, 'inr': 480, 'usdt': 5.7},
    {'credits': 5000, 'inr': 1150, 'usdt': 13.5},
]

API_ENDPOINTS = {
    'upi': 'https://upi-info.vercel.app/api/upi',
    'number': 'http://osintx.info/API/krobetahack.php',
    'telegram': 'https://tg-info-neon.vercel.app/user-details',
    'ip': 'https://karmali.serv00.net/ip_api.php',
    'pakistan': 'https://pak-num-api.vercel.app/search',
    'aadhar_family': 'https://family-members-n5um.vercel.app/fetch',
    'aadhar': 'http://osintx.info/API/krobetahack.php',
    'call_history': 'https://my-vercel-flask-qmfgrzwdl-okvaipro-svgs-projects.vercel.app/api/call_statement'
}

API_KEYS = {
    'number': 'SHAD0WINT3L',
    'aadhar': 'SHAD0WINT3L',
    'aadhar_family': 'paidchx',
    'upi': '456'
}

BRANDING_FOOTER = f"\n\n━━━━━━━━━━━━━━━━━━━\n🔗 Join: {CHANNEL_LINK_1}\n📢 Support: {CHANNEL_LINK_2}\n💬 Contact Admin: {ADMIN_CONTACT}\n━━━━━━━━━━━━━━━━━━━"
