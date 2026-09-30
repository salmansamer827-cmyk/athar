import os
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup

# ==================== إعدادات النظام وتيليجرام ====================
TELEGRAM_BOT_TOKEN ="8812727842:AAFvAH43kkDFzLG91VIkLgz4s6o7sUmWL7I"
TELEGRAM_CHAT_ID = "8297464896"

# إعدادات رأس المال والمخاطرة
INITIAL_CAPITAL = 200.0     # رأس المال المرجعي (USDT)
RISK_PERCENT = 0.01         # نسبة المخاطرة بكل صفقة (1%)
REWARD_RATIO = 3.0          # نسبة العائد للمخاطرة (1:3)
ATR_MULTIPLIER = 1.5        # معامل الوقف الديناميكي

# قائمة الأصول المستهدفة بالكامل
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 
    'XAU/USDT', 'ONDO/USDT', 'PENDLE/USDT', 'LINK/USDT', 'TAO/USDT'
]

# ==================== عميل بيانات بينانس المباشر (Spot & Futures) ====================
class BinanceDataClient:
    """عميل خفيف يفرق بين أسواق السبوت وعقود الذهب (Futures) لجلب الشموع بدقة"""
    @staticmethod
    def fetch_ohlcv(symbol, timeframe, limit=100):
        s = symbol.replace('/', '').upper()
        tf_map = {'1M': '1M', '1W': '1w', '1d': '1d', '4h': '4h'}
        tf = tf_map.get(timeframe, timeframe)
        
        # توجيه الذهب لعقود الفيوتشرز وباقي العملات للسبوت
        if s == 'XAUUSDT':
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={s}&interval={tf}&limit={limit}"
        else:
            url = f"https://api.binance.com/api/v3/klines?symbol={s}&interval={tf}&limit={limit}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        cleaned_data = []
        for c in data:
            cleaned_data.append([
                int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])
            ])
        return cleaned_data

# ==================== دوال الإرسال لتيليجرام ====================
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    for attempt in range(3):
        try:
            requests.post(url, json=payload, timeout=20)
            return
        except Exception as e:
            print(f"[-] تنبيه: فشل إرسال تيليجرام (محاولة {attempt+1}/3): {e}")
            time.sleep(3)

# ==================== بوابة الأخبار الاقتصادية ====================
def get_investing_economic_news():
    try:
        url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        today_str = datetime.now().strftime('%Y-%m-%d')
        payload = {
            "dateFrom": today_str, "dateTo": today_str,
            "timeZone": "55", "country[]": ["5", "72", "17", "43", "22", "37"]
        }
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return "محايد ⚖️", "• تعذر الاتصال ببوابة الأخبار."
            
        data = response.json()
        if isinstance(data, dict) and "data" in data and data['data']:
            soup = BeautifulSoup(data['data'], 'html.parser')
            rows = soup.find_all('tr', id=True)
            high_impact_events = 0
            news_summary = ""

            for row in rows:
                sentiment_td = row.find('td', {'class': 'sentiment'})
                if sentiment_td:
                    bulls = len(sentiment_td.find_all('i', {'class': 'grayFullBullishIcon'}))
                    if bulls >= 3:
                        high_impact_events += 1
                        event_title = row.find('td', {'class': 'event'}).text.strip() if row.find('td', {'class': 'event'}) else "خبر اقتصادي"
                        news_summary += f"• `{event_title}`\n"

            market_outlook = f"نشط 📊 ({high_impact_events} أحداث كبرى)" if high_impact_events > 0 else "محايد ⚖️"
            return market_outlook, news_summary if news_summary else "• لا توجد أخبار حرجة اليوم."
        return "محايد ⚖️", "• لا توجد بيانات مجدولة."
    except Exception as e:
        return "محايد ⚖️", "• تم التخطي: لا يمكن تحميل الأخبار."

# ==================== المحرك الخوارزمي الرياضي والمؤشرات ====================
def fetch_data(symbol, timeframe, limit=100):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            ohlcv = BinanceDataClient.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                print(f"[-] خطأ في جلب بيانات {symbol} فريم {timeframe}: {e}")
                return None

def calculate_advanced_indicators(df):
    """حساب المؤشرات الفنية باستخدام المتوسطات الأسية (EMA) ومعادلات ويلدر الأصلية"""
    # المتوسطات الأسية بدقة فائقة
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # مؤشر القوة النسبية RSI (تنعيم ويلدر)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = np.where(avg_loss == 0, 100, 100 - (100 / (1 + rs)))
    
    # متوسط المدى الحقيقي ATR (تنعيم ويلدر)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(alpha=1/14, adjust=False).mean()

    # مؤشر الزخم MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # حجم السيولة EMA للسيولة
    df['Volume_EMA20'] = df['volume'].ewm(span=20, adjust=False).mean()
    
    return df

