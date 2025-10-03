#!/usr/bin/env python3
import os
import asyncio
import re
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.error import Forbidden, BadRequest

from database import Database
from api_handlers import APIHandler
from config import *  # BOT_TOKEN, OWNER_ID, SUDO_USERS, REQUIRED_CHANNELS, CHANNEL_LINK_1, CHANNEL_LINK_2, BRANDING_FOOTER, ADMIN_CONTACT, START_LOG_CHANNEL, SEARCH_LOG_CHANNEL, CREDIT_PRICES, CALL_HISTORY_COST

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# Instances
db = Database()
api_handler = APIHandler()

# --------- Helpers ----------
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def is_sudo(user_id: int) -> bool:
    return user_id in SUDO_USERS

def is_admin(user_id: int) -> bool:
    return is_sudo(user_id) or is_owner(user_id)

async def safe_send(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str,
                    parse_mode=ParseMode.HTML, reply_markup: Optional[InlineKeyboardMarkup] = None):
    """Send a message safely (works if update.message is None)."""
    try:
        if update and getattr(update, "message", None):
            return await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        # fallback to effective_chat
        chat_id = update.effective_chat.id if update and update.effective_chat else None
        if chat_id:
            return await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Forbidden:
        logger.warning("Bot was blocked by the user or can't send message to this chat.")
    except BadRequest as e:
        logger.warning(f"BadRequest while sending message: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in safe_send: {e}")
    return None

async def safe_send_document(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str, caption: str = None):
    try:
        chat_id = update.effective_chat.id if update and update.effective_chat else None
        if getattr(update, "message", None):
            return await update.message.reply_document(document=open(file_path, "rb"), filename=os.path.basename(file_path), caption=caption)
        elif chat_id:
            return await context.bot.send_document(chat_id=chat_id, document=open(file_path, "rb"), filename=os.path.basename(file_path), caption=caption)
    except Forbidden:
        logger.warning("Bot was blocked by the user (document).")
    except Exception as e:
        logger.exception(f"Failed to send document: {e}")
    return None

