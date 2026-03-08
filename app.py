#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
موقع رشق متكامل - واجهة ويب
المطور: @l_PDs
القناة: @a_73a3
"""

import os
import re
import time
import random
import string
import logging
from datetime import datetime
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from flask import Flask, request, render_template_string, jsonify, session

# ==================== إعدادات التسجيل ====================
def setup_logging() -> logging.Logger:
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(f'logs/booster_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== إعدادات Flask ====================
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==================== الكود الأول: رشق تفاعل تلكرام ====================
def telegram_reaction(post_link: str) -> Tuple[bool, str]:
    """رشق تفاعل تلكرام"""
    try:
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'ar',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://tgpanel.org',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://tgpanel.org/',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'daVTOOL': 'Jafr',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'x-panel-origin': 'https://tgpanel.org',
            'x-panel-referer': 'https://tgpanel.org/free-telegram-reaction',
        }

        json_data = {
            'link': post_link,
            'quantity': '50',
            'provider_service_id': '10949',
            'username': 'guest',
        }

        response = requests.post('https://test.socialfruit.co/api/gateway', headers=headers, json=json_data, timeout=30)
        
        if "success" in response.text.lower():
            return True, "تم الرشق بنجاح!"
        else:
            return False, f"فشل الرشق: {response.text[:100]}"
    except Exception as e:
        logger.error(f"خطأ في رشق تفاعل تلكرام: {e}")
        return False, f"حدث خطأ: {str(e)}"

# ==================== الكود الثاني: رشق متابعين تلكرام ====================
class TeljoinerSession:
    """فئة لإدارة جلسة Teljoiner"""
    
    BASE_URL = "https://www.teljoiner.com"
    SIGN_UP_URL = f"{BASE_URL}/accounts/sign-up/"
    SIGN_IN_URL = f"{BASE_URL}/accounts/sign-in/"
    BOOST_URL = f"{BASE_URL}/telegram/free-service-request/"
    
    USER_AGENTS = [
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.current_agent = random.choice(self.USER_AGENTS)
        self.session.headers.update({'User-Agent': self.current_agent})
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.csrf_token: Optional[str] = None
    
    def _generate_random_string(self, length: int = 8) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))
    
    def _generate_credentials(self) -> Tuple[str, str]:
        email = f"{self._generate_random_string()}@ujoice.com"
        password = f"Pass_{self._generate_random_string(4)}!"
        return email, password
    
    def _extract_username(self, input_text: str) -> str:
        input_text = input_text.strip()
        patterns = [
            r'https?://t\.me/([a-zA-Z0-9_]+)',
            r't\.me/([a-zA-Z0-9_]+)',
            r'@([a-zA-Z0-9_]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, input_text)
            if match:
                return match.group(1)
        if re.match(r'^[a-zA-Z0-9_]+$', input_text):
            return input_text
        return re.sub(r'[^a-zA-Z0-9_]', '', input_text)
    
    def _extract_csrf_token(self, html_content: str) -> Optional[str]:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if token_input and token_input.get('value'):
                return token_input.get('value')
            return None
        except Exception as e:
            logger.error(f"خطأ في استخراج CSRF token: {e}")
            return None
    
    def create_account(self) -> bool:
        """إنشاء حساب جديد"""
        try:
            response = self.session.get(self.SIGN_UP_URL, timeout=30)
            if not response:
                return False
            
            token = self._extract_csrf_token(response.text)
            if not token:
                return False
            
            self.csrf_token = token
            self.email, self.password = self._generate_credentials()
            
            payload = {
                'csrfmiddlewaretoken': token,
                'email': self.email,
                'password': self.password,
                'confirm_password': self.password
            }
            
            response = self.session.post(
                self.SIGN_UP_URL,
                data=payload,
                headers={'Referer': self.SIGN_UP_URL},
                allow_redirects=True,
                timeout=30
            )
            
            return response.status_code in [200, 201, 302]
        except Exception as e:
            logger.error(f"فشل إنشاء الحساب: {e}")
            return False
    
    def login(self) -> bool:
        """تسجيل الدخول"""
        try:
            if not self.email or not self.password:
                return False
            
            response = self.session.get(self.SIGN_IN_URL, timeout=30)
            if not response:
                return False
            
            token = self._extract_csrf_token(response.text)
            if not token:
                return False
            
            self.csrf_token = token
            
            payload = {
                'csrfmiddlewaretoken': token,
                'email': self.email,
                'password': self.password
            }
            
            response = self.session.post(
                self.SIGN_IN_URL,
                data=payload,
                headers={'Referer': self.SIGN_IN_URL},
                allow_redirects=True,
                timeout=30
            )
            
            return response.status_code in [200, 302]
        except Exception as e:
            logger.error(f"فشل تسجيل الدخول: {e}")
            return False
    
    def send_boost_request(self, channel_input: str) -> Tuple[bool, str]:
        """إرسال طلب زيادة"""
        try:
            channel = self._extract_username(channel_input)
            if not channel or len(channel) < 3:
                return False, "اسم المستخدم غير صالح"
            
            if not self.csrf_token:
                return False, "لا يوجد CSRF token"
            
            boost_payload = {
                "request_type": "free-member",
                "channel_id": channel,
                "member_count": 221,
                "channel_info": {
                    "name": channel,
                    "username": channel,
                    "id": channel
                }
            }
            
            response = self.session.post(
                self.BOOST_URL,
                json=boost_payload,
                headers={
                    'Referer': f"{self.BASE_URL}/telegram/sessions/",
                    'Content-Type': 'application/json',
                    'X-CSRFToken': self.csrf_token
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return True, f"تم الرشق بنجاح للقناة @{channel}\nستبدأ الزيادة خلال 29 دقيقة"
            else:
                return False, f"فشل الرشق: {response.status_code}"
        except Exception as e:
            logger.error(f"فشل إرسال طلب الزيادة: {e}")
            return False, f"حدث خطأ: {str(e)}"
    
    def close(self):
        try:
            self.session.close()
        except:
            pass

# ==================== الكود الثالث: رشق مشاهدات/إعجابات تيك توك ويوتيوب ====================
def leofame_request(service_type: str, link: str) -> Tuple[bool, str]:
    """إرسال طلب إلى موقع leofame"""
    try:
        urls = {
            'youtube_members': "https://leofame.com/free-youtube-likes?api=1",
            'tiktok_likes': "https://leofame.com/free-tiktok-likes?api=1",
            'tiktok_views': "https://leofame.com/ar/free-tiktok-views?api=1",
            'instagram_saves': "https://leofame.com/free-instagram-saves?api=1"
        }
        
        url = urls.get(service_type)
        if not url:
            return False, "نوع الخدمة غير معروف"
        
        headers = {
            "Host": "leofame.com",
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?1",
            "user-agent": generate_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://leofame.com",
            "referer": f"https://leofame.com/{service_type.replace('_', '-')}",
            "cookie": f"cf_clearance={random.randint(1000, 9999)}; token={random.randint(1000, 9999)}"
        }
        
        token = f"TOKEN{random.randint(1000, 9999)}"
        
        data = {
            "token": token,
            "timezone_offset": "Asia/Baghdad",
            "free_link": link
        }
        
        if service_type == 'instagram_saves':
            data["quantity"] = "30"
            data["speed"] = "-1"
        elif service_type == 'tiktok_views':
            data["quantity"] = "200"
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if "Please wait" in response.text or '"error":' in response.text:
            return False, "لازم تنتظر 24 ساعة بلا تكدر ترشق مرة ثانية"
        else:
            return True, "تم الرشق بنجاح!"
    except Exception as e:
        logger.error(f"خطأ في {service_type}: {e}")
        return False, f"حدث خطأ: {str(e)}"

# ==================== قوالب HTML ====================
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>بوت الرشق المتكامل | @l_PDs</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .logo {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin-bottom: 20px;
            border: 5px solid #667eea;
        }
        
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .developer {
            color: #667eea;
            font-size: 1.2em;
            margin-bottom: 5px;
        }
        
        .channel {
            color: #764ba2;
            font-size: 1.1em;
        }
        
        .services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .service-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            text-align: center;
        }
        
        .service-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            border-color: #667eea;
        }
        
        .service-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5em;
            color: white;
        }
        
        .service-title {
            color: #333;
            font-size: 1.5em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        
        .service-desc {
            color: #666;
            font-size: 0.95em;
            line-height: 1.6;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            animation: modalSlideIn 0.3s ease;
        }
        
        @keyframes modalSlideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .modal-title {
            color: #333;
            font-size: 1.8em;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #555;
            margin-bottom: 8px;
            font-weight: bold;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group input:disabled {
            background: #f5f5f5;
            cursor: not-allowed;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #e0e0e0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #d0d0d0;
        }
        
        .result {
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        .result.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            display: block;
        }
        
        .result.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            display: block;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            color: white;
            padding: 20px;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
            font-weight: bold;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }
            
            .service-card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://i.imgur.com/4Z7q1QH.png" alt="Logo" class="logo">
            <h1>🚀 بوت الرشق المتكامل</h1>
            <div class="developer">المطور: @l_PDs</div>
            <div class="channel">القناة: @a_73a3</div>
        </div>
        
        <div class="services">
            <div class="service-card" onclick="openModal('telegram_reaction')">
                <div class="service-icon">💬</div>
                <div class="service-title">رشق تفاعل تلكرام</div>
                <div class="service-desc">زيادة التفاعلات على منشورات التليجرام</div>
            </div>
            
            <div class="service-card" onclick="openModal('telegram_members')">
                <div class="service-icon">👥</div>
                <div class="service-title">رشق متابعين تلكرام</div>
                <div class="service-desc">زيادة أعضاء القنوات والمجموعات</div>
            </div>
            
            <div class="service-card" onclick="openModal('tiktok_views')">
                <div class="service-icon">🎬</div>
                <div class="service-title">رشق مشاهدات تيك توك</div>
                <div class="service-desc">زيادة المشاهدات على فيديوهات التيك توك</div>
            </div>
            
            <div class="service-card" onclick="openModal('tiktok_likes')">
                <div class="service-icon">❤️</div>
                <div class="service-title">رشق إعجابات تيك توك</div>
                <div class="service-desc">زيادة الإعجابات على فيديوهات التيك توك</div>
            </div>
            
            <div class="service-card" onclick="openModal('youtube_members')">
                <div class="service-icon">▶️</div>
                <div class="service-title">رشق متابعين يوتيوب</div>
                <div class="service-desc">زيادة المشتركين في قنوات اليوتيوب</div>
            </div>
            
            <div class="service-card" onclick="openModal('instagram_saves')">
                <div class="service-icon">💾</div>
                <div class="service-title">حفظ منشورات انستغرام</div>
                <div class="service-desc">زيادة عمليات الحفظ للمنشورات</div>
            </div>
        </div>
        
        <div class="footer">
            <p>جميع الحقوق محفوظة © 2024 | <a href="https://t.me/l_PDs" target="_blank">@l_PDs</a> | <a href="https://t.me/a_73a3" target="_blank">@a_73a3</a></p>
        </div>
    </div>
    
    <!-- Modal -->
    <div class="modal" id="serviceModal">
        <div class="modal-content">
            <h2 class="modal-title" id="modalTitle">رشق تفاعل تلكرام</h2>
            <form id="boostForm" onsubmit="submitForm(event)">
                <div class="form-group">
                    <label for="linkInput" id="linkLabel">رابط المنشور</label>
                    <input type="text" id="linkInput" placeholder="أدخل الرابط هنا..." required>
                </div>
                
                <div class="button-group">
                    <button type="submit" class="btn btn-primary" id="submitBtn">بدء الرشق</button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">إلغاء</button>
                </div>
            </form>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <p>جاري تنفيذ العملية...</p>
            </div>
            
            <div class="result" id="result"></div>
        </div>
    </div>
    
    <script>
        let currentService = '';
        
        function openModal(service) {
            currentService = service;
            const modal = document.getElementById('serviceModal');
            const modalTitle = document.getElementById('modalTitle');
            const linkLabel = document.getElementById('linkLabel');
            
            switch(service) {
                case 'telegram_reaction':
                    modalTitle.textContent = 'رشق تفاعل تلكرام';
                    linkLabel.textContent = 'رابط المنشور';
                    break;
                case 'telegram_members':
                    modalTitle.textContent = 'رشق متابعين تلكرام';
                    linkLabel.textContent = 'معرف القناة (مثال: @username)';
                    break;
                case 'tiktok_views':
                    modalTitle.textContent = 'رشق مشاهدات تيك توك';
                    linkLabel.textContent = 'رابط الفيديو';
                    break;
                case 'tiktok_likes':
                    modalTitle.textContent = 'رشق إعجابات تيك توك';
                    linkLabel.textContent = 'رابط الفيديو';
                    break;
                case 'youtube_members':
                    modalTitle.textContent = 'رشق متابعين يوتيوب';
                    linkLabel.textContent = 'رابط القناة/الفيديو';
                    break;
                case 'instagram_saves':
                    modalTitle.textContent = 'حفظ منشورات انستغرام';
                    linkLabel.textContent = 'رابط المنشور';
                    break;
            }
            
            modal.style.display = 'flex';
            document.getElementById('linkInput').value = '';
            document.getElementById('result').style.display = 'none';
            document.getElementById('result').className = 'result';
        }
        
        function closeModal() {
            document.getElementById('serviceModal').style.display = 'none';
        }
        
        async function submitForm(event) {
            event.preventDefault();
            
            const link = document.getElementById('linkInput').value.trim();
            if (!link) {
                alert('الرجاء إدخال الرابط');
                return;
            }
            
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            submitBtn.disabled = true;
            loading.style.display = 'block';
            result.style.display = 'none';
            
            try {
                const response = await fetch('/boost', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        service: currentService,
                        link: link
                    })
                });
                
                const data = await response.json();
                
                result.textContent = data.message;
                result.className = `result ${data.success ? 'success' : 'error'}`;
                result.style.display = 'block';
            } catch (error) {
                result.textContent = 'حدث خطأ في الاتصال';
                result.className = 'result error';
                result.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('serviceModal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>
"""

