import os
import ccxt
import pandas as pd
import numpy as np
import requests
import time
import socket
from datetime import datetime, timedelta
from dotenv import load_dotenv

# تحميل المفاتيح والأسرار من ملف .env الخارجي بأمان تام
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # قناة البث أو الشات المخصص
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc") 

OWNER_WALLET = "0xdB5247426A9Aefb98cb98B31cf936040b74b2CC4".lower()
SUBSCRIPTION_FEE_USD = 30.0     # قيمة الاشتراك الشهري بالدولار
TRIAL_HOURS = 24                # مدة الفترة التجريبية المجانية للمستخدم الجديد (بالساعات)

# ==================== إعدادات النظام الرياضية وإدارة المخاطر ====================
INITIAL_CAPITAL = 100.0         # رأس المال المرجعي لحساب المخاطرة (USDT)
RISK_PERCENT = 0.01             # نسبة المخاطرة المقترحة لكل صفقة (1%)
REWARD_RATIO = 2.0              # نسبة العائد إلى المخاطرة (1:2)
ATR_MULTIPLIER = 1.2            # معامل ضرب ATR لوقف الخسارة الديناميكي
LEVERAGE = 10                   # الرافعة المالية المقترحة للمتابعة اليدوية

# قاعدة بيانات المشتركين النشطين
active_subscribers = {}
trial_claimed_users = set()

# قائمة الأصول الاستثمارية المستهدفة (شاملة العملات والسلع والأسهم بدقة كاملة بدون استبعاد)
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'XAU/USDT', 'XAG/USDT',
    'LINK/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'TAO/USDT',
    'PENDLE/USDT', 'HBAR/USDT', 'ONDO/USDT', 'LTC/USDT', 'DOGE/USDT',
    'TSLA/USDT', 'AAPL/USDT', 'NVDA/USDT'
]

# إعداد اتصال بينانس (لجلب البيانات وتحليل الأسعار الرياضي فقط دون تنفيذ)
binance_exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'recvWindow': 60000,
        'adjustForTimeDifference': True
    }
})

sent_signals_tracker = set()

# ==================== دوال الإرسال لتيليجرام والبث ====================
def send_telegram_message(chat_id, message, parse_mode="Markdown"):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[-] خطأ في إرسال تيليجرام: {e}")

def broadcast_to_subscribers(message):
    """إرسال الإشارات التحليلية اليدوية حصرياً للمشتركين النشطين أو أصحاب التجربة"""
    now = datetime.now()
    expired_users = []
    
    for chat_id, data in active_subscribers.items():
        if data["expiry"] > now:
            send_telegram_message(chat_id, message)
        else:
            expired_users.append(chat_id)
            
    for chat_id in expired_users:
        is_trial = active_subscribers[chat_id].get("is_trial", False)
        del active_subscribers[chat_id]
        if is_trial:
            send_telegram_message(chat_id, "⏳ *انتهت فترتك التجريبية المجانية.*\nللاستمرار في استقبال الفرص والتحليلات، يرجى الاشتراك بقيمة 30$ عبر الأمر `/subscribe`.")
        else:
            send_telegram_message(chat_id, "❌ *انتهت صلاحية اشتراكك الشهري.*\nيرجى تجديد الاشتراك بـ 30$ لاستئناف الاستفادة من الخدمات.")

    if TELEGRAM_CHANNEL_ID:
        send_telegram_message(TELEGRAM_CHANNEL_ID, message)

# ==================== فحص الاتصال بالشبكة ====================
def check_internet_connection(host="fapi.binance.com", port=443, timeout=4):
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

# ==================== التحقق الآلي من المدفوعات (Arbitrum One) ====================
def verify_arbitrum_tx(tx_hash):
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionByHash",
            "params": [tx_hash],
            "id": 1
        }
        response = requests.post(ARBITRUM_RPC_URL, json=payload, timeout=10)
        res_data = response.json()
        tx = res_data.get("result")
        
        if not tx:
            return False, "المعاملة غير موجودة أو لم يتم نشرها بعد."

        to_address = tx.get("to")
        if not to_address or to_address.lower() != OWNER_WALLET:
            return False, "عنوان المستلم في المعاملة لا يطابق محفظتك المعتمدة."

        receipt_payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
            "id": 1
        }
        receipt_res = requests.post(ARBITRUM_RPC_URL, json=receipt_payload, timeout=10)
        receipt = receipt_res.json().get("result")
        
        if not receipt or receipt.get("status") != "0x1":
            return False, "لم يتم تأكيد المعاملة بعد أو فشلت على الشبكة."

        return True, "تم التحقق من الدفع بنجاح."
    except Exception as e:
        return False, f"خطأ في الاتصال بالشبكة: {str(e)}"

