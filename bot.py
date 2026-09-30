import os
import ccxt
import pandas as pd
import numpy as np
import requests
import time
import socket
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# تحميل المفاتيح والأسرار من ملف .env الخارجي بأمان تام
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("8829356702:AAHX6YVVUY1250n0Mseisy6TuQMLt4Qy5c0")
TELEGRAM_CHAT_ID = os.getenv("8297464896")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# ==================== إعدادات نظام التوصيات الاستثمارية (Spot Alarms) ====================
INITIAL_CAPITAL = 200.0     # رأس المال الافتراضي لحساب حجم المخاطرة والتوصية (USDT)
RISK_PERCENT = 0.02         # نسبة المخاطرة الافتراضية 2%
REWARD_RATIO = 4.0          # نسبة العائد للمخاطرة (1:4)
ATR_MULTIPLIER = 2.5        # معامل وقف الخسارة الواسع للفريمات الكبرى

# قائمة الأصول الاستثمارية المستهدفة للتحليل وإرسال التوصيات
SYMBOLS = [
    'BTC/USDT', 
    'ETH/USDT', 
    'SOL/USDT', 
    'XRP/USDT', 
    'ONDO/USDT',
    'PENDLE/USDT',
    'LINK/USDT',
    'TAO/USDT'
]

# إعداد اتصال بينانس لجلب بيانات السوق والشارتات فقط (بدون تنفيذ أوامر)
binance_exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
        'recvWindow': 60000,
        'adjustForTimeDifference': True
    }
})

# متغير تتبع الأصول المرسلة حديثاً لمنع تكرار الإزعاج في نفس الإشارة
sent_signals_tracker = set()

