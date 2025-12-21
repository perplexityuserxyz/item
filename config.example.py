import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
VERSION = "v2"

OWNER_ID = 7924074157
SUDO_USERS = [7924074157, 5294360309, 7905267752]

REQUIRED_CHANNELS = [
    {"id": "@DataTraceUpdates", "name": "DataTrace Updates"},
    {"id": -1003498235341, "name": "DataTrace Support"},
]

START_LOG_CHANNEL = -1002765060940
SEARCH_LOG_CHANNEL = -1003066524164

ADMIN_CONTACT = "@DatatraceHelp"
CHANNEL_LINK_1 = "https://t.me/DataTraceUpdates"
CHANNEL_LINK_2 = "https://t.me/+JTDIx-NzrAdmYWFl"

MIN_DIAMOND_PURCHASE = 50
DIAMOND_PRICE_INR = 5
REFERRAL_REWARD_DIAMOND = 1

API_ENDPOINTS = {
    "upi": "https://j4tnx-upi-info-api.onrender.com/upi_id=",
    "verify": "https://chumt-d8kr3hc69-okvaipro-svgs-projects.vercel.app/verify?query={query}",
    "pan": "https://panapi-6g7kjm4ah-okvaipro-svgs-projects.vercel.app/api/pan?pan={pan}",
    "number": "https://no-info-api.onrender.com/num/{number}",
    "vehicle_rc_pdf": "http://3.111.238.230:5004/generate_rc?number={number}",
    "ip": "https://karmali.serv00.net/ip_api.php",
    "pakistan": "https://pak-num-api.vercel.app/search",
    "aadhar_family": "https://aadharapi-5z8qp4sqw-okvaipro-svgs-projects.vercel.app/fetch",
    "aadhar": "https://dt-support.gauravyt566.workers.dev/?aadhaar={aadhar}",
    "numfb": "https://numfb-3m572zbr1-okvaipro-svgs-projects.vercel.app/lookup?number={number}&key={key}",
    "insta_profile": "https://anmolinstainfo.worldgreeker.workers.dev/user?username={username}",
    "insta_posts": "https://anmolinstainfo.worldgreeker.workers.dev/posts?username={username}",
    "bank_ifsc": "https://ifsc.razorpay.com/{ifsc}",
}

API_KEYS = {
    "number": "",
    "aadhar_family": "datatrace",
    "upi": "",
    "numfb": "chxprm456",
}

BRANDING_FOOTER = (
    "\n\n----------------------\n"
    f"Updates: {CHANNEL_LINK_1}\n"
    f"Support: {CHANNEL_LINK_2}\n"
    f"Contact: {ADMIN_CONTACT}"
)