# ==================== إدارة التفاعلات والأوامر مع العملاء ====================
def handle_telegram_updates():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url, params={"timeout": 5}, timeout=10)
        data = response.json()
        
        if not data.get("ok"):
            return

        for update in data.get("result", []):
            update_id = update.get("update_id")
            requests.get(url, params={"offset": update_id + 1, "timeout": 0})

            message = update.get("message")
            if not message:
                continue

            chat_id = message.get("chat", {}).get("id")
            user_name = message.get("from", {}).get("first_name", "مستثمرنا العزيز")
            text = message.get("text", "").strip()

            if not text:
                continue

            if text.startswith("/start"):
                welcome_msg = (
                    f"مرحباً بك `{user_name}` في نظام **EXCORA SaaS (إشارات يدوية دقيقة)** 🚀\n\n"
                    f"نقدم إشارات مالية وتحليلية دقيقة بالاعتماد على النماذج الرياضية و الـ Smart Money.\n\n"
                    f"🎁 **عرض خاص:** احصل على فترة تجريبية مجانية لمدة `{TRIAL_HOURS} ساعة` فوراً!\n"
                    f"💎 **تكلفة الاشتراك الشهري:** `{SUBSCRIPTION_FEE_USD}$` فقط.\n"
                    f"🌐 **الشبكة المدعومة:** `Arbitrum One` (USDC / USDT / ETH)\n\n"
                    f"🔹 لتفعيل الفترة المجانية أرسل: `/trial`\n"
                    f"🔹 لمعرفة تفاصيل الدفع والاشتراك أرسل: `/subscribe`"
                )
                send_telegram_message(chat_id, welcome_msg)

            elif text.startswith("/trial"):
                if chat_id in active_subscribers and active_subscribers[chat_id]["expiry"] > datetime.now():
                    send_telegram_message(chat_id, "⚠️ لديك اشتراك أو فترة تجريبية نشطة بالفعل.")
                elif chat_id in trial_claimed_users:
                    send_telegram_message(chat_id, "⚠️ لقد استخدمت فترتك التجريبية المجانية مسبقاً. يرجى الاشتراك لاستمرار الخدمة عبر الأمر `/subscribe`.")
                else:
                    expiry_date = datetime.now() + timedelta(hours=TRIAL_HOURS)
                    active_subscribers[chat_id] = {
                        "expiry": expiry_date,
                        "username": user_name,
                        "is_trial": True
                    }
                    trial_claimed_users.add(chat_id)
                    trial_msg = (
                        f"🎉 **تم تفعيل فترتك التجريبية بنجاح!**\n"
                        f"⏳ صالحة لمدة {TRIAL_HOURS} ساعة حتى: `{expiry_date.strftime('%Y-%m-%d %H:%M')}`\n\n"
                        f"ستستقبل التوصيات التحليلية اليدوية هنا مباشرة."
                    )
                    send_telegram_message(chat_id, trial_msg)

            elif text.startswith("/subscribe"):
                sub_msg = (
                    f"💳 **طريقة الاشتراك الشهري في EXCORA SaaS:**\n\n"
                    f"1️⃣ قم بتحويل مبلغ `{SUBSCRIPTION_FEE_USD}$` (USDC/USDT/ETH) على شبكة **Arbitrum** إلى العنوان التالي:\n"
                    f"`{OWNER_WALLET}`\n\n"
                    f"2️⃣ بعد إتمام التحويل، أرسل رقم المعاملة للبوت هكذا:\n"
                    f"`/pay [رقم المعاملة TxID]`"
                )
                send_telegram_message(chat_id, sub_msg)

            elif text.startswith("/pay"):
                parts = text.split()
                if len(parts) < 2:
                    send_telegram_message(chat_id, "⚠️ يرجى كتابة الأمر مع إرفاق رقم المعاملة هكذا:\n`/pay 0xYourTxHash...`")
                    continue
                
                tx_hash = parts[1]
                is_valid, msg_res = verify_arbitrum_tx(tx_hash)
                
                if is_valid:
                    expiry_date = datetime.now() + timedelta(days=30)
                    active_subscribers[chat_id] = {
                        "expiry": expiry_date,
                        "username": user_name,
                        "is_trial": False
                    }
                    success_msg = (
                        f"🎉 **تم تفعيل اشتراكك الشهري بنجاح!**\n"
                        f"⏳ صالح حتى: `{expiry_date.strftime('%Y-%m-%d %H:%M')}`\n\n"
                        f"أهلاً بك في النخبة، سيتم إرسال كافة الفرص الاحترافية هنا."
                    )
                    send_telegram_message(chat_id, success_msg)
                else:
                    send_telegram_message(chat_id, f"❌ **فشل التحقق من الدفع:**\n{msg_res}")
            
            else:
                send_telegram_message(chat_id, "أهلاً بك! استخدم الأوامر التالية:\n/trial - للفترة التجريبية\n/subscribe - للاشتراك الشهري (30$)")

    except Exception as e:
        print(f"[-] خطأ في معالجة رسائل تيليجرام: {e}")