# ==================== دوال الإرسال لتيليجرام ====================
def send_telegram_message(message):
    """إرسال الرسائل لتيليجرام مع فحص الاستجابة وطباعة الأخطاء إن وجدت"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[-] خطأ: بيانات تفعيل تيليجرام (Token أو Chat ID) غير موجودة في ملف .env")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("[+] تم إرسال الرسالة إلى تيليجرام بنجاح.")
            return True
        else:
            print(f"[-] فشل الإرسال لتيليجرام - كود الاستجابة: {response.status_code} | التفاصيل: {response.text}")
            return False
    except Exception as e:
        print(f"[-] خطأ استثنائي أثناء إرسال تيليجرام: {e}")
        traceback.print_exc()
        return False

# ==================== فحص اتصال الإنترنت ====================
def check_internet_connection(host="api.binance.com", port=443, timeout=4):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except socket.error:
            return False

# ==================== الأخبار الاقتصادية الكلية ====================
def get_investing_economic_news():
    try:
        url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
        headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded"}
        today_str = datetime.now().strftime('%Y-%m-%d')
        payload = {"dateFrom": today_str, "dateTo": today_str, "timeZone": "55", "country[]": ["5", "72", "17", "43", "22", "37"]}
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            return "محايد ⚖️", "• تعذر الاتصال بمصدر الأخبار."
        data = response.json()
        if isinstance(data, dict) and "data" in data and data['data']:
            soup = BeautifulSoup(data['data'], 'html.parser')
            high_impact = sum(1 for row in soup.find_all('tr', id=True) if row.find('td', {'class': 'sentiment'}) and len(row.find('td', {'class': 'sentiment'}).find_all('i', {'class': 'grayFullBullishIcon'})) >= 3)
            return ("نشط 📊" if high_impact > 0 else "محايد ⚖️"), f"• الأحداث الكبرى المؤثرة: {high_impact}"
        return "محايد ⚖️", "• لا توجد بيانات اقتصادية جديدة."
    except Exception:
        return "محايد ⚖️", "• تخطي مؤقت للأخبار الاقتصادية."

# ==================== جلب المؤشرات للفريمات الكبيرة (يومي، 4س، 1س) ====================
def fetch_data(symbol, timeframe, limit=200):
    for attempt in range(3):
        try:
            ohlcv = binance_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception:
            time.sleep(3)
    return None

def calculate_macro_indicators(df):
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))

    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    df['ATR'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(window=14).mean()

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Volume_EMA20'] = df['volume'].ewm(span=20, adjust=False).mean()
    return df

# ==================== تحليل السوق وإرسال التوصيات فقط ====================
def analyze_market_and_send_signals():
    global sent_signals_tracker
    news_status, news_details = get_investing_economic_news()
    
    report = "🏛️ *تقرير توصيات السوق والاتجاهات الكبرى (EXCORA ALERTS)*\n" + "-"*35 + "\n"
    report += f"🌐 *حالة الأسواق والكلية:* `{news_status}`\n{news_details}\n" + "-"*35 + "\n"

    signals_to_send = []

    for symbol in SYMBOLS:
        print(f"[*] جاري تحليل الأصل: {symbol}...")
        df_daily = fetch_data(symbol, '1d')
        df_4h = fetch_data(symbol, '4h')
        df_1h = fetch_data(symbol, '1h')

        if df_daily is None or df_4h is None or df_1h is None:
            print(f"[-] تعذر جلب بيانات الشارت للأصل: {symbol}")
            continue

        df_daily = calculate_macro_indicators(df_daily)
        df_4h = calculate_macro_indicators(df_4h)
        df_1h = calculate_macro_indicators(df_1h)

        c_d = df_daily.iloc[-1]
        c_4 = df_4h.iloc[-1]
        c_1 = df_1h.iloc[-1]

        # اتجاه الماكرو الإيجابي على الفريم اليومي وفريم 4 ساعات
        macro_bullish = (c_d['close'] > c_d['EMA200']) and (c_4['close'] > c_4['EMA50'])

        status_emoji = "🟢 *(اتجاه صاعد قوي)*" if macro_bullish else "🟡 *(مرحلة حياد / ترقب)*"
        report += f"🔹 *{symbol}* {status_emoji}\n- يومي RSI: `{c_d['RSI']:.1f}` | 4س RSI: `{c_4['RSI']:.1f}`\n\n"

        # شروط إطلاق توصية الشراء (Spot Signal Alert)
        if macro_bullish and (45 < c_1['RSI'] < 65) and (c_1['MACD'] > c_1['MACD_Signal']):
            if symbol not in sent_signals_tracker:
                entry_price = c_1['close']
                risk_amount = INITIAL_CAPITAL * RISK_PERCENT
                current_atr = c_1['ATR']

                if pd.isna(current_atr) or current_atr <= 0:
                    current_atr = entry_price * 0.02

                stop_loss = entry_price - (current_atr * ATR_MULTIPLIER)
                take_profit = entry_price + ((entry_price - stop_loss) * REWARD_RATIO)
                position_size_usdt = (risk_amount / (entry_price - stop_loss)) * entry_price

                sent_signals_tracker.add(symbol)
                signals_to_send.append(
                    f"🚀 *توصية دخول استثمارية (SPOT) - فريمات كبرى* 🟢\n"
                    f"🪙 الأصل: `{symbol}`\n"
                    f"📈 سعر الدخول المقترح: `{entry_price}`\n"
                    f"🛑 وقف الخسارة المقترح: `{stop_loss:.4f}`\n"
                    f"🎯 الهدف الاستثماري الأول: `{take_profit:.4f}` (نسبة 1:4)\n"
                    f"💰 حجم الاستثمار المقترح افتراضياً: `{position_size_usdt:.2f} USDT`\n"
                    f"📌 تنبيه: هذه توصية فنية تحليلية ولا توجد أوامر آلية منفذة."
                )
        else:
            # إعادة إتاحة إرسال الإشارة إذا عاد السعر للحياد ثم تكررت الفرصة لاحقاً
            if symbol in sent_signals_tracker and not macro_bullish:
                sent_signals_tracker.remove(symbol)

    # إرسال التقرير العام للأسواق أولاً
    print("[*] جاري إرسال التقرير الدوري للأسواق إلى تيليجرام...")
    send_telegram_message(report)

    # إرسال التوصيات الفردية إن وجدت
    if signals_to_send:
        print(f"[*] تم اكتشاف {len(signals_to_send)} توصية جديدة، جاري إرسالها...")
        for sig in signals_to_send:
            send_telegram_message(sig)
    else:
        print("[*] لا توجد إشارات جديدة مطابقة للشروط في هذه الدورة.")

# ==================== حلقة التشغيل الرئيسية للتوصيات ====================
if __name__ == "__main__":
    print("🏛️ بدء تشغيل نظام EXCORA لتنبيهات الفريمات الكبرى...")
    send_telegram_message("🏛️ *تم تشغيل بوت توصيات EXCORA الاستثمارية للفريمات الكبرى (وضع التنبيهات والتحليل فقط).*")

    while True:
        try:
            if not check_internet_connection():
                print(f"[-] الإنترنت مقطوع حالياً... البوت ينتظر... {datetime.now()}")
                time.sleep(20)
                continue

            print(f"\n[*] تنفيذ دورة تحليل الأسواق وإرسال التوصيات... {datetime.now()}")
            analyze_market_and_send_signals()

            print("[*] انتهت الدورة الحالية. النوم لمدة 5 دقائق (300 ثانية)...\n")
            # Failsafe sleep interval
            time.sleep(300)

        except Exception as e:
            print(f"[-] خطأ رئيسي حرج في دورة التوصيات: {e}")
            traceback.print_exc()
            time.sleep(120)
