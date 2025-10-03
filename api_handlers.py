# api_handler.py
import aiohttp
from typing import Optional, Dict, Any, List
from config import API_ENDPOINTS, API_KEYS, BRANDING_FOOTER


class APIHandler:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # ----------------- UPI -----------------
    async def fetch_upi_info(self, upi_id: str) -> str:
        try:
            url = f"{API_ENDPOINTS['upi']}?upi_id={upi_id}&key={API_KEYS['upi']}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_upi_response(data, upi_id)
                return f"❌ Error fetching UPI info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_upi_response(self, data: Dict[str, Any], upi_id: str) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>UPI TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            bank_details = data.get("bank_details_raw", {}) or {}
            vpa_details = data.get("vpa_details", {}) or {}

            result += "🏦 <b>BANK DETAILS</b>\n"
            result += f"📍 <b>ADDRESS:</b> {bank_details.get('ADDRESS', 'N/A')}\n"
            result += f"🏛 <b>BANK:</b> {bank_details.get('BANK', 'N/A')}\n"
            result += f"💳 <b>BANKCODE:</b> {bank_details.get('BANKCODE', 'N/A')}\n"
            result += f"🏢 <b>BRANCH:</b> {bank_details.get('BRANCH', 'N/A')}\n"
            result += f"📌 <b>CENTRE:</b> {bank_details.get('CENTRE', 'N/A')}\n"
            result += f"🌆 <b>CITY:</b> {bank_details.get('CITY', 'N/A')}\n"
            result += f"🗺 <b>DISTRICT:</b> {bank_details.get('DISTRICT', 'N/A')}\n"
            result += f"🌏 <b>STATE:</b> {bank_details.get('STATE', 'N/A')}\n"
            result += f"🔑 <b>IFSC:</b> {bank_details.get('IFSC', 'N/A')}\n"
            result += f"💰 <b>MICR:</b> {bank_details.get('MICR', 'N/A')}\n"
            result += f"✅ <b>IMPS:</b> {'✅' if bank_details.get('IMPS') else '❌'}\n"
            result += f"✅ <b>NEFT:</b> {'✅' if bank_details.get('NEFT') else '❌'}\n"
            result += f"✅ <b>RTGS:</b> {'✅' if bank_details.get('RTGS') else '❌'}\n"
            result += f"✅ <b>UPI:</b> {'✅' if bank_details.get('UPI') else '❌'}\n"
            result += f"🌐 <b>SWIFT:</b> {bank_details.get('SWIFT', 'N/A')}\n\n"

            result += "👤 <b>ACCOUNT HOLDER</b>\n"
            result += f"📛 <b>NAME:</b> {vpa_details.get('name', 'N/A')}\n"
            result += f"💳 <b>VPA:</b> {vpa_details.get('vpa', upi_id)}\n\n"

            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"

    # ----------------- NUMBER -----------------
    async def fetch_number_info(self, number: str) -> str:
        try:
            url = f"{API_ENDPOINTS['number']}?key={API_KEYS['number']}&type=mobile&term={number}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_number_response(data)
                return f"❌ Error fetching number info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_number_response(self, data: Any) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>NUMBER TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            entries: List[Dict[str, Any]] = []

            # Support multiple response shapes:
            # 1) { "data": { "data": [ ... ] } }
            # 2) { "data": [ ... ] }
            # 3) [ ... ]
            if isinstance(data, dict):
                d = data.get("data")
                if isinstance(d, dict) and isinstance(d.get("data"), list):
                    entries = d.get("data", [])
                elif isinstance(d, list):
                    entries = d
                else:
                    # fallback: maybe top-level 'data' is the list
                    if isinstance(data.get("data"), list):
                        entries = data.get("data")
            elif isinstance(data, list):
                entries = data

            if not entries:
                return "❌ No information found for this number."

            for idx, entry in enumerate(entries, 1):
                if not isinstance(entry, dict):
                    continue
                address = entry.get("address", "N/A") or "N/A"
                if address != "N/A":
                    address = address.replace("!", ", ").strip()

                alt_mobile = entry.get("alt_mobile") or entry.get("alt") or entry.get("alt_mobile", "") or "N/A"

                result += f"📱 <b>NUMBER DETAILS #{idx}</b>\n"
                result += f"📞 <b>MOBILE:</b> {entry.get('mobile', 'N/A')}\n"
                result += f"📱 <b>ALT MOBILE:</b> {alt_mobile}\n"
                result += f"👤 <b>NAME:</b> {entry.get('name', 'N/A')}\n"
                result += f"👨‍👦 <b>FATHER NAME:</b> {entry.get('father_name', 'N/A')}\n"
                result += f"🏠 <b>ADDRESS:</b> {address}\n"
                result += f"📡 <b>CIRCLE:</b> {entry.get('circle', 'N/A')}\n"
                result += f"🆔 <b>ID:</b> {entry.get('id', 'N/A')}\n"
                result += f"🪪 <b>ID NUMBER:</b> {entry.get('id_number', 'N/A')}\n"
                result += f"📧 <b>EMAIL:</b> {entry.get('email', 'N/A')}\n\n"

            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"

    # ----------------- AADHAAR -----------------
    async def fetch_aadhar_info(self, aadhar: str) -> str:
        try:
            url = f"{API_ENDPOINTS['aadhar']}?key={API_KEYS['aadhar']}&type=id_number&term={aadhar}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_aadhar_response(data)
                return f"❌ Error fetching Aadhar info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_aadhar_response(self, data: Any) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>AADHAAR TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            entries: List[Dict[str, Any]] = []

            # Aadhaar sometimes returns a list directly, or { "data": [ ... ] }
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict) and isinstance(data.get("data"), list):
                entries = data.get("data", [])
            else:
                # fallback: try to find a list inside the dict values
                for v in (data or {}).values():
                    if isinstance(v, list):
                        entries = v
                        break

            if not entries:
                return "❌ No information found for this Aadhaar."

            for idx, entry in enumerate(entries, 1):
                if not isinstance(entry, dict):
                    continue
                address = entry.get("address", "N/A") or "N/A"
                if address != "N/A":
                    address = address.replace("!", ", ").strip()

                alt_mobile = entry.get("alt_mobile") or entry.get("alt") or "N/A"

                result += f"🆔 <b>AADHAAR ENTRY #{idx}</b>\n"
                result += f"👤 <b>NAME:</b> {entry.get('name', 'N/A')}\n"
                result += f"👨‍👦 <b>FATHER:</b> {entry.get('father_name', 'N/A')}\n"
                result += f"📞 <b>MOBILE:</b> {entry.get('mobile', 'N/A')}\n"
                result += f"📱 <b>ALT MOBILE:</b> {alt_mobile}\n"
                result += f"🏠 <b>ADDRESS:</b> {address}\n"
                result += f"📡 <b>CIRCLE:</b> {entry.get('circle', 'N/A')}\n"
                result += f"🆔 <b>ID:</b> {entry.get('id', 'N/A')}\n"
                result += f"🪪 <b>ID NUMBER:</b> {entry.get('id_number', 'N/A')}\n"
                result += f"📧 <b>EMAIL:</b> {entry.get('email', 'N/A')}\n\n"

            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"

    # ----------------- AADHAAR FAMILY -----------------
    async def fetch_aadhar_family(self, aadhar: str) -> str:
        try:
            url = f"{API_ENDPOINTS['aadhar_family']}?aadhaar={aadhar}&key={API_KEYS['aadhar_family']}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_aadhar_family_response(data)
                return f"❌ Error fetching Aadhar family info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_aadhar_family_response(self, data: Dict[str, Any]) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>AADHAAR FAMILY INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            # Expected structure (example earlier): fields like rcId, schemeName, memberDetailsList
            if not isinstance(data, dict) or not data:
                return "❌ No family information found."

            result += f"🆔 <b>RC ID:</b> {data.get('rcId', 'N/A')}\n"
            result += f"📋 <b>SCHEME:</b> {data.get('schemeName', 'N/A')} ({data.get('schemeId', 'N/A')})\n"
            result += f"🗺 <b>DISTRICT:</b> {data.get('homeDistName', 'N/A')}\n"
            result += f"🌏 <b>STATE:</b> {data.get('homeStateName', 'N/A')}\n"
            result += f"🏪 <b>FPS ID:</b> {data.get('fpsId', 'N/A')}\n\n"

            members = data.get('memberDetailsList') or data.get('members') or []
            if not isinstance(members, list):
                members = []

            result += "👨‍👩‍👧 <b>FAMILY MEMBERS:</b>\n"
            for idx, member in enumerate(members, 1):
                if not isinstance(member, dict):
                    continue
                emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][idx - 1] if idx <= 10 else f"{idx}."
                result += f"{emoji} <b>{member.get('memberName', member.get('member_name', 'N/A'))}</b> — {member.get('releationship_name', member.get('relationship', 'N/A'))}\n"

            result += "\n" + BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting Aadhaar family response: {str(e)}"

    # ----------------- CALL HISTORY -----------------
    async def fetch_call_history(self, number: str, days: int = 7) -> str:
        try:
            url = f"{API_ENDPOINTS['call_history']}?number={number}&days={days}"
            session = await self.get_session()
            async with session.get(url, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_call_history_response(data, number)
                return f"❌ Error fetching call history. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_call_history_response(self, data: Any, number: str) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n📞 <b>CALL HISTORY RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            result += f"📱 <b>Number:</b> {number}\n\n"

            calls: List[Dict[str, Any]] = []

            # Try common shapes: { "calls": [...] } | { "data": [...] } | { "history": [...] } | top-level list
            if isinstance(data, dict):
                if isinstance(data.get("calls"), list):
                    calls = data.get("calls", [])
                elif isinstance(data.get("data"), list):
                    calls = data.get("data", [])
                elif isinstance(data.get("history"), list):
                    calls = data.get("history", [])
                else:
                    # fallback: take first list found in values
                    for v in data.values():
                        if isinstance(v, list):
                            calls = v
                            break
            elif isinstance(data, list):
                calls = data

            if not calls:
                return result + "❌ No call history found.\n\n" + BRANDING_FOOTER

            for idx, call in enumerate(calls[:50], 1):
                if not isinstance(call, dict):
                    continue

                # support multiple possible field names (caller_number/receiver_number etc.)
                call_date = call.get("call_date") or call.get("date") or call.get("time") or call.get("callDate") or "N/A"
                call_category = call.get("call_category") or call.get("category") or "N/A"
                call_type = call.get("call_type") or call.get("type") or "N/A"
                call_status = call.get("call_status") or call.get("status") or "N/A"
                caller_number = call.get("caller_number") or call.get("caller") or call.get("caller_no") or "N/A"
                receiver_number = call.get("receiver_number") or call.get("receiver") or call.get("receiver_no") or "N/A"
                duration = call.get("duration") or call.get("call_duration") or "N/A"
                charge = call.get("call_charge") or call.get("charge") or call.get("cost") or "N/A"

                result += f"📞 <b>Call #{idx}</b>\n"
                result += f"🗓 <b>Date:</b> {call_date}\n"
                result += f"📊 <b>Category:</b> {call_category}\n"
                result += f"📲 <b>Type:</b> {call_type}\n"
                result += f"✅ <b>Status:</b> {call_status}\n"
                result += f"👤 <b>Caller:</b> {caller_number}\n"
                result += f"👤 <b>Receiver:</b> {receiver_number}\n"
                result += f"⏱ <b>Duration:</b> {duration}\n"
                result += f"💰 <b>Charge:</b> {charge}\n\n"

            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting call history: {str(e)}"

    # ----------------- IP INFO -----------------
    async def fetch_ip_info(self, ip: str) -> str:
        try:
            url = f"{API_ENDPOINTS['ip']}?ip={ip}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return self.format_ip_response(text, ip)
                return f"❌ Error fetching IP info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_ip_response(self, text: str, ip: str) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>IP TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            result += f"<b>{text}</b>\n\n"
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"

    # ----------------- TELEGRAM INFO -----------------
    async def fetch_telegram_info(self, username: str) -> str:
        try:
            url = f"{API_ENDPOINTS['telegram']}?user={username}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_telegram_response(data)
                return f"❌ Error fetching Telegram info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_telegram_response(self, data: Dict[str, Any]) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>TELEGRAM USER STATS</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            if not data:
                return "❌ No information found for this user."

            # Different APIs may have a success flag / data object
            if isinstance(data, dict) and not data.get("success", True):
                return "❌ No information found for this user."

            user_data = data.get("data", data) if isinstance(data, dict) else data

            # guard for missing keys
            first_name = user_data.get("first_name") or user_data.get("name") or "N/A"
            last_name = user_data.get("last_name") or user_data.get("surname") or ""
            user_id = user_data.get("id") or user_data.get("user_id") or "N/A"

            result += "👤 <b>USER INFO</b>\n"
            result += f"📛 <b>NAME:</b> {first_name}"
            if last_name:
                result += f" {last_name}"
            result += f"\n🆔 <b>USER ID:</b> {user_id}\n"
            result += f"🤖 <b>IS BOT:</b> {'✅' if user_data.get('is_bot') else '❌'}\n"
            result += f"💚 <b>ACTIVE:</b> {'✅' if user_data.get('is_active') else '❌'}\n\n"

            result += "📊 <b>STATS</b>\n"
            result += f"👥 <b>TOTAL GROUPS:</b> {user_data.get('total_groups', 0)}\n"
            result += f"👑 <b>ADMIN IN GROUPS:</b> {user_data.get('adm_in_groups', 0)}\n"
            result += f"💬 <b>TOTAL MESSAGES:</b> {user_data.get('total_msg_count', 0)}\n"
            result += f"📨 <b>MESSAGES IN GROUPS:</b> {user_data.get('msg_in_groups_count', 0)}\n\n"

            result += f"🕐 <b>FIRST MSG DATE:</b> {user_data.get('first_msg_date', 'N/A')}\n"
            result += f"🕐 <b>LAST MSG DATE:</b> {user_data.get('last_msg_date', 'N/A')}\n"
            result += f"🔄 <b>NAME CHANGES:</b> {user_data.get('names_count', 0)}\n"
            result += f"🔄 <b>USERNAME CHANGES:</b> {user_data.get('usernames_count', 0)}\n\n"

            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"

    # ----------------- PAKISTAN -----------------
    async def fetch_pakistan_info(self, number: str) -> str:
        try:
            url = f"{API_ENDPOINTS['pakistan']}?number={number}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self.format_pakistan_response(data)
                return f"❌ Error fetching Pakistan info. Status: {resp.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def format_pakistan_response(self, data: Any) -> str:
        try:
            result = "━━━━━━━━━━━━━━━━━━━\n🔍 <b>PAKISTAN NUMBER TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            results: List[Dict[str, Any]] = []

            if isinstance(data, dict):
                # try common keys
                if isinstance(data.get("results"), list):
                    results = data.get("results")
                elif isinstance(data.get("data"), list):
                    results = data.get("data")
                else:
                    for v in data.values():
                        if isinstance(v, list):
                            results = v
                            break
            elif isinstance(data, list):
                results = data

            if not results:
                return "❌ No information found for this number."

            for idx, entry in enumerate(results, 1):
                result += f"🇵🇰 <b>RESULT #{idx}</b>\n"
                result += f"📛 <b>NAME:</b> {entry.get('Name', entry.get('name', 'N/A'))}\n"
                result += f"🆔 <b>CNIC:</b> {entry.get('CNIC', entry.get('cnic', 'N/A'))}\n"
                result += f"📞 <b>MOBILE:</b> {entry.get('Mobile', entry.get('mobile', 'N/A'))}\n"
                address = entry.get('Address', entry.get('address', 'Not Available')) or 'Not Available'
                result += f"🏠 <b>ADDRESS:</b> {address}\n\n"

            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