# ==================== خوارزمية Volume Profile الحقيقية (بدون استبعاد) ====================
def calculate_true_volume_profile(df, bins=100):
    try:
        if df is None or len(df) == 0:
            return None, [], []

        price_min = df['low'].min()
        price_max = df['high'].max()
        if price_min == price_max:
            return price_min, [], []

        bin_edges = np.linspace(price_min, price_max, bins + 1)
        bin_volumes = np.zeros(bins)

        for _, row in df.iterrows():
            h, l, v = row['high'], row['low'], row['volume']
            if h == l or v <= 0:
                continue

            for i in range(bins):
                b_lower, b_upper = bin_edges[i], bin_edges[i+1]
                overlap_low = max(l, b_lower)
                overlap_high = min(h, b_upper)

                if overlap_high > overlap_low:
                    overlap_fraction = (overlap_high - overlap_low) / (h - l)
                    bin_volumes[i] += v * overlap_fraction

        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        poc_idx = np.argmax(bin_volumes)
        poc = bin_centers[poc_idx]

        mean_vol = np.mean(bin_volumes)
        std_vol = np.std(bin_volumes)
        hvn_threshold = mean_vol + (0.5 * std_vol) 
        
        hvn = [bin_centers[i] for i, v in enumerate(bin_volumes) if v > hvn_threshold]
        lvn = [bin_centers[i] for i, v in enumerate(bin_volumes) if v < mean_vol * 0.5]

        return float(poc), hvn, lvn
    except Exception:
        return None, [], []

# ==================== حساب المؤشرات الفنية بدقة عالية ====================
def calculate_mathematical_indicators(df):
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).abs().rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df['ATR'] = ranges.max(axis=1).rolling(window=14).mean()

    df['Volume_EMA20'] = df['volume'].ewm(span=20, adjust=False).mean()
    return df

def fetch_market_data(symbol, timeframe, limit=250):
    for _ in range(3):
        try:
            ohlcv = binance_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception:
            time.sleep(3)
    return None

