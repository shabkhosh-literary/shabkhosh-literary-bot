
import os
import json
import random
import urllib.request
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
        "صبح، فرصتی دوباره برای دیدن زیبایی‌های کوچک و ساختن روزی روشن است. 🌱\n\n#شب_خوش",
        "گاهی یک شروع آرام، از هزار تصمیم بزرگ ارزشمندتر است. ☀️\n\n#شب_خوش",
        "جهان هر صبح صفحه‌ای سپید پیش رویمان می‌گذارد. 🌿\n\n#شب_خوش",
    ],
    "night": [
        "شب که می‌رسد، صداها آرام می‌شوند و حرف‌های نگفته شنیده می‌شوند. 🌙\n\n#شب_خوش",
        "بعضی واژه‌ها را باید در سکوت شب میان دل و پنجره رها کرد. ✨\n\n#شب_خوش",
        "امشب کمی مکث کن؛ شاید آرامش همین باشد که با خودت مهربان‌تر شوی. 🕊️\n\n#شب_خوش",
    ],
}

CONTENT = {
    "🌹 شعر": [
        "گاهی تمام شعر جهان\nدر یک نگاه خلاصه می‌شود...\n\n#شب_خوش",
        "دلم بهانه‌ای از جنس باران می‌خواهد\nو پنجره‌ای که رو به فردا باز شود... 🌧️",
        "در ازدحام این همه صدا\nدلم سکوتی می‌خواهد\nکه نام تو را زمزمه کند. ✨",
    ],
    "📖 داستان کوتاه": [
        "پیرمرد هر روز برای دو نفر چای می‌ریخت؛ یکی برای خودش و دیگری برای خاطره‌ای که هنوز دوستش داشت.\n\nبعضی آدم‌ها حتی در نبودنشان هم مهمان خانه دل ما هستند.",
        "دختری هر شب چراغ اتاقش را روشن می‌گذاشت. پرسیدند چرا؟ گفت: شاید کسی در تاریکی دنبال راه خانه‌اش بگردد.\n\nگاهی مهربانی یعنی چراغی برای دیگری بودن.",
    ],
    "❤️ متن عاشقانه": [
        "دوست داشتن یعنی میان تمام اتفاق‌های روز، هنوز کسی باشد که دلت بخواهد اول از همه برایش تعریف کنی. ❤️",
        "بعضی آدم‌ها شبیه خانه‌اند؛ حتی وقتی دورند، دلت کنارشان آرام می‌گیرد.",
    ],
    "✨ جملات انگیزشی": [
        "قرار نیست هر روز فوق‌العاده باشی؛ کافی است هر روز کمی به خودت نزدیک‌تر شوی.",
        "از قدم‌های کوچک نترس؛ تمام مسیرهای بزرگ با یک قدم آغاز شده‌اند. 🌱",
    ],
    "🖋️ دل‌نوشته": [
        "گاهی آدم فقط دلش می‌خواهد کسی بدون پرسیدن دلیل، حال دلش را بفهمد...",
        "ما از کنار خیلی چیزها ساده می‌گذریم؛ از لبخندها، از مهربانی‌ها و از لحظه‌هایی که شاید دیگر تکرار نشوند.",
    ],
    "☀️ صبح بخیر": [
        "صبح بخیر؛ امیدوارم امروز سهم دلت آرامش و سهم نگاهت زیبایی باشد. ☀️",
        "روز تازه‌ای آغاز شده؛ با امید شروع کن و با لبخند ادامه بده. 🌷",
    ],
    "🌙 شب بخیر": [
        "شب بخیر؛ تمام خستگی‌های امروز را زمین بگذار و به آرامش فردا اعتماد کن. 🌙",
        "چشم‌هایت را ببند؛ دنیا می‌تواند تا صبح کمی صبر کند. شبت آرام. ✨",
    ],
}

MENU = {
    "keyboard": [
        ["🌹 شعر", "📖 داستان کوتاه"],
        ["❤️ متن عاشقانه", "✨ جملات انگیزشی"],
        ["🖋️ دل‌نوشته"],
        ["☀️ صبح بخیر", "🌙 شب بخیر"],
    ],
    "resize_keyboard": True,
    "persistent": True,
}

