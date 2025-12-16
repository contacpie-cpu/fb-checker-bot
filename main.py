from server import keep_alive
keep_alive()
import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = "PASTE_TELEGRAM_BOT_TOKEN_CUA_BAN_O_DAY"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

WATCH_LIST = {}  # chat_id -> set(urls)


def check_facebook(url: str):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; SM-A505F) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0 Mobile Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True,
        )
    except Exception:
        return "UNKNOWN ❓", "Request failed"

    text = r.text.lower()
    status = r.status_code
    length = len(text)

    if status in (404, 410) or "page isn’t available" in text:
        return "DIE_CONFIRMED ❌", "404 / Page unavailable"

    if "checkpoint" in text or "review the decision" in text:
        return "CHECKPOINT ⚠️", "Facebook checkpoint"

    if "this content isn’t available right now" in text:
        return "PRIVATE 🔒", "Privacy restriction"

    if "log in to facebook" in text or "login to continue" in text:
        return "LIVE_LIMITED ⚠️", "Login required"

    if length < 800:
        return "BLOCKED_IP ⚠️", "Blocked datacenter IP"

    return "LIVE_PUBLIC ✅", "Public access"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 FB Checker Bot đã hoạt động\n\n"
        "Lệnh sử dụng:\n"
        "/check <link_fb>\n"
        "/watch <link_fb>\n"
        "/list"
    )


async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Vui lòng nhập link Facebook")
        return

    url = context.args[0]
    status, reason = check_facebook(url)

    await update.message.reply_text(
        f"🔎 Kết quả kiểm tra\n"
        f"📄 Link: {url}\n"
        f"📌 Trạng thái: {status}\n"
        f"📝 Lý do: {reason}"
    )


async def watch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Vui lòng nhập link Facebook")
        return

    url = context.args[0]
    chat_id = update.effective_chat.id

    WATCH_LIST.setdefault(chat_id, set()).add(url)

    await update.message.reply_text(
        f"👀 Đã theo dõi:\n{url}\n\nBot sẽ tự kiểm tra định kỳ."
    )


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    urls = WATCH_LIST.get(chat_id)

    if not urls:
        await update.message.reply_text("📭 Chưa theo dõi link nào")
        return

    text = "📋 Danh sách đang theo dõi:\n"
    for u in urls:
        text += f"- {u}\n"

    await update.message.reply_text(text)


async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, urls in WATCH_LIST.items():
        for url in urls:
            status, reason = check_facebook(url)

            if status == "LIVE_PUBLIC ✅":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "🚨 FACEBOOK ĐÃ SỐNG LẠI\n\n"
                        f"📄 Link: {url}\n"
                        f"📌 Trạng thái: {status}\n"
                        f"📝 Lý do: {reason}"
                    ),
                )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("watch", watch_cmd))
    app.add_handler(CommandHandler("list", list_cmd))

    app.job_queue.run_repeating(
        monitor_job,
        interval=300,
        first=60,
    )

    app.run_polling()


if __name__ == "__main__":
    main()
