import requests
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ChatJoinRequestHandler,
)

# ================= CONFIG =================

TOKEN = "8284715892:AAH3AxEnYp6nVEzDF-AmIXYGNBZuGFBEAy0"
CHANNEL_ID = -1003742118245
ADMIN_ID = 5072932186

# ========= GOLDAPI SETTINGS =========

GOLDAPI_KEY = "goldapi-152a3asmlmlc131-io"
GOLDAPI_URL = "https://www.goldapi.io/api/XAU/USD"

active_trade = None
current_task = None

# ================= GET GOLD PRICE =================

def get_gold_price():
    try:
        headers = {"x-access-token": GOLDAPI_KEY}
        r = requests.get(GOLDAPI_URL, headers=headers, timeout=10)
        data = r.json()

        if "price" in data:
            return float(data["price"])
        else:
            print("GoldAPI Response:", data)
            return None
    except Exception as e:
        print("Price Fetch Error:", e)
        return None

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    start_text = """
<b>WELCOME TO GOLD SIGNAL VAULT</b>

<b>Free XAUUSD signals are provided for traders connected through our official broker link.</b>

<b>To continue receiving full trade setups and updates:</b>

<b>1️⃣ Open your trading account using the official link below</b>
<b>2️⃣ Send your Trading ID for verification</b>
<b>3️⃣ Get continued access & future upgrades</b>

<b>🖥 https://brokeraccountguide.com ☝</b>

<b>Only verified broker-connected traders will receive long-term access.</b>
<b>This is a restricted-access channel.</b>
<b>Unverified or inactive users may be removed without notice.</b>

<b>Trade smart. Protect capital first.</b>
"""

    await update.message.reply_text(start_text, parse_mode="HTML")

# ================= PRICE COMMAND =================

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = get_gold_price()
    if p:
        await update.message.reply_text(
            f"<b>💰 XAU/USD Live Price: {p}</b>",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "<b>❌ Price fetch error</b>",
            parse_mode="HTML"
        )

# ================= JOIN REQUEST AUTO APPROVE =================

async def approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=update.chat_join_request.from_user.id,
        )
    except:
        pass

# ================= SIGNAL HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_trade, current_task

    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text.lower()

    if "buy" in text:
        trade_type = "BUY"
    elif "sell" in text:
        trade_type = "SELL"
    else:
        return

    # Stop previous trade if running
    if active_trade:
        active_trade = None
        if current_task:
            current_task.cancel()

    p = get_gold_price()

    if not p:
        await update.message.reply_text(
            "<b>❌ Price fetch error</b>",
            parse_mode="HTML"
        )
        return

    entry = round(p, 2)

    if trade_type == "BUY":
        tp1 = round(entry + 5, 2)
        tp2 = round(entry + 10, 2)
        sl = round(entry - 10, 2)
    else:
        tp1 = round(entry - 5, 2)
        tp2 = round(entry - 10, 2)
        sl = round(entry + 10, 2)

    active_trade = {
        "type": trade_type,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "sl": sl,
        "last_price": entry,
        "tp1_hit": False,
    }

    signal_text = f"""
<b>XAUUSD {trade_type} {entry}</b>

<b>TP {tp1}</b>
<b>TP {tp2}</b>

<b>SL {sl}</b>
"""

    msg = await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=signal_text,
        parse_mode="HTML",
    )

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text="<b>⚠️ Use lot size according to your account equity</b>",
        reply_to_message_id=msg.message_id,
        parse_mode="HTML",
    )

    current_task = asyncio.create_task(track_trade(context, msg.message_id))

# ================= TRADE TRACKER =================

async def track_trade(context, reply_id):
    global active_trade

    try:
        while active_trade:
            await asyncio.sleep(5)

            p = get_gold_price()
            if not p:
                continue

            price = round(p, 2)

            # BUY
            if active_trade["type"] == "BUY":

                if price >= active_trade["last_price"] + 1:
                    active_trade["last_price"] = price
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"<b>XAUUSD trade active ✅ Price {price}</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )

                if price >= active_trade["tp1"] and not active_trade["tp1_hit"]:
                    active_trade["tp1_hit"] = True
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text="<b>XAUUSD TP1 hit successful 👑</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )

                if price >= active_trade["tp2"]:
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text="<b>XAUUSD TP2 hit successful 👑</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )
                    active_trade = None
                    break

                if price <= active_trade["sl"]:
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text="<b>Stop loss hit ❌</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )
                    active_trade = None
                    break

            # SELL
            else:

                if price <= active_trade["last_price"] - 1:
                    active_trade["last_price"] = price
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"<b>XAUUSD trade active ✅ Price {price}</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )

                if price <= active_trade["tp1"] and not active_trade["tp1_hit"]:
                    active_trade["tp1_hit"] = True
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text="<b>XAUUSD TP1 hit successful 👑</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )

                if price <= active_trade["tp2"]:
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text="<b>XAUUSD TP2 hit successful 👑</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )
                    active_trade = None
                    break

                if price >= active_trade["sl"]:
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text="<b>Stop loss hit ❌</b>",
                        reply_to_message_id=reply_id,
                        parse_mode="HTML",
                    )
                    active_trade = None
                    break

    except:
        pass

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(ChatJoinRequestHandler(approve_join))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
