import os
import ccxt
import pandas as pd
import numpy as np
import requests
import time
import hmac
import hashlib
import socket
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

# تحميل المفاتيح والأسرار من ملف .env الخارجي بأمان تام
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# ==================== إعدادات النظام الاستثماري الرياضي وإدارة المخاطر ====================
INITIAL_CAPITAL = 100.0        # رأس المال المرجعي الاستثماري للحساب (USDT)
RISK_PERCENT = 0.02             # نسبة المخاطرة المحافظة لكل صفقة استثمارية (2%)
REWARD_RATIO = 3.5              # نسبة عائد إلى مخاطرة عالية الاستثمارية (1:3.5)
ATR_MULTIPLIER = 2.5            # معامل ضرب ATR واسع للوقف الفريمات الكبيرة
BREAKEVEN_TRIGGER_PCT = 30.0    # تفعيل التأمين التلقائي عند ربح 30% للمراكز الطويلة
LEVERAGE = 3                    # رافعة مالية استثمارية منخفضة وآمنة للمدى الطويل

# إحصائيات الأداء التراكمي الاستثماري للمحفظة
total_realized_pnl = 0.0
winning_trades_count = 0
losing_trades_count = 0

# قائمة الأصول الاستثمارية المستهدفة
SYMBOLS = [
    # العملات الرقمية الكبرى
    'BTC/USDT',    # بيتكوين
    'ETH/USDT',    # إيثريوم
    'XRP/USDT',    # ريبل
    'SOL/USDT',    # سولانا
    'BNB/USDT',    # بينانس كوين
    'TRX/USDT',    # ترون
    
    # العملات الرقمية والتمويل اللامركزي (DeFi) والذكاء الاصطناعي
    'ADA/USDT',    # كاردانو
    'DOGE/USDT',   # دوجكوين
    'LINK/USDT',   # تشينلينك
    'LTC/USDT',    # لايتكوين
    'HBAR/USDT',   # هيديرا
    'ONDO/USDT',   # أوندو
    'TAO/USDT',    # بيتاو / تينسور
    'PENDLE/USDT', # بندل
    'RENDER/USDT', # ريندر
    
    # المعادن الثمينة (السلع)
    'XAU/USDT',    # الذهب
    'XAG/USDT',    # الفضة
    
    # الأسهم الأمريكية
    'TSLA/USDT',   # تسلا
    'AAPL/USDT',   # آبل
    'NVDA/USDT',   # إنفيديا
]






# إعداد اتصال بينانس الاحترافي الآمن للعقود الآجلة
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

# متغيرات التتبع الرياضية والداخلية
_previous_active_symbols = set()
secured_trades = set()

# ==================== دوال الإرسال لتيليجرام ====================
def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[-] خطأ في إرسال تيليجرام: {e}")

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