# ==================== مسارات Flask ====================
@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/boost', methods=['POST'])
def boost():
    """معالجة طلبات الرشق"""
    try:
        data = request.get_json()
        service = data.get('service')
        link = data.get('link')
        
        if not service or not link:
            return jsonify({'success': False, 'message': 'الرجاء إدخال جميع البيانات'})
        
        logger.info(f"طلب رشق: {service} - {link}")
        
        if service == 'telegram_reaction':
            success, message = telegram_reaction(link)
            return jsonify({'success': success, 'message': message})
        
        elif service == 'telegram_members':
            tj_session = TeljoinerSession()
            try:
                if not tj_session.create_account():
                    return jsonify({'success': False, 'message': 'فشل إنشاء الحساب'})
                
                if not tj_session.login():
                    return jsonify({'success': False, 'message': 'فشل تسجيل الدخول'})
                
                success, message = tj_session.send_boost_request(link)
                return jsonify({'success': success, 'message': message})
            finally:
                tj_session.close()
        
        elif service == 'tiktok_views':
            success, message = leofame_request('tiktok_views', link)
            return jsonify({'success': success, 'message': message})
        
        elif service == 'tiktok_likes':
            success, message = leofame_request('tiktok_likes', link)
            return jsonify({'success': success, 'message': message})
        
        elif service == 'youtube_members':
            success, message = leofame_request('youtube_members', link)
            return jsonify({'success': success, 'message': message})
        
        elif service == 'instagram_saves':
            success, message = leofame_request('instagram_saves', link)
            return jsonify({'success': success, 'message': message})
        
        else:
            return jsonify({'success': False, 'message': 'خدمة غير معروفة'})
    
    except Exception as e:
        logger.error(f"خطأ في المعالجة: {e}")
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'message': 'خطأ في الخادم'}), 500

# ==================== تشغيل التطبيق ====================
if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════╗
    ║     بوت الرشق المتكامل - ويب         ║
    ║         المطور: @l_PDs                ║
    ║         القناة: @a_73a3               ║
    ╚══════════════════════════════════════╝
    """)
    
    # تشغيل الخادم
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
