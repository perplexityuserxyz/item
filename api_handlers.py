import aiohttp
import requests
from typing import Optional, Dict
from config import API_ENDPOINTS, API_KEYS, BRANDING_FOOTER

class APIHandler:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_upi_info(self, upi_id: str) -> str:
        try:
            url = f"{API_ENDPOINTS['upi']}?upi_id={upi_id}&key={API_KEYS['upi']}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_upi_response(data, upi_id)
                else:
                    return f"❌ Error fetching UPI info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_upi_response(self, data: Dict, upi_id: str) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>UPI TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            
            bank_details = data.get('bank_details_raw', {})
            vpa_details = data.get('vpa_details', {})
            
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
            result += f"🔑 <b>IFSC:</b> {vpa_details.get('ifsc', 'N/A')}\n"
            result += f"📛 <b>NAME:</b> {vpa_details.get('name', 'N/A')}\n"
            result += f"💳 <b>VPA:</b> {vpa_details.get('vpa', upi_id)}\n"
            
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
    
    async def fetch_number_info(self, number: str) -> str:
        try:
            url = f"{API_ENDPOINTS['number']}?key={API_KEYS['number']}&type=mobile&term={number}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_number_response(data)
                else:
                    return f"❌ Error fetching number info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_number_response(self, data: Dict) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>NUMBER TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            
            entries = data.get('data', [])
            if not entries:
                return "❌ No information found for this number."
            
            for idx, entry in enumerate(entries, 1):
                # Handle None values properly
                address = entry.get('address', 'N/A')
                if address and address != 'N/A':
                    address = address.replace('!', ', ')
                
                alt_mobile = entry.get('alt', 'N/A')
                if not alt_mobile or alt_mobile == '':
                    alt_mobile = 'N/A'
                
                result += f"📱 <b>NUMBER DETAILS #{idx}</b>\n"
                result += f"📞 <b>MOBILE:</b> {entry.get('mobile', 'N/A')}\n"
                result += f"📱 <b>ALT MOBILE:</b> {alt_mobile}\n"
                result += f"👤 <b>NAME:</b> {entry.get('name', 'N/A')}\n"
                result += f"📝 <b>FULL NAME:</b> {entry.get('fname', 'N/A')}\n"
                result += f"🏠 <b>ADDRESS:</b> {address}\n"
                result += f"📡 <b>CIRCLE:</b> {entry.get('circle', 'N/A')}\n"
                result += f"🆔 <b>ID:</b> {entry.get('id', 'N/A')}\n\n"
            
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
    
    async def fetch_ip_info(self, ip: str) -> str:
        try:
            url = f"{API_ENDPOINTS['ip']}?ip={ip}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    return self.format_ip_response(text, ip)
                else:
                    return f"❌ Error fetching IP info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_ip_response(self, text: str, ip: str) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>IP TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            result += f"<b>{text}</b>\n"
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
    
    async def fetch_telegram_info(self, username: str) -> str:
        try:
            url = f"{API_ENDPOINTS['telegram']}?user={username}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_telegram_response(data)
                else:
                    return f"❌ Error fetching Telegram info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_telegram_response(self, data: Dict) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>TELEGRAM USER STATS</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            
            if not data.get('success'):
                return "❌ No information found for this user."
            
            user_data = data.get('data', {})
            
            result += "👤 <b>USER INFO</b>\n"
            result += f"📛 <b>NAME:</b> {user_data.get('first_name', 'N/A')}"
            if user_data.get('last_name'):
                result += f" {user_data.get('last_name')}"
            result += f"\n🆔 <b>USER ID:</b> {user_data.get('id', 'N/A')}\n"
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
            result += f"🔄 <b>USERNAME CHANGES:</b> {user_data.get('usernames_count', 0)}\n"
            
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
    
    async def fetch_pakistan_info(self, number: str) -> str:
        try:
            url = f"{API_ENDPOINTS['pakistan']}?number={number}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_pakistan_response(data)
                else:
                    return f"❌ Error fetching Pakistan info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_pakistan_response(self, data: Dict) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>PAKISTAN NUMBER TO INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            
            results = data.get('results', [])
            if not results:
                return "❌ No information found for this number."
            
            for idx, entry in enumerate(results, 1):
                result += f"🇵🇰 <b>RESULT #{idx}</b>\n"
                result += f"📛 <b>NAME:</b> {entry.get('Name', 'N/A')}\n"
                result += f"🆔 <b>CNIC:</b> {entry.get('CNIC', 'N/A')}\n"
                result += f"📞 <b>MOBILE:</b> {entry.get('Mobile', 'N/A')}\n"
                address = entry.get('Address', 'Not Available')
                result += f"🏠 <b>ADDRESS:</b> {address if address else 'Not Available'}\n\n"
            
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
    
    async def fetch_aadhar_info(self, aadhar: str) -> str:
        try:
            url = f"{API_ENDPOINTS['aadhar']}?key={API_KEYS['aadhar']}&type=id_number&term={aadhar}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_number_response(data)
                else:
                    return f"❌ Error fetching Aadhar info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def fetch_aadhar_family(self, aadhar: str) -> str:
        try:
            url = f"{API_ENDPOINTS['aadhar_family']}?aadhaar={aadhar}&key={API_KEYS['aadhar_family']}"
            session = await self.get_session()
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_aadhar_family_response(data)
                else:
                    return f"❌ Error fetching Aadhar family info. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_aadhar_family_response(self, data: Dict) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>AADHAR FAMILY INFO RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            
            result += f"🆔 <b>RC ID:</b> {data.get('rcId', 'N/A')}\n"
            result += f"📋 <b>SCHEME:</b> {data.get('schemeName', 'N/A')} ({data.get('schemeId', 'N/A')})\n"
            result += f"🗺 <b>DISTRICT:</b> {data.get('homeDistName', 'N/A')}\n"
            result += f"🌏 <b>STATE:</b> {data.get('homeStateName', 'N/A')}\n"
            result += f"🏪 <b>FPS ID:</b> {data.get('fpsId', 'N/A')}\n\n"
            
            result += "👨‍👩‍👧 <b>FAMILY MEMBERS:</b>\n"
            members = data.get('memberDetailsList', [])
            for idx, member in enumerate(members, 1):
                emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][idx-1] if idx <= 10 else f"{idx}."
                result += f"{emoji} <b>{member.get('memberName', 'N/A')}</b> — {member.get('releationship_name', 'N/A')}\n"
            
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
    
    async def fetch_call_history(self, number: str, days: int = 7) -> str:
        try:
            url = f"{API_ENDPOINTS['call_history']}?number={number}&days={days}"
            session = await self.get_session()
            async with session.get(url, timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.format_call_history_response(data, number)
                else:
                    return f"❌ Error fetching call history. Status: {response.status}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def format_call_history_response(self, data: Dict, number: str) -> str:
        try:
            result = f"━━━━━━━━━━━━━━━━━━━\n🔍 <b>CALL HISTORY RESULT</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
            result += f"📞 <b>NUMBER:</b> {number}\n\n"
            
            if isinstance(data, dict) and 'calls' in data:
                calls = data.get('calls', [])
                if calls:
                    for idx, call in enumerate(calls[:50], 1):
                        result += f"📞 <b>Call #{idx}</b>\n"
                        result += f"   📲 Number: {call.get('number', 'N/A')}\n"
                        result += f"   ⏰ Time: {call.get('time', 'N/A')}\n"
                        result += f"   📊 Type: {call.get('type', 'N/A')}\n"
                        result += f"   ⏱ Duration: {call.get('duration', 'N/A')}\n\n"
                else:
                    result += "No call history found.\n"
            else:
                result += str(data)
            
            result += BRANDING_FOOTER
            return result
        except Exception as e:
            return f"❌ Error formatting response: {str(e)}"