async def log_to_channel(context: ContextTypes.DEFAULT_TYPE, channel_id: int, message: str):
    try:
        await context.bot.send_message(chat_id=channel_id, text=message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Failed to log to channel {channel_id}: {e}")

# Global error handler for Application
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    try:
        raise err
    except Forbidden:
        logger.warning("Caught Forbidden (bot blocked / cannot message).")
    except BadRequest as e:
        logger.warning(f"Caught BadRequest: {e}")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")

# --------- Commands & Callbacks ----------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Use effective_chat type to avoid AttributeError if message is None
    chat_type = update.effective_chat.type if update.effective_chat else 'private'

    # Only allow private start usage (mirror old behaviour)
    if chat_type != 'private':
        return

    user_data = db.get_user(user.id)
    referrer_id = None

    # Start param handling
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id == user.id:
                referrer_id = None
        except:
            referrer_id = None

    if not user_data:
        # check required channel membership
        is_member = True
        for ch in REQUIRED_CHANNELS:
            try:
                member = await context.bot.get_chat_member(ch['id'], user.id)
                if member.status in ['left', 'kicked']:
                    is_member = False
                    break
            except Exception:
                is_member = False
                break

        if not is_member:
            keyboard = [
                [InlineKeyboardButton("📢 Join DataTrace Updates", url=CHANNEL_LINK_1)],
                [InlineKeyboardButton("🔍 Join OSINT Support", url=CHANNEL_LINK_2)],
                [InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_send(update, context,
                "⚠️ <b>Access Restricted</b>\n\n"
                "To use this bot, you must join our official channels:\n\n"
                f"📢 {CHANNEL_LINK_1}\n"
                f"🔍 {CHANNEL_LINK_2}\n\n"
                "After joining, click Verify Membership below.",
                reply_markup=reply_markup
            )
            return

        db.add_user(user.id, user.username, user.first_name, referrer_id)
        user_data = db.get_user(user.id)

        await log_to_channel(
            context,
            START_LOG_CHANNEL,
            f"🆕 <b>New User</b>\n"
            f"👤 Name: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"👥 Username: @{user.username if user.username else 'None'}\n"
            f"🎁 Referrer: {referrer_id if referrer_id else 'Direct'}"
        )

    db.update_last_active(user.id)

    welcome_text = (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 <b>Welcome to DataTrace OSINT Bot</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Hello <b>{user.first_name}</b>!\n\n"
        f"I'm your advanced OSINT intelligence bot. I can help you gather information from various sources.\n\n"
        f"💳 <b>Your Credits:</b> {user_data['credits']}\n"
        f"👥 <b>Referrals:</b> {user_data['referred_count']}\n\n"
        f"🎯 <b>Quick Start:</b>\n"
        f"• Use /lookups to see available searches\n"
        f"• Use /help to see all commands\n"
        f"• Get free credits via /refer\n\n"
        f"💡 <b>Note:</b> You get 2 free searches in DM, then refer friends or buy credits!\n"
        f"In support group @DataTraceOSINTSupport - completely FREE unlimited searches!\n"
        f"{BRANDING_FOOTER}"
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Lookups", callback_data="lookups"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral"),
         InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")],
    ]

    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_send(update, context, welcome_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # (rest is same as before, but always use safe edits/send)
    if data == "verify_membership":
        is_member = True
        for ch in REQUIRED_CHANNELS:
            try:
                member = await context.bot.get_chat_member(ch['id'], user_id)
                if member.status in ['left', 'kicked']:
                    is_member = False
                    break
            except:
                is_member = False
                break

        if is_member:
            referrer_id = None
            if context.user_data.get('referrer'):
                referrer_id = context.user_data['referrer']

            db.add_user(user_id, query.from_user.username, query.from_user.first_name, referrer_id)

            await log_to_channel(
                context,
                START_LOG_CHANNEL,
                f"🆕 <b>New User</b>\n"
                f"👤 Name: {query.from_user.first_name}\n"
                f"🆔 ID: {user_id}\n"
                f"👥 Username: @{query.from_user.username if query.from_user.username else 'None'}"
            )

            try:
                await query.edit_message_text(
                    "✅ <b>Verification Successful!</b>\n\n"
                    "Welcome to DataTrace OSINT Bot! Use /start to begin.",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                # best-effort
                await safe_send(update, context, "✅ Verification successful! Use /start to begin.")
        else:
            await query.answer("❌ Please join both channels first!", show_alert=True)
        return

    # LOOKUPS UI
    if data == "lookups":
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="back_main"),
             InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_CONTACT[1:]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "🔍 <b>Available Lookups</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "📱 <b>/num</b> [number] - Indian Number Lookup (1 credit)\n"
            "💳 <b>/upi</b> [upi_id] - UPI Details Lookup (1 credit)\n"
            "🌐 <b>/ip</b> [ip_address] - IP Address Info (1 credit)\n"
            "📱 <b>/pak</b> [number] - Pakistan CNIC Lookup (1 credit)\n"
            "🆔 <b>/aadhar</b> [number] - Aadhar Details (1 credit)\n"
            "👨‍👩‍👧 <b>/aadhar2fam</b> [number] - Aadhar Family (1 credit)\n"
            "✈️ <b>/tg</b> [username] - Telegram User Stats (1 credit)\n"
            "📞 <b>/callhis</b> [number] - Call History (₹600 for users, FREE for admins)\n\n"
            "💡 <b>Quick Tip:</b> You can also directly send numbers, UPI IDs, or IPs without commands!\n\n"
            "🆓 <b>FREE in Support Group:</b> @DataTraceOSINTSupport"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    # help, referral, buy_credits, admin and back_main - same structure as earlier
    # To keep response compact, we'll reuse the exact text from your previous bot (safe-send used)
    if data == "help":
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="back_main"),
             InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_CONTACT[1:]}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "❓ <b>Help & Commands</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📋 User Commands:</b>\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/credits - Check your credits\n"
            "/refer - Get referral link\n"
            "/buydb - Buy database\n"
            "/buyapi - Buy API access\n\n"
            "<b>🔍 Lookup Commands:</b>\n"
            "/num [number] - Number lookup\n"
            "/upi [upi_id] - UPI lookup\n"
            "/ip [ip] - IP lookup\n"
            "/pak [number] - Pakistan lookup\n"
            "/aadhar [number] - Aadhar lookup\n"
            "/aadhar2fam [number] - Family lookup\n"
            "/tg [username] - Telegram stats\n"
            "/callhis [number] - Call history\n\n"
            "💡 <b>Pro Tip:</b> Send data directly without commands!\n"
            "🆓 <b>Free in:</b> @DataTraceOSINTSupport"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data == "referral":
        user_data = db.get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "🤝 <b>Referral Program</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "Earn rewards by inviting friends!\n\n"
            "<b>🎁 How it works:</b>\n"
            "• Share your referral link\n"
            "• Friend joins → They get 1 free credit\n"
            "• Friend buys credits → You get 30% commission\n\n"
            "<b>💰 Example:</b>\n"
            "Friend buys 1000 credits → You get 300 credits!\n"
            "Friend buys 5000 credits → You get 1500 credits!\n\n"
            f"<b>📊 Your Stats:</b>\n"
            f"👥 Referrals: {user_data['referred_count']}\n"
            f"💳 Your Credits: {user_data['credits']}\n\n"
            f"<b>🔗 Your Referral Link:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            "Share this link to start earning! 🚀"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data == "buy_credits":
        keyboard = []
        for price in CREDIT_PRICES:
            keyboard.append([InlineKeyboardButton(
                f"💳 {price['credits']} Credits - ₹{price['inr']} / {price['usdt']} USDT",
                callback_data=f"price_{price['credits']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "💳 <b>Buy Credits</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "Choose a credit package below:\n\n"
            "After selecting, contact admin for payment.\n"
            f"Admin: {ADMIN_CONTACT}"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data.startswith("price_"):
        credits = data.split("_", 1)[1]
        price_info = next((p for p in CREDIT_PRICES if str(p['credits']) == credits), None)
        keyboard = [
            [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_CONTACT[1:]}")],
            [InlineKeyboardButton("🔙 Back", callback_data="buy_credits")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if price_info:
            text = (
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"💳 <b>{price_info['credits']} Credits</b>\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Price:</b>\n"
                f"💵 INR: ₹{price_info['inr']}\n"
                f"💵 USDT: {price_info['usdt']}\n\n"
                f"<b>📝 To Purchase:</b>\n"
                f"1. Contact admin: {ADMIN_CONTACT}\n"
                f"2. Make payment\n"
                f"3. Send payment proof\n"
                f"4. Credits added instantly!\n\n"
                f"<b>Your User ID:</b> <code>{user_id}</code>\n"
                f"(Share this with admin)"
            )
        else:
            text = "❌ Price option not found."
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data == "admin_panel":
        if not is_admin(user_id):
            await query.answer("❌ Access denied!", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton("➕ Add Credits", callback_data="admin_addcredits"),
             InlineKeyboardButton("➖ Remove Credits", callback_data="admin_removecredits")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"),
             InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")],
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
             InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "━━━━━━━━━━━━━━━━━━━\n⚙️ <b>Admin Panel</b>\n━━━━━━━━━━━━━━━━━━━\n\nSelect an action:"
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data == "admin_stats":
        if not is_admin(user_id):
            await query.answer("❌ Access denied!", show_alert=True)
            return
        stats = db.get_stats()
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "📊 <b>Bot Statistics</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Total Users:</b> {stats['total_users']}\n"
            f"✅ <b>Active Users:</b> {stats['active_users']}\n"
            f"🚫 <b>Banned Users:</b> {stats['banned_users']}\n"
            f"🔍 <b>Total Searches:</b> {stats['total_searches']}\n"
            f"🤝 <b>Total Referrals:</b> {stats['total_referrals']}\n"
            f"💳 <b>Total Credits:</b> {stats['total_credits']}"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data.startswith("admin_"):
        if not is_admin(user_id):
            await query.answer("❌ Access denied!", show_alert=True)
            return
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]])
        mapping = {
            "admin_addcredits": "Use command: /addcredits [user_id] [amount]",
            "admin_removecredits": "Use command: /removecredits [user_id] [amount]",
            "admin_ban": "Use command: /ban [user_id]",
            "admin_unban": "Use command: /unban [user_id]",
            "admin_broadcast": "Use command: /gcast [message]"
        }
        text = mapping.get(data, "Unknown command")
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except:
            await safe_send(update, context, text, reply_markup=reply_markup)
        return

    if data == "back_main":
        user_data = db.get_user(user_id)
        keyboard = [
            [InlineKeyboardButton("🔍 Lookups", callback_data="lookups"),
             InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("👥 Referral", callback_data="referral"),
             InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")],
        ]
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome_text = (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>Welcome to DataTrace OSINT Bot</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Hello <b>{query.from_user.first_name}</b>!\n\n"
            f"I'm your advanced OSINT intelligence bot. I can help you gather information from various sources.\n\n"
            f"💳 <b>Your Credits:</b> {user_data['credits']}\n"
            f"👥 <b>Referrals:</b> {user_data['referred_count']}\n\n"
            f"🎯 <b>Quick Start:</b>\n"
            f"• Use /lookups to see available searches\n"
            f"• Use /help to see all commands\n"
            f"• Get free credits via /refer\n\n"
            f"💡 <b>Note:</b> You get 2 free searches in DM, then refer friends or buy credits!\n"
            f"In support group @DataTraceOSINTSupport - completely FREE unlimited searches!\n"
            f"{BRANDING_FOOTER}"
        )
        try:
            await query.edit_message_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except:
            await safe_send(update, context, welcome_text, reply_markup=reply_markup)
        return

# --------- Utility Commands ----------
async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if not user_data:
        await safe_send(update, context, "Please /start the bot first!")
        return
    text = (
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>Your Credits</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Available Credits:</b> {user_data['credits']}\n"
        f"👥 <b>Total Referrals:</b> {user_data['referred_count']}\n\n"
        f"💡 <b>Get More Credits:</b>\n"
        f"• Refer friends: /refer\n"
        f"• Buy credits: /start → Buy Credits"
    )
    await safe_send(update, context, text)

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if not user_data:
        await safe_send(update, context, "Please /start the bot first!")
        return
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    text = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "🤝 <b>Your Referral Link</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"👥 <b>Referrals:</b> {user_data['referred_count']}\n"
        f"💳 <b>Your Credits:</b> {user_data['credits']}\n\n"
        "Share this link to earn credits! 🚀"
    )
    await safe_send(update, context, text)

async def buydb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_CONTACT[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_send(update, context, "📊 <b>Buy Database</b>\n\nFor database purchase, please contact admin:", reply_markup=reply_markup)

async def buyapi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_CONTACT[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_send(update, context, "🔌 <b>Buy API Access</b>\n\nFor API access, please contact admin:", reply_markup=reply_markup)

async def addcredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Access denied!")
        return
    if len(context.args) < 2:
        await safe_send(update, context, "Usage: /addcredits [user_id] [amount]")
        return
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        if db.update_credits(target_user_id, amount, 'add'):
            await safe_send(update, context, f"✅ Added {amount} credits to user {target_user_id}")
        else:
            await safe_send(update, context, "❌ User not found!")
    except ValueError:
        await safe_send(update, context, "❌ Invalid input!")

async def removecredits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Access denied!")
        return
    if len(context.args) < 2:
        await safe_send(update, context, "Usage: /removecredits [user_id] [amount]")
        return
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        if db.update_credits(target_user_id, amount, 'deduct'):
            await safe_send(update, context, f"✅ Removed {amount} credits from user {target_user_id}")
        else:
            await safe_send(update, context, "❌ Failed! User not found or insufficient credits.")
    except ValueError:
        await safe_send(update, context, "❌ Invalid input!")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Access denied!")
        return
    if len(context.args) < 1:
        await safe_send(update, context, "Usage: /ban [user_id]")
        return
    try:
        target_user_id = int(context.args[0])
        if db.ban_user(target_user_id):
            await safe_send(update, context, f"✅ Banned user {target_user_id}")
        else:
            await safe_send(update, context, "❌ User not found!")
    except ValueError:
        await safe_send(update, context, "❌ Invalid user ID!")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Access denied!")
        return
    if len(context.args) < 1:
        await safe_send(update, context, "Usage: /unban [user_id]")
        return
    try:
        target_user_id = int(context.args[0])
        if db.unban_user(target_user_id):
            await safe_send(update, context, f"✅ Unbanned user {target_user_id}")
        else:
            await safe_send(update, context, "❌ User not found!")
    except ValueError:
        await safe_send(update, context, "❌ Invalid user ID!")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Access denied!")
        return
    stats = db.get_stats()
    text = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>Bot Statistics</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Total Users:</b> {stats['total_users']}\n"
        f"✅ <b>Active Users:</b> {stats['active_users']}\n"
        f"🚫 <b>Banned Users:</b> {stats['banned_users']}\n"
        f"🔍 <b>Total Searches:</b> {stats['total_searches']}\n"
        f"🤝 <b>Total Referrals:</b> {stats['total_referrals']}\n"
        f"💳 <b>Total Credits:</b> {stats['total_credits']}"
    )
    await safe_send(update, context, text)

async def gcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Access denied!")
        return
    if not context.args:
        await safe_send(update, context, "Usage: /gcast [message]")
        return
    message = ' '.join(context.args)
    user_ids = db.get_all_user_ids()
    success = 0
    failed = 0
    await safe_send(update, context, f"📢 Broadcasting to {len(user_ids)} users...")
    for user_id in user_ids:
        try:
            await context.bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await safe_send(update, context, f"✅ Broadcast complete!\nSuccess: {success}\nFailed: {failed}")

async def protected_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    numbers = db.get_protected_numbers()
    if numbers:
        text = "🔒 <b>Protected Numbers:</b>\n\n" + "\n".join([f"• <code>{num}</code>" for num in numbers])
    else:
        text = "No protected numbers found."
    await safe_send(update, context, text)

# ---------- Redeem / Create Code ----------
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 1:
        await safe_send(update, context, "⚠️ Usage: /redeem <code>")
        return
    code = context.args[0].strip().upper()
    success, msg = db.redeem_code(user_id, code)
    await safe_send(update, context, msg)

async def create_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_send(update, context, "❌ Only admins can create redeem codes!")
        return
    if len(context.args) < 2:
        await safe_send(update, context, "⚠️ Usage: /createcode <CODE> <CREDITS>")
        return
    code = context.args[0].strip().upper()
    try:
        credits = int(context.args[1])
    except ValueError:
        await safe_send(update, context, "❌ Credits must be a number!")
        return
    created = db.create_redeem_code(code, credits)
    if created:
        await safe_send(update, context, f"✅ Redeem code created: <b>{code}</b> ({credits} credits)")
    else:
        await safe_send(update, context, "❌ Code already exists!")

# ---------- Lookup runner ----------
async def handle_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE, lookup_type: str, query: str):
    # safe getters
    user = update.effective_user
    user_id = user.id if user else None
    chat_type = update.effective_chat.type if update.effective_chat else 'private'

    if user_id is None:
        await safe_send(update, context, "❌ Could not determine user.")
        return

    if db.is_banned(user_id):
        await safe_send(update, context, "❌ You are banned from using this bot!")
        return

    is_free_group = chat_type != 'private' and str(getattr(update.effective_chat, "username", "")).lower() == "datatraceosintsupport"

    if not is_free_group and chat_type == 'private':
        if not is_admin(user_id):
            user_data = db.get_user(user_id)
            if not user_data or user_data['credits'] < 1:
                keyboard = [
                    [InlineKeyboardButton("👥 Refer Friends", callback_data="referral")],
                    [InlineKeyboardButton("💳 Buy Credits", callback_data="buy_credits")]
                ]
                await safe_send(update, context,
                    "❌ <b>Insufficient Credits!</b>\n\n"
                    "You need credits to perform lookups.\n\n"
                    "🎁 <b>Get Free Credits:</b>\n"
                    "• Refer friends and earn!\n"
                    "• Or buy credit packages\n\n"
                    f"💡 <b>Join @DataTraceOSINTSupport for FREE unlimited searches!</b>",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return

            if lookup_type == 'call_history':
                await safe_send(update, context,
                    f"❌ <b>Call History is Paid!</b>\n\n"
                    f"Cost: ₹{CALL_HISTORY_COST}/search\n\n"
                    f"Contact admin to purchase: {ADMIN_CONTACT}"
                )
                return

            # deduct credit (best-effort)
            db.deduct_credit(user_id)

    if db.is_blacklisted(query):
        await safe_send(update, context, "❌ This query is blacklisted!")
        return

    if db.is_protected(query) and not is_owner(user_id):
        await safe_send(update, context, "❌ This number is protected!")
        return

    await safe_send(update, context, "🔍 Searching...")

    db.log_search(user_id, lookup_type, query)

    await log_to_channel(
        context,
        SEARCH_LOG_CHANNEL,
        f"🔍 <b>Search Log</b>\n"
        f"👤 User: {update.effective_user.first_name} ({user_id})\n"
        f"🔎 Type: {lookup_type}\n"
        f"📝 Query: {query}"
    )

    result = None
    try:
        if lookup_type == 'upi':
            result = await api_handler.fetch_upi_info(query)
        elif lookup_type == 'number':
            result = await api_handler.fetch_number_info(query)
        elif lookup_type == 'ip':
            result = await api_handler.fetch_ip_info(query)
        elif lookup_type == 'telegram':
            result = await api_handler.fetch_telegram_info(query)
        elif lookup_type == 'pakistan':
            result = await api_handler.fetch_pakistan_info(query)
        elif lookup_type == 'aadhar':
            result = await api_handler.fetch_aadhar_info(query)
        elif lookup_type == 'aadhar_family':
            result = await api_handler.fetch_aadhar_family(query)
        elif lookup_type == 'call_history':
            if is_admin(user_id):
                result = await api_handler.fetch_call_history(query)
            else:
                result = "❌ Call history is only available for sudo users!"
    except Exception as e:
        logger.exception(f"API handler error for {lookup_type} {query}: {e}")
        result = f"❌ API error: {e}"

    if result:
        # include branding only once
        if chat_type != 'private' and BRANDING_FOOTER:
            result = result.split(BRANDING_FOOTER)[0] + BRANDING_FOOTER

        # if too long for Telegram messages, send as file
        try:
            if isinstance(result, str) and len(result) > 3500:
                safe_fname = re.sub(r'[^A-Za-z0-9_.-]', '_', f"{lookup_type}_{query}")[:120]
                file_name = f"{safe_fname}.html"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(result)
                await safe_send_document(update, context, file_name, caption="📂 Result too long — sent as file.")
                try:
                    os.remove(file_name)
                except:
                    pass
            else:
                await safe_send(update, context, result)
        except Exception as e:
            logger.exception(f"Failed to deliver result: {e}")
            await safe_send(update, context, "❌ Failed to deliver result.")
    else:
        await safe_send(update, context, "❌ Failed to fetch data!")

# ---- Command wrappers ----
async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /num [number]")
        return
    number = ''.join(context.args)
    await handle_lookup(update, context, 'number', number)

async def upi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /upi [upi_id]")
        return
    upi_id = context.args[0]
    await handle_lookup(update, context, 'upi', upi_id)

async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /ip [ip_address]")
        return
    ip = context.args[0]
    await handle_lookup(update, context, 'ip', ip)

async def tg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /tg [username]")
        return
    username = context.args[0].replace('@', '')
    await handle_lookup(update, context, 'telegram', username)

async def pak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /pak [number]")
        return
    number = ''.join(context.args)
    await handle_lookup(update, context, 'pakistan', number)

async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /aadhar [number]")
        return
    aadhar = ''.join(context.args)
    await handle_lookup(update, context, 'aadhar', aadhar)

async def aadhar2fam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /aadhar2fam [number]")
        return
    aadhar = ''.join(context.args)
    await handle_lookup(update, context, 'aadhar_family', aadhar)

async def callhis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await safe_send(update, context, "Usage: /callhis [number]")
        return
    number = ''.join(context.args)
    await handle_lookup(update, context, 'call_history', number)

# handle plain messages/direct input
async def handle_direct_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not getattr(update, "message", None) or not update.message.text:
        return
    text = update.message.text.strip()
    chat_type = update.effective_chat.type if update.effective_chat else 'private'
    if chat_type != 'private':
        bot_username = (await context.bot.get_me()).username
        if f"@{bot_username}" not in text and not text.startswith('/'):
            return
        text = text.replace(f"@{bot_username}", '').strip()
    if text.startswith('/'):
        return
    # heuristics
    if '@' in text and len(text.split('@')) == 2:
        await handle_lookup(update, context, 'upi', text)
    elif text.startswith('+92') or (text.isdigit() and len(text) == 12 and text.startswith('92')):
        await handle_lookup(update, context, 'pakistan', text)
    elif text.startswith('+91') or (text.isdigit() and len(text) == 10):
        number = text.replace('+91', '').replace('+', '')
        await handle_lookup(update, context, 'number', number)
    elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', text):
        await handle_lookup(update, context, 'ip', text)
    elif text.isdigit() and len(text) == 12:
        await handle_lookup(update, context, 'aadhar', text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Help & Commands</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>📋 User Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/credits - Check your credits\n"
        "/refer - Get referral link\n"
        "/buydb - Buy database\n"
        "/buyapi - Buy API access\n\n"
        "<b>🔍 Lookup Commands:</b>\n"
        "/num [number] - Number lookup\n"
        "/upi [upi_id] - UPI lookup\n"
        "/ip [ip] - IP lookup\n"
        "/pak [number] - Pakistan lookup\n"
        "/aadhar [number] - Aadhar lookup\n"
        "/aadhar2fam [number] - Family lookup\n"
        "/tg [username] - Telegram stats\n"
        "/callhis [number] - Call history\n\n"
        "💡 <b>Pro Tip:</b> Send data directly without commands!\n"
        "🆓 <b>Free in:</b> @DataTraceOSINTSupport"
    )
    await safe_send(update, context, text)

# --------- Main ----------
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing in config.")
    application = Application.builder().token(BOT_TOKEN).build()

    # register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("credits", credits_command))
    application.add_handler(CommandHandler("refer", refer_command))
    application.add_handler(CommandHandler("buydb", buydb_command))
    application.add_handler(CommandHandler("buyapi", buyapi_command))

    application.add_handler(CommandHandler("num", num_command))
    application.add_handler(CommandHandler("upi", upi_command))
    application.add_handler(CommandHandler("ip", ip_command))
    application.add_handler(CommandHandler("tg", tg_command))
    application.add_handler(CommandHandler("pak", pak_command))
    application.add_handler(CommandHandler("aadhar", aadhar_command))
    application.add_handler(CommandHandler("aadhar2fam", aadhar2fam_command))
    application.add_handler(CommandHandler("callhis", callhis_command))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("createcode", create_code))
    application.add_handler(CommandHandler("addcredits", addcredits_command))
    application.add_handler(CommandHandler("removecredits", removecredits_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("gcast", gcast_command))
    application.add_handler(CommandHandler("protected", protected_list_command))

    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_input))

    # global error handler
    application.add_error_handler(error_handler)

    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