# ==================== وحدة التحليل وإرسال التقارير ====================
def analyze_market():
    news_status, news_details = get_investing_economic_news()

    report = "📊 *تقرير النظام الاستراتيجي (EXCORA PRO)*\n" + "-"*32 + "\n"
    report += f"🌐 *الأخبار الكلية:* `{news_status}`\n" + "-"*32 + "\n"
    
    signals_to_send = []

    for symbol in SYMBOLS:
        df_monthly = fetch_data(symbol, '1M', 100)
        df_weekly  = fetch_data(symbol, '1W', 100)
        df_daily   = fetch_data(symbol, '1d', 100)
        df_4h      = fetch_data(symbol, '4h', 100)

        if any(df is None or df.empty for df in [df_monthly, df_weekly, df_daily, df_4h]):
            continue

        df_monthly = calculate_advanced_indicators(df_monthly)
        df_weekly  = calculate_advanced_indicators(df_weekly)
        df_daily   = calculate_advanced_indicators(df_daily)
        df_4h      = calculate_advanced_indicators(df_4h)

        c_mo = df_monthly.iloc[-1]
        c_we = df_weekly.iloc[-1]
        c_da = df_daily.iloc[-1]
        c_4h = df_4h.iloc[-1]

        # تقييم الهيكل العام عبر الـ EMA
        macro_bullish = (c_mo['close'] > c_mo['EMA50']) and (c_we['close'] > c_we['EMA50'])
        macro_bearish = (c_mo['close'] < c_mo['EMA50']) and (c_we['close'] < c_we['EMA50'])
        
        daily_bullish = c_da['close'] > c_da['EMA50']
        daily_bearish = c_da['close'] < c_da['EMA50']

        if macro_bullish and daily_bullish:
            trend_state = "BULLISH"
            status_emoji = "🟢 *(صاعد بقوة)*"
        elif macro_bearish and daily_bearish:
            trend_state = "BEARISH"
            status_emoji = "🔴 *(هابط بقوة)*"
        else:
            trend_state = "NEUTRAL"
            status_emoji = "🟡 *(متذبذب / تقاطع)*"

        report += f"🔹 *{symbol}* {status_emoji}\n"
        report += f"- يومي RSI: `{c_da['RSI']:.1f}` | 4س RSI: `{c_4h['RSI']:.1f}`\n\n"

        current_signal_state = None
        is_volume_confirmed = c_4h['volume'] > c_4h['Volume_EMA20']

        # شروط إشارات 4 ساعات
        if trend_state == "BULLISH":
            if (c_4h['close'] > c_4h['EMA50'] and 40 < c_4h['RSI'] < 60 and 
                c_4h['MACD'] > c_4h['MACD_Signal'] and is_volume_confirmed):
                current_signal_state = "LONG"
        elif trend_state == "BEARISH":
            if (c_4h['close'] < c_4h['EMA50'] and 40 < c_4h['RSI'] < 60 and 
                c_4h['MACD'] < c_4h['MACD_Signal'] and is_volume_confirmed):
                current_signal_state = "SHORT"

        # حسابات إدارة المخاطر الدقيقة
        if current_signal_state is not None:
            entry_price = float(c_4h['close'])
            current_atr = float(c_4h['ATR'])
            if pd.isna(current_atr) or current_atr <= 0:
                current_atr = entry_price * 0.015

            risk_amount = INITIAL_CAPITAL * RISK_PERCENT
            
            if current_signal_state == "LONG":
                stop_loss = entry_price - (current_atr * ATR_MULTIPLIER)
                take_profit = entry_price + ((entry_price - stop_loss) * REWARD_RATIO)
                sl_distance = entry_price - stop_loss
            else:
                stop_loss = entry_price + (current_atr * ATR_MULTIPLIER)
                take_profit = entry_price - ((stop_loss - entry_price) * REWARD_RATIO)
                sl_distance = stop_loss - entry_price

            position_size = risk_amount / sl_distance if sl_distance > 0 else 0

            signals_to_send.append(
                f"🚨 *إشارة {current_signal_state} خوارزمية مؤكدة* {'🟢' if current_signal_state == 'LONG' else '🔴'}\n"
                f"🪙 الأصل: `{symbol}`\n"
                f"⏱️ الفريم: `4 ساعات (تأكيد كلي)`\n"
                f"📈 الدخول: `{entry_price:.4f}`\n"
                f"🛑 وقف الخسارة: `{stop_loss:.4f}`\n"
                f"🎯 الهدف: `{take_profit:.4f}` (1:{int(REWARD_RATIO)})\n"
                f"⚖️ الكمية المقترحة: `{position_size:.4f} {symbol.split('/')[0]}`\n"
                f"💡 الخسارة المقدرة: `~{risk_amount:.2f} USDT`"
            )

    send_telegram_message(report)
    for sig in signals_to_send:
        send_telegram_message(sig)

# ==================== حلقة التشغيل الرئيسية ====================
if __name__ == "__main__":
    startup_msg = (
        "🤖 *تم تفعيل محرك EXCORA PRO* 🚀\n"
        "• الاتصال: `Binance REST API` (نظيف وبدون أخطاء)\n"
        "• دورة التحديث: `كل 120 ثانية`\n"
        "• المؤشرات: `EMA 50/200 & Wilder RSI/ATR`"
    )
    print(startup_msg)
    send_telegram_message(startup_msg)
    
    while True:
        try:
            print(f"[*] يتم الآن معالجة الأسواق والسيولة... {datetime.now().strftime('%H:%M:%S')}")
            analyze_market()
            time.sleep(120)  # الفحص كل 120 ثانية
        except Exception as e:
            print(f"[-] خطأ غير متوقع في الحلقة الرئيسية: {e}")
            time.sleep(60)
