import os, json, random, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
CHANNEL_ID = os.getenv("CHANNEL_ID", "@go0dn")
API = f"https://api.telegram.org/bot{TOKEN}/"
TZ = ZoneInfo("Asia/Tehran")
DATA = Path("data")
STATE_FILE = DATA / "state.json"

BANK = {
    "morning": [
        "صبح، فرصتی دوباره برای دیدن زیبایی‌های کوچک و ساختن روزی روشن است. امروز را با مهربانی آغاز کنیم. 🌱\n\n#شب_خوش",
        "گاهی یک شروع آرام، از هزار تصمیم بزرگ ارزشمندتر است. روزت را با امید و نگاهی تازه آغاز کن. ☀️\n\n#شب_خوش",
        "جهان هر صبح صفحه‌ای سپید پیش رویمان می‌گذارد؛ بنویسیمش با واژه‌های خوب و رفتارهای مهربان. 🌿\n\n#شب_خوش",
    ],
    "night": [
        "شب که می‌رسد، صداها آرام می‌شوند و حرف‌های نگفته آهسته‌تر از همیشه شنیده می‌شوند. 🌙\n\n#شب_خوش",
        "بعضی واژه‌ها را نمی‌شود بلند گفت؛ باید در سکوت شب، میان دل و پنجره رهایشان کرد. ✨\n\n#شب_خوش",
        "امشب کمی مکث کن؛ شاید آرامش همین باشد که با خودت مهربان‌تر شوی. 🕊️\n\n#شب_خوش",
    ],
}

def api(method, payload):
    data = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(API + method, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        result = json.loads(r.read().decode())
    if not result.get("ok"):
        raise RuntimeError(result)
    return result["result"]

def load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"offset": 0, "posts": {}}

def save(state):
    DATA.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def send_admin(text, post_key):
    markup = {"inline_keyboard": [[
        {"text": "✅ تأیید", "callback_data": f"approve|{post_key}"},
        {"text": "❌ رد", "callback_data": f"reject|{post_key}"}
    ]]}
    api("sendMessage", {"chat_id": ADMIN_ID, "text": text, "reply_markup": markup})

def make_draft(state, slot, target_day):
    key = f"{target_day.isoformat()}:{slot}"
    if key in state["posts"]:
        return
    text = random.choice(BANK[slot])
    state["posts"][key] = {"text": text, "status": "pending", "sent": False}
    title = "پیش‌نویس صبحگاهی" if slot == "morning" else "پیش‌نویس شبانه"
    send_admin(f"🌙 {title}\n\n{text}\n\nاگر تأییدش کنی، در زمان مقرر منتشر می‌شود.", key)

def process_updates(state):
    updates = api("getUpdates", {
        "offset": state.get("offset", 0),
        "timeout": 0,
        "allowed_updates": ["callback_query"]
    })
    for update in updates:
        state["offset"] = max(state.get("offset", 0), update["update_id"] + 1)
        cq = update.get("callback_query")
        if not cq:
            continue
        if cq["from"]["id"] != ADMIN_ID:
            api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "اجازه دسترسی نداری."})
            continue
        try:
            action, key = cq["data"].split("|", 1)
            post = state["posts"].get(key)
            if not post or post["status"] != "pending":
                api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "این پیش‌نویس دیگر فعال نیست."})
                continue
            post["status"] = "approved" if action == "approve" else "rejected"
            state["posts"][key] = post
            answer = "تأیید شد؛ در زمان مقرر منتشر می‌شود." if action == "approve" else "پست رد شد."
            api("answerCallbackQuery", {"callback_query_id": cq["id"], "text": answer})
            msg = cq.get("message", {})
            if msg:
                api("editMessageReplyMarkup", {
                    "chat_id": msg["chat"]["id"],
                    "message_id": msg["message_id"],
                    "reply_markup": {"inline_keyboard": []}
                })
        except Exception:
            # Keep the run alive; malformed or stale callbacks are ignored.
            pass

def publish_if_approved(state, slot, target_day):
    key = f"{target_day.isoformat()}:{slot}"
    post = state["posts"].get(key)
    if not post or post["status"] != "approved" or post.get("sent"):
        return
    api("sendMessage", {"chat_id": CHANNEL_ID, "text": post["text"]})
    post["sent"] = True
    post["status"] = "published"
    state["posts"][key] = post

def main():
    now = datetime.now(TZ)
    state = load()

    # Create drafts shortly before the two planned publishing times.
    if now.hour == 7 and 30 <= now.minute <= 39:
        make_draft(state, "morning", now.date())
    if now.hour == 23 and 30 <= now.minute <= 39:
        make_draft(state, "night", (now + timedelta(days=1)).date())

    # Process approval/rejection buttons on every run.
    process_updates(state)

    # Publish only approved posts. A small grace window accommodates 5-minute polling.
    if now.hour == 8 and 0 <= now.minute <= 14:
        publish_if_approved(state, "morning", now.date())
    if now.hour == 0 and 0 <= now.minute <= 14:
        publish_if_approved(state, "night", now.date())

    save(state)

if __name__ == "__main__":
    main()
