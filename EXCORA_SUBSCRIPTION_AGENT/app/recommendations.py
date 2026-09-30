def build_recommendation(
    symbol,
    direction,
    entry_low,
    entry_high,
    stop_loss,
    take_profit_1,
    take_profit_2,
    timeframe,
    confirmations
):

    confirmation_text = "\n".join(
        f"✓ {item}" for item in confirmations
    )

    return f"""
🚨 EXCORA PRO RECOMMENDATION

🪙 {symbol}

📊 الاتجاه:
{direction}

⏱ الإطار:
{timeframe}

📍 منطقة الدخول:
{entry_low} - {entry_high}

🛑 Stop Loss:
{stop_loss}

🎯 Take Profit 1:
{take_profit_1}

🎯 Take Profit 2:
{take_profit_2}

🔎 التأكيدات:
{confirmation_text}

⚠️ توصية تحليلية فقط.
لا يتم تنفيذ أي صفقة تلقائياً.
"""