# ==================== إدارة المراكز عبر HMAC ====================
def get_binance_positions():
    endpoint = "/fapi/v3/positionRisk"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            timestamp = int(time.time() * 1000)
            params = {"timestamp": timestamp, "recvWindow": 60000}
            query_string = urlencode(params)
            signature = hmac.new(
                BINANCE_SECRET_KEY.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            url = f"https://fapi.binance.com{endpoint}?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                time.sleep(2)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                return []
    return []

def has_open_position(symbol):
    try:
        positions = get_binance_positions()
        clean_symbol = symbol.replace('/', '')
        for pos in positions:
            if pos.get('symbol', '') == clean_symbol and float(pos.get('positionAmt', 0)) != 0:
                return True
        return False
    except Exception as e:
        print(f"[-] خطأ في فحص المراكز لـ {symbol}: {e}")
        return False

# ==================== خوارزمية Volume Profile الرياضية الاستثمارية (بدون استبعاد) ====================
def calculate_true_volume_profile(df, bins=100):
    try:
        if df is None or len(df) == 0:
            return None, None, None, [], []

        price_min = df['low'].min()
        price_max = df['high'].max()
        if price_min == price_max:
            return price_min, price_max, price_min, [], []

        bin_edges = np.linspace(price_min, price_max, bins + 1)
        bin_volumes = np.zeros(bins)

        for _, row in df.iterrows():
            h = row['high']
            l = row['low']
            v = row['volume']
            
            if h == l or v <= 0:
                continue

            for i in range(bins):
                b_lower = bin_edges[i]
                b_upper = bin_edges[i+1]

                overlap_low = max(l, b_lower)
                overlap_high = min(h, b_upper)

                if overlap_high > overlap_low:
                    overlap_fraction = (overlap_high - overlap_low) / (h - l)
                    bin_volumes[i] += v * overlap_fraction

        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        poc_idx = np.argmax(bin_volumes)
        poc = bin_centers[poc_idx]

        total_vol = np.sum(bin_volumes)
        if total_vol == 0:
            return poc, price_max, price_min, [], []

        sorted_indices = np.argsort(bin_volumes)[::-1]
        cumulative_vol = 0
        va_indices = []
        for idx in sorted_indices:
            cumulative_vol += bin_volumes[idx]
            va_indices.append(idx)
            if cumulative_vol >= total_vol * 0.70:
                break
        
        va_prices = [bin_centers[i] for i in va_indices]
        val = min(va_prices) if va_prices else price_min
        vah = max(va_prices) if va_prices else price_max

        mean_vol = np.mean(bin_volumes)
        std_vol = np.std(bin_volumes)
        hvn_threshold = mean_vol + (0.5 * std_vol)
        
        hvn = [bin_centers[i] for i, v in enumerate(bin_volumes) if v > hvn_threshold]
        lvn = [bin_centers[i] for i, v in enumerate(bin_volumes) if v < mean_vol * 0.5]

        return float(poc), float(vah), float(val), hvn, lvn
    except Exception as e:
        print(f"[-] خطأ في حساب Volume Profile: {e}")
        return None, None, None, [], []

def is_near_hvn(current_price, hvn_list, tolerance_pct=0.008):
    if not hvn_list:
        return False
    for hvn_level in hvn_list:
        if abs(current_price - hvn_level) / current_price <= tolerance_pct:
            return True
    return False

# ==================== كشف مناطق الأوردر بلوك الإستثمارية ====================
def detect_order_blocks(df):
    bullish_ob_retest, bearish_ob_retest = False, False
    b_ob_low, b_ob_high = 0.0, 0.0
    r_ob_low, r_ob_high = 0.0, 0.0

    try:
        if len(df) >= 5:
            for i in range(len(df) - 3, 2, -1):
                if df['close'].iloc[i] < df['open'].iloc[i]:
                    body_size_next = df['close'].iloc[i+1] - df['open'].iloc[i+1]
                    if df['close'].iloc[i+1] > df['open'].iloc[i+1] and body_size_next > (df['ATR'].iloc[i+1] * 1.0):
                        b_ob_low = float(df['low'].iloc[i])
                        b_ob_high = float(df['high'].iloc[i])
                        current_close = df['close'].iloc[-1]
                        current_low = df['low'].iloc[-1]
                        if b_ob_low <= current_close <= b_ob_high or (current_low <= b_ob_high and current_close >= b_ob_low):
                            bullish_ob_retest = True
                            break

            for i in range(len(df) - 3, 2, -1):
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    body_size_next = df['open'].iloc[i+1] - df['close'].iloc[i+1]
                    if df['close'].iloc[i+1] < df['open'].iloc[i+1] and body_size_next > (df['ATR'].iloc[i+1] * 1.0):
                        r_ob_low = float(df['low'].iloc[i])
                        r_ob_high = float(df['high'].iloc[i])
                        current_close = df['close'].iloc[-1]
                        current_high = df['high'].iloc[-1]
                        if r_ob_low <= current_close <= r_ob_high or (current_high >= r_ob_low and current_close <= r_ob_high):
                            bearish_ob_retest = True
                            break
    except Exception as e:
        print(f"[-] خطأ في حساب الأوردر بلوك: {e}")

    return bullish_ob_retest, b_ob_low, b_ob_high, bearish_ob_retest, r_ob_low, r_ob_high

# ==================== كشف فجوات القيمة العادلة الإستثمارية (FVG) ====================
def detect_fair_value_gaps_with_retest(df):
    bullish_fvg_retest, bearish_fvg_retest = False, False
    fvg_zone = (0.0, 0.0)
    try:
        if len(df) >= 4:
            if df['low'].iloc[-2] > df['high'].iloc[-4]:
                fvg_low = df['high'].iloc[-4]
                fvg_high = df['low'].iloc[-2]
                fvg_zone = (fvg_low, fvg_high)
                if fvg_low <= df['close'].iloc[-1] <= fvg_high or (df['low'].iloc[-1] <= fvg_high and df['close'].iloc[-1] > fvg_low):
                    bullish_fvg_retest = True

            if df['high'].iloc[-2] < df['low'].iloc[-4]:
                fvg_high = df['low'].iloc[-4]
                fvg_low = df['high'].iloc[-2]
                fvg_zone = (fvg_low, fvg_high)
                if fvg_low <= df['close'].iloc[-1] <= fvg_high or (df['high'].iloc[-1] >= fvg_low and df['close'].iloc[-1] < fvg_high):
                    bearish_fvg_retest = True
    except Exception:
        pass
    return bullish_fvg_retest, bearish_fvg_retest, fvg_zone

# ==================== هيكل السوق الإستثماري (BOS + Retest) ====================
def analyze_market_structure_with_retest(df, window=5):
    try:
        df['swing_high'] = df['high'][(df['high'] == df['high'].rolling(window*2+1, center=True).max())]
        df['swing_low'] = df['low'][(df['low'] == df['low'].rolling(window*2+1, center=True).min())]

        recent_swing_highs = df['swing_high'].dropna()
        recent_swing_lows = df['swing_low'].dropna()

        resistance = recent_swing_highs.iloc[-1] if not recent_swing_highs.empty else df['high'].max()
        support = recent_swing_lows.iloc[-1] if not recent_swing_lows.empty else df['low'].min()

        bos_bullish_retest, bos_bearish_retest = False, False
        
        if len(recent_swing_highs) >= 2 and len(recent_swing_lows) >= 2:
            broken_resistance = recent_swing_highs.iloc[-2]
            broken_support = recent_swing_lows.iloc[-2]
            
            if df['close'].iloc[-2] > broken_resistance and abs(df['low'].iloc[-1] - broken_resistance) <= (df['close'].iloc[-1] * 0.005):
                bos_bullish_retest = True
            elif df['close'].iloc[-1] > broken_resistance and df['close'].iloc[-2] > broken_resistance:
                bos_bullish_retest = True

            if df['close'].iloc[-2] < broken_support and abs(df['high'].iloc[-1] - broken_support) <= (df['close'].iloc[-1] * 0.005):
                bos_bearish_retest = True
            elif df['close'].iloc[-1] < broken_support and df['close'].iloc[-2] < broken_support:
                bos_bearish_retest = True

        return support, resistance, bos_bullish_retest, bos_bearish_retest
    except Exception:
        return df['low'].min(), df['high'].max(), False, False

# ==================== الشموع الانعكاسية الاستثمارية ====================
def detect_reversal_candles(df):
    try:
        c_curr = df.iloc[-1]
        c_prev = df.iloc[-2]

        is_bullish_engulfing = (c_prev['close'] < c_prev['open']) and \
                              (c_curr['close'] > c_curr['open']) and \
                              (c_curr['close'] >= c_prev['open']) and \
                              (c_curr['open'] <= c_prev['close'])

        is_bearish_engulfing = (c_prev['close'] > c_prev['open']) and \
                              (c_curr['close'] < c_curr['open']) and \
                              (c_curr['close'] <= c_prev['open']) and \
                              (c_curr['open'] >= c_prev['close'])

        return is_bullish_engulfing, is_bearish_engulfing
    except Exception:
        return False, False

# ==================== حساب المؤشرات الفنية الاستثمارية ====================
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
    true_range = ranges.max(axis=1)
    df['ATR'] = true_range.rolling(window=14).mean()

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Volume_EMA20'] = df['volume'].ewm(span=20, adjust=False).mean()

    return df

def fetch_market_data(symbol, timeframe, limit=100):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            ohlcv = binance_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                print(f"[-] خطأ في جلب بيانات {symbol}: {e}")
                return None

# ==================== محرك التنفيذ الاستثماري الآلي ====================
def execute_algorithmic_order(symbol, side, raw_position_size, entry_price):
    try:
        try:
            binance_exchange.set_leverage(LEVERAGE, symbol)
        except Exception:
            pass 

        markets = binance_exchange.load_markets()
        if symbol == 'XAU/USDT' and 'XAU/USDT:USDT' in markets:
            symbol = 'XAU/USDT:USDT'

        if symbol not in markets:
            return f"❌ الرمز {symbol} غير مدعوم."

        market = markets[symbol]
        raw_amount = raw_position_size / entry_price
        formatted_amount_str = binance_exchange.amount_to_precision(symbol, raw_amount)
        final_amount = float(formatted_amount_str)

        min_amount = float(market.get('limits', {}).get('amount', {}).get('min') or 0.0)
        min_cost = float(market.get('limits', {}).get('cost', {}).get('min') or 10.0)

        if final_amount < min_amount or (final_amount * entry_price) < min_cost:
            return f"❌ الكمية أقل من الحد الأدنى الاستثماري لـ {symbol}"

        order_side = 'buy' if side == 'LONG' else 'sell'
        order = binance_exchange.create_order(
            symbol=symbol,
            type='market',
            side=order_side,
            amount=final_amount
        )

        return f"✅ التنفيذ الاستثماري ناجح | ID: {order.get('id', 'N/A')} | الكمية: {final_amount}"
    except Exception as e:
        print(f"[-] خطأ أثناء تنفيذ صفقة {symbol}: {e}")
        return f"❌ فشل التنفيذ: {str(e)}"

# ==================== مراقبة الصفقات الاستثمارية وإدارة الأداء ====================
def monitor_active_trades():
    global _previous_active_symbols, secured_trades
    global total_realized_pnl, winning_trades_count, losing_trades_count, LEVERAGE
    
    try:
        positions = get_binance_positions()
        active_reports = []
        current_active_symbols = set()

        for pos in positions:
            position_amt = float(pos.get('positionAmt', 0))
            if position_amt != 0:
                raw_symbol = pos.get('symbol', '')
                symbol = raw_symbol[:-4] + '/' + raw_symbol[-4:] if len(raw_symbol) >= 7 else raw_symbol
                current_active_symbols.add(symbol)

                entry_price = float(pos.get('entryPrice', 0))
                unrealized_pnl = float(pos.get('unRealizedProfit', 0))
                initial_margin = (abs(position_amt) * entry_price) / LEVERAGE  
                pnl_percentage = (unrealized_pnl / initial_margin) * 100 if initial_margin > 0 else 0.0
                side = 'LONG' if position_amt > 0 else 'SHORT'

                if pnl_percentage >= BREAKEVEN_TRIGGER_PCT and symbol not in secured_trades:
                    secured_trades.add(symbol)
                    send_telegram_message(
                        f"🛡️ *تأمين الصفقة الاستثمارية (Breakeven Triggered)*\n"
                        f"🪙 الأصل: `{symbol}` | الاتجاه: `{side}`\n"
                        f"📈 الربح الاستثماري بلغ `{pnl_percentage:.2f}%` وتم رصد التأمين بنجاح."
                    )

                status_icon = "🟢" if pnl_percentage >= 0 else "🔴"
                active_reports.append(
                    f"{status_icon} *{symbol}* | الاتجاه: `{side}` | PnL: `{pnl_percentage:.2f}%`"
                )

        closed_symbols = _previous_active_symbols - current_active_symbols
        for symbol in closed_symbols:
            if symbol in secured_trades:
                secured_trades.remove(symbol)
            try:
                time.sleep(2) 
                income_history = binance_exchange.fapiPrivateGetIncome({'symbol': symbol.replace('/', ''), 'limit': 5})
                realized_pnl = sum([float(item.get('income', 0.0)) for item in income_history if item.get('incomeType') == 'REALIZED_PNL'])
                
                total_realized_pnl += realized_pnl
                if realized_pnl > 0:
                    winning_trades_count += 1
                    closure_type = f"🟢 ربح استثماري محقق (+{realized_pnl:.2f} USDT)"
                else:
                    losing_trades_count += 1
                    closure_type = f"🔴 خسارة استثمارية ({realized_pnl:.2f} USDT)"

                total_trades = winning_trades_count + losing_trades_count
                win_rate = (winning_trades_count / total_trades * 100) if total_trades > 0 else 0.0

                send_telegram_message(
                    f"🔔 *إغلاق صفقة استثمارية وتحديث الأداء*\n"
                    f"🪙 الأصل: `{symbol}`\n"
                    f"📌 النتيجة: {closure_type}\n"
                    f"-----------------------------------\n"
                    f"📊 *الإحصائيات الاستثمارية التراكمية:*\n"
                    f"✅ الصفقات الرابحة: `{winning_trades_count}`\n"
                    f"❌ الصفقات الخاسرة: `{losing_trades_count}`\n"
                    f"🎯 نسبة النجاح (Win Rate): `{win_rate:.1f}%`\n"
                    f"💰 الربح التراكمي الإجمالي: `{total_realized_pnl:.2f} USDT`"
                )
            except Exception:
                pass

        _previous_active_symbols = current_active_symbols
        if active_reports:
            send_telegram_message("📈 *تقرير أداء المحفظة الاستثمارية المباشر*\n" + "\n".join(active_reports))
            
    except Exception as e:
        print(f"[-] خطأ في تتبع الصفقات الاستثمارية: {e}")

# ==================== خوارزمية التحليل الاستثماري الشامل (1M / 1W / 1D) ====================
def run_algorithmic_market_analysis():
    signals_to_send = []
    report = "📊 *التقرير الرياضي الاستثماري الشامل (EXCORA Smart Money + VP - 1M/1W/1D)*\n" + "-"*35 + "\n"

    for symbol in SYMBOLS:
        if has_open_position(symbol):
            report += f"🔹 *{symbol}* 🔒 *(موقف استثماري مفتوح)*\n\n"
            continue

        # جلب بيانات الفريمات الاستثمارية: 1 شهر، 1 أسبوع، 1 يوم
        df_1m = fetch_market_data(symbol, '1M')
        df_1w = fetch_market_data(symbol, '1w')
        df_1d = fetch_market_data(symbol, '1d')

        if df_1m is None or df_1w is None or df_1d is None:
            continue

        df_1m = calculate_mathematical_indicators(df_1m)
        df_1w = calculate_mathematical_indicators(df_1w)
        df_1d = calculate_mathematical_indicators(df_1d)

        c_1m = df_1m.iloc[-1]
        c_1w = df_1w.iloc[-1]
        c_1d = df_1d.iloc[-1]

        # 1. الاتجاه العام الاستثماري طويل الأجل
        trend_1m = "BULLISH" if c_1m['close'] > c_1m['EMA50'] else "BEARISH"
        confirm_1w_trend = "BULLISH" if c_1w['close'] > c_1w['EMA50'] else "BEARISH"

        # 2. الهيكل، الأوردر بلوك، FVG و Volume Profile على الفريم الأسبوعي (1W)
        support, resistance, bos_bullish_retest, bos_bearish_retest = analyze_market_structure_with_retest(df_1w)
        bull_fvg_retest, bear_fvg_retest, fvg_zone = detect_fair_value_gaps_with_retest(df_1w)
        bull_ob_retest, b_low, b_high, bear_ob_retest, r_low, r_high = detect_order_blocks(df_1w)

        poc, vah, val, hvn, lvn = calculate_true_volume_profile(df_1w, bins=100)
        price_near_hvn = is_near_hvn(c_1d['close'], hvn, tolerance_pct=0.01)

        # 3. تحديد مناطق الدخول الاستثمارية بعيدة المدى
        optimal_entry_zone_min = min(b_low if b_low > 0 else c_1d['close'], fvg_zone[0] if fvg_zone[0] > 0 else c_1d['close'])
        optimal_entry_zone_max = max(b_high if b_high > 0 else c_1d['close'], fvg_zone[1] if fvg_zone[1] > 0 else c_1d['close'])

        bull_engulfing, bear_engulfing = detect_reversal_candles(df_1d)
        is_volume_confirmed = c_1d['volume'] > c_1d['Volume_EMA20']

        status_emoji = "🟢 (صاعد استثمارياً)" if (trend_1m == "BULLISH" and confirm_1w_trend == "BULLISH") else ("🔴 (هابط استثمارياً)" if (trend_1m == "BEARISH" and confirm_1w_trend == "BEARISH") else "🟡 (تذبذب استثماري)")

        report += f"🔹 *{symbol}* {status_emoji}\n" \
                  f"   - الاتجاه: `1شهر: {trend_1m} | 1أسبوع: {confirm_1w_trend}`\n" \
                  f"   - 🎯 *منطقة التجميع والدخول (Zone):* `{optimal_entry_zone_min:.2f}` ⟷ `{optimal_entry_zone_max:.2f}`\n" \
                  f"   - VP POC: `{poc if poc else 0:.2f}` | تطابق HVN: `{'✅ متوفر' if price_near_hvn else '❌ غير متوفر'}`\n\n"

        current_signal_state = None

        if trend_1m == "BULLISH" and confirm_1w_trend == "BULLISH":
            if (bull_ob_retest or bos_bullish_retest or bull_fvg_retest) and price_near_hvn and (bull_engulfing or 35 < c_1d['RSI'] < 65) and is_volume_confirmed:
                current_signal_state = "LONG"

        elif trend_1m == "BEARISH" and confirm_1w_trend == "BEARISH":
            if (bear_ob_retest or bos_bearish_retest or bear_fvg_retest) and price_near_hvn and (bear_engulfing or 35 < c_1d['RSI'] < 65) and is_volume_confirmed:
                current_signal_state = "SHORT"

        if current_signal_state is not None:
            entry_price = c_1d['close']
            risk_amount = INITIAL_CAPITAL * RISK_PERCENT
            current_atr = c_1d['ATR']

            if pd.isna(current_atr) or current_atr <= 0:
                current_atr = entry_price * 0.02

            if current_signal_state == "LONG":
                stop_loss = entry_price - (current_atr * ATR_MULTIPLIER)
                take_profit = entry_price + ((entry_price - stop_loss) * REWARD_RATIO)
                position_size = (risk_amount / (entry_price - stop_loss)) * entry_price
                exec_res = execute_algorithmic_order(symbol, "LONG", position_size, entry_price)

                signals_to_send.append(
                    f"🚨 *إشارة دخول استثمارية شراء (LONG - 1M/1W)* 🟢\n"
                    f"🪙 الأصل: `{symbol}`\n"
                    f"📍 *منطقة التجميع الموصى بها:* `{optimal_entry_zone_min:.2f} - {optimal_entry_zone_max:.2f}`\n"
                    f"📈 السعر الحالي: `{entry_price}`\n"
                    f"🛑 وقف الخسارة الاستثماري: `{stop_loss:.4f}`\n"
                    f"🎯 الهدف الاستثماري: `{take_profit:.4f}`\n"
                    f"⚡ التنفيذ: {exec_res}"
                )

            elif current_signal_state == "SHORT":
                stop_loss = entry_price + (current_atr * ATR_MULTIPLIER)
                take_profit = entry_price - ((stop_loss - entry_price) * REWARD_RATIO)
                position_size = (risk_amount / (stop_loss - entry_price)) * entry_price
                exec_res = execute_algorithmic_order(symbol, "SHORT", position_size, entry_price)

                signals_to_send.append(
                    f"🚨 *إشارة دخول استثمارية بيع (SHORT - 1M/1W)* 🔴\n"
                    f"🪙 الأصل: `{symbol}`\n"
                    f"📍 *منطقة البيع الاستثماري الموصى بها:* `{optimal_entry_zone_min:.2f} - {optimal_entry_zone_max:.2f}`\n"
                    f"📉 السعر الحالي: `{entry_price}`\n"
                    f"🛑 وقف الخسارة الاستثماري: `{stop_loss:.4f}`\n"
                    f"🎯 الهدف الاستثماري: `{take_profit:.4f}`\n"
                    f"⚡ التنفيذ: {exec_res}"
                )

    send_telegram_message(report)
    for sig in signals_to_send:
        send_telegram_message(sig)

# ==================== حلقة التشغيل الرئيسية والاستثمارية ====================
if __name__ == "__main__":
    send_telegram_message("🤖 *تم تفعيل محرك EXCORA الاستثماري طويل الأجل (1M / 1W / 1D) بنجاح واحترافية تامة.*")

    while True:
        try:
            if not check_internet_connection():
                print(f"[-] انقطاع الاتصال... إعادة محاولة... {datetime.now()}")
                time.sleep(15)
                continue

            print(f"[*] بدء دورة التحليل الاستثماري طويل الأجل... {datetime.now()}")
            run_algorithmic_market_analysis()
            monitor_active_trades()

            time.sleep(3600) # التكرار كل ساعة بما يتناسب مع الفريمات الكبيرة (شهرية وأسبوعية)
        except Exception as e:
            print(f"[-] خطأ حرج في الحلقة الرئيسية الاستثمارية: {e}")
            time.sleep(120)