def api(method, payload):
    data = json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(
        API + method,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        result = json.loads(r.read().decode())
    if not result.get("ok"):
        raise RuntimeError(result)
    return result["result"]

def send_message(chat_id, text, markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if markup:
        payload["reply_markup"] = markup
    api("sendMessage", payload)

def is_member(user_id):
    result = api("getChatMember", {
        "chat_id": CHANNEL_ID,
        "user_id": user_id
    })
    status = result.get("status")
    return status in ("creator", "administrator", "member") or (
        status == "restricted" and result.get("is_member", False)
    )

def join_message(chat_id):
    markup = {
        "inline_keyboard": [
            [{"text": "📢 عضویت در کانال", "url": "https://t.me/go0dn"}],
            [{"text": "🔄 بررسی عضویت", "callback_data": "check_join"}]
        ]
    }
    send_message(
        chat_id,
        "🌙 به ربات شب خوش خوش آمدی!\n\n"
        "برای استفاده از امکانات ادبی ربات، ابتدا عضو کانال شب خوش شو.",
        markup
    )

def show_menu(chat_id):
    send_message(
        chat_id,
        "🌷 به دنیای واژه‌ها خوش آمدی!\n\n"
        "از منوی زیر یکی از بخش‌ها را انتخاب کن:",
        MENU
    )

def handle_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").strip()

    if text.startswith("/start"):
        if is_member(user_id):
            show_menu(chat_id)
        else:
            join_message(chat_id)
        return

    if not text:
        return

    if not is_member(user_id):
        join_message(chat_id)
        return

    if text in CONTENT:
        answer = random.choice(CONTENT[text])
        send_message(chat_id, answer, MENU)
    else:
        send_message(
            chat_id,
            "لطفاً یکی از گزینه‌های منو را انتخاب کن. 🌷",
            MENU
        )

def load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"offset": 0, "posts": {}}

def save(state):
    DATA.mkdir(exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def send_admin(text, post_key):
    markup = {
        "inline_keyboard": [[
            {"text": "✅ تأیید", "callback_data": f"approve|{post_key}"},
            {"text": "❌ رد", "callback_data": f"reject|{post_key}"}
        ]]
    }
    api("sendMessage", {
        "chat_id": ADMIN_ID,
        "text": text,
        "reply_markup": markup
    })

def make_draft(state, slot, target_day):
    key = f"{target_day.isoformat()}:{slot}"
    if key in state["posts"]:
        return

    text = random.choice(BANK[slot])
    state["posts"][key] = {
        "text": text,
        "status": "pending",
        "sent": False
    }
    title = "پیش‌نویس صبحگاهی" if slot == "morning" else "پیش‌نویس شبانه"
    send_admin(
        f"🌙 {title}\n\n{text}\n\n"
        "اگر تأییدش کنی، در زمان مقرر منتشر می‌شود.",
        key
    )

def process_updates(state):
    updates = api("getUpdates", {
        "offset": state.get("offset", 0),
        "timeout": 0,
        "allowed_updates": ["message", "callback_query"]
    })

    for update in updates:
        state["offset"] = max(
            state.get("offset", 0),
            update["update_id"] + 1
        )

        message = update.get("message")
        if message:
            handle_message(message)
            continue

        cq = update.get("callback_query")
        if not cq:
            continue

        user_id = cq["from"]["id"]
        chat_id = cq.get("message", {}).get("chat", {}).get("id")

        if cq.get("data") == "check_join":
            api("answerCallbackQuery", {
                "callback_query_id": cq["id"]
            })
            if is_member(user_id):
                show_menu(chat_id)
            else:
                join_message(chat_id)
            continue

        if user_id != ADMIN_ID:
            api("answerCallbackQuery", {
                "callback_query_id": cq["id"],
                "text": "اجازه دسترسی نداری."
            })
            continue

        try:
            action, key = cq["data"].split("|", 1)
            post = state["posts"].get(key)

            if not post or post["status"] != "pending":
                api("answerCallbackQuery", {
                    "callback_query_id": cq["id"],
                    "text": "این پیش‌نویس دیگر فعال نیست."
                })
                continue

            if action not in ("approve", "reject"):
                continue

            post["status"] = (
                "approved" if action == "approve" else "rejected"
            )
            state["posts"][key] = post

            answer = (
                "تأیید شد؛ در زمان مقرر منتشر می‌شود."
                if action == "approve"
                else "پست رد شد."
            )
            api("answerCallbackQuery", {
                "callback_query_id": cq["id"],
                "text": answer
            })

            msg = cq.get("message", {})
            if msg:
                api("editMessageReplyMarkup", {
                    "chat_id": msg["chat"]["id"],
                    "message_id": msg["message_id"],
                    "reply_markup": {"inline_keyboard": []}
                })
        except Exception:
            pass

def publish_if_approved(state, slot, target_day):
    key = f"{target_day.isoformat()}:{slot}"
    post = state["posts"].get(key)

    if not post or post["status"] != "approved" or post.get("sent"):
        return

    api("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": post["text"]
    })
    post["sent"] = True
    post["status"] = "published"
    state["posts"][key] = post

def main():
    now = datetime.now(TZ)
    state = load()

    if now.hour == 7 and 30 <= now.minute <= 39:
        make_draft(state, "morning", now.date())

    if now.hour == 23 and 30 <= now.minute <= 39:
        make_draft(state, "night", (now + timedelta(days=1)).date())

    process_updates(state)

    if now.hour == 8 and 0 <= now.minute <= 14:
        publish_if_approved(state, "morning", now.date())

    if now.hour == 0 and 0 <= now.minute <= 14:
        publish_if_approved(state, "night", now.date())

    save(state)

if __name__ == "__main__":
    main()