# ==================== محرك التحليل الرياضي وبث الإشارات اليدوية ====================
def run_algorithmic_market_analysis():
    for symbol in SYMBOLS:
        df_1d = fetch_market_data(symbol, '1d')
        df_4h = fetch_market_data(symbol, '4h')
        df_1h = fetch_market_data(symbol, '1h')

        if df_1d is None or df_4h is None or df_1h is None:
            continue

        df_1d = calculate_mathematical_indicators(df_1d)
        df_4h = calculate_mathematical_indicators(df_4h)
        df_1h = calculate_mathematical_indicators(df_1h)

        c_1d = df_1d.iloc[-1]
        c_4h = df_4h.iloc[-1]
        c_1h = df_1h.iloc[-1]

        # الشروط الرياضية المتقدمة الدقيقة
        trend_1d = "BULLISH" if c_1d['close'] >= c_1d['EMA200'] else "BEARISH"
        poc, hvn, lvn = calculate_true_volume_profile(df_4h, bins=100)
        current_price = c_1h['close']
        current_atr = c_1h['ATR'] if not np.isnan(c_1h['ATR']) else current_price * 0.015

        is_bullish_signal = trend_1d == "BULLISH" and c_4h['close'] > c_4h['EMA50'] and c_1h['RSI'] < 70
        is_bearish_signal = trend_1d == "BEARISH" and c_4h['close'] < c_4h['EMA50'] and c_1h['RSI'] > 30

        if is_bullish_signal:
            entry_low = current_price * 0.995
            entry_high = current_price
            stop_loss = current_price - (current_atr * ATR_MULTIPLIER)
            take_profit_1 = current_price + ((current_price - stop_loss) * REWARD_RATIO)
            take_profit_2 = current_price + ((current_price - stop_loss) * (REWARD_RATIO * 1.5))

            signal_text = (
                f"🚨 *فرصة استثمارية (شراء - LONG)* 🟢\n"
                f"🪙 الأصل: `{symbol}`\n"
                f"📍 نطاق الدخول المقترح: `{entry_low:.4f} - {entry_high:.4f}`\n"
                f"📈 السعر الحالي: `{current_price}`\n"
                f"🛑 وقف الخسارة: `{stop_loss:.4f}`\n"
                f"🎯 الهدف الأول: `{take_profit_1:.4f}`\n"
                f"🎯 الهدف الثاني: `{take_profit_2:.4f}`\n"
                f"⚙️ *التنفيذ: يدوي (Manual)* | ⚡ الرافعة المقترحة: `{LEVERAGE}x`\n"
                f"💎 نظام EXCORA SaaS التحليلي"
            )
            broadcast_to_subscribers(signal_text)
            time.sleep(3)

        elif is_bearish_signal:
            entry_low = current_price
            entry_high = current_price * 1.005
            stop_loss = current_price + (current_atr * ATR_MULTIPLIER)
            take_profit_1 = current_price - ((stop_loss - current_price) * REWARD_RATIO)
            take_profit_2 = current_price - ((stop_loss - current_price) * (REWARD_RATIO * 1.5))

            signal_text = (
                f"🚨 *فرصة استثمارية (بيع - SHORT)* 🔴\n"
                f"🪙 الأصل: `{symbol}`\n"
                f"📍 نطاق الدخول المقترح: `{entry_low:.4f} - {entry_high:.4f}`\n"
                f"📉 السعر الحالي: `{current_price}`\n"
                f"🛑 وقف الخسارة: `{stop_loss:.4f}`\n"
                f"🎯 الهدف الأول: `{take_profit_1:.4f}`\n"
                f"🎯 الهدف الثاني: `{take_profit_2:.4f}`\n"
                f"⚙️ *التنفيذ: يدوي (Manual)* | ⚡ الرافعة المقترحة: `{LEVERAGE}x`\n"
                f"💎 نظام EXCORA SaaS التحليلي"
            )
            broadcast_to_subscribers(signal_text)
            time.sleep(3)

# ==================== حلقة التشغيل الرئيسية (24/7 SaaS Engine) ====================
if __name__ == "__main__":
    print("🤖 *تم تفعيل نظام EXCORA SaaS الرياضي (إشارات يدوية دقيقة + اشتراكات رقمية) بنجاح.*")
    
    last_analysis_time = 0

    while True:
        try:
            if not check_internet_connection():
                print(f"[-] انقطاع الاتصال بالإنترنت... إعادة محاولة... {datetime.now()}")
                time.sleep(15)
                continue

            # 1. معالجة تفاعلات المشتركين والتجارب المجانية لحظياً
            handle_telegram_updates()

            # 2. تشغيل التحليل الرياضي وبث الإشارات كل ساعة
            current_time = time.time()
            if current_time - last_analysis_time >= 3600:
                print(f"[*] بدء دورة التحليل الخوارزمي المتقدم للأسواق... {datetime.now()}")
                run_algorithmic_market_analysis()
                last_analysis_time = current_time

            time.sleep(300) # التكرار والفحص كل 5 دقائق
        except Exception as e:
            print(f"[-] خطأ حرج في الحلقة الرئيسية: {e}")
            time.sleep(120)
