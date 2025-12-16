import os
import json
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ===== CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
WATCH_FILE = "watchlist.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ===== FB CHECK =====
def check_facebook(url: str) -> str:
    try:
        if not url.startswith("http"):
            url = "https://www.facebook.com/" + url

        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            t = r.text.lower()
            if "sorry, this page isn't available" in t:
                return "DIE ❌"
            if "log in" in t:
                return "RESTRICTED ⚠️"
            return "LIVE ✅"

        if r.status_code in [404, 410]:
            return "DIE ❌"

        return "UNKNOWN ⚠️"
    except:
        return "ERROR ⚠️"

# ===== WATCH STORAGE =====
def load_watchlist():
    if not os.path.exists(WATCH_FILE):
        return {}
    with open(WATCH_FILE, "r") as f:
        return json.load(f)

def save_watchlist(data):
    with open(WATCH_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ===== BOT COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 FB Checker Bot\n\n"
        "/watch <link|uid> – Theo dõi FB DIE\n"
        "Gửi link bất kỳ để check LIVE / DIE"
    )

async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Dùng: /watch <link hoặc UID>")
        return

    url = context.args[0]
    chat_id = str(update.message.chat_id)

    data = load_watchlist()
    status = check_facebook(url)

    data[url] = {
        "chat_id": chat_id,
        "last_status": status
    }

    save_watchlist(data)

    await update.message.reply_text(
        f"👀 Đã theo dõi:\n{url}\nTrạng thái hiện tại: {status}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = update.message.text.splitlines()
    result = []

    for line in lines:
        status = check_facebook(line.strip())
        result.append(f"{line.strip()} → {status}")

    await update.message.reply_text("\n".join(result))

# ===== AUTO MONITOR =====
async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    data = load_watchlist()

    for url, info in data.items():
        old_status = info["last_status"]
        new_status = check_facebook(url)

        if old_status.startswith("DIE") and new_status.startswith("LIVE"):
            await context.bot.send_message(
                chat_id=info["chat_id"],
                text=(
                    "🚨 FB ĐÃ SỐNG LẠI!\n\n"
                    f"{url}\n"
                    f"Trạng thái: {new_status}"
                )
            )

        data[url]["last_status"] = new_status

    save_watchlist(data)

# ===== MAIN =====
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("watch", watch))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # check mỗi 5 phút
    app.job_queue.run_repeating(monitor_job, interval=300, first=60)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=os.getenv("WEBHOOK_URL")
    )

if __name__ == "__main__":
    main()
