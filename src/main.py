"""
Boiler English Daily — Main entry point
اجرای تمرین روزانه: واژگان + شنیداری + سناریو + مرور + پیشرفت + نوتیفیکیشن
"""
import os
import sys
import json
import shutil
import traceback
from datetime import datetime

# اجازه import نسبی وقتی به صورت ماژول اجرا می‌شود
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai_client import AIClient
from src.prompts import VOCAB_PROMPT, DAILY_SCENARIO_PROMPT
from src.vocabulary import add_words, get_due_words, get_stats
from src.listening import generate_listening_exercise
from src.progress import log_session, get_summary, get_weekly_scores
from src.notifier import send_telegram


# ============ تنظیمات ============
TOPICS = [
    "steam boiler components",
    "hot water boiler operation",
    "pressure vessel fabrication",
    "welding procedures (WPS/PQR)",
    "non-destructive testing (NDT)",
    "ASME code compliance",
    "hydrostatic testing",
    "boiler safety valves",
    "materials (SA-516, SA-106)",
    "burner and combustion systems",
    "feedwater and blowdown",
    "inspection and quality control",
    "heat exchanger design",
    "pipe fittings and flanges",
    "corrosion and material selection",
    "boiler efficiency and performance",
]

CATEGORIES = [
    "customer requesting a quotation for a 10-ton steam boiler",
    "ASME inspector asking about WPS and PQR documents",
    "operator reporting low water level in the boiler",
    "site engineer discussing hydrotest procedure",
    "manager reviewing project timeline and delivery",
    "supplier negotiating spare parts prices",
    "technician explaining boiler startup procedure",
    "engineer reviewing P&ID drawing with the team",
    "safety officer checking pressure relief valve settings",
    "project manager presenting weekly progress report",
    "customer complaining about delayed shipment",
    "design engineer clarifying nozzle orientation on vessel drawing",
]


# ============ انتخاب موضوع روز ============
def pick_daily_topic() -> str:
    day = datetime.now().timetuple().tm_yday
    return TOPICS[day % len(TOPICS)]


def pick_daily_category() -> str:
    day = datetime.now().timetuple().tm_yday
    return CATEGORIES[day % len(CATEGORIES)]


# ============ کپی داده‌ها به docs برای GitHub Pages ============
def copy_data_to_docs():
    """کپی داده‌ها و فایل‌های صوتی برای GitHub Pages"""
    os.makedirs("docs/data", exist_ok=True)

    # کپی فایل‌های JSON
    for fname in ["vocabulary.json", "progress.json", "curriculum.json", "scenarios.json"]:
        src = f"data/{fname}"
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
            with open(f"docs/data/{fname}", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✓ Copied {fname}")

    # کپی فایل‌های صوتی MP3
    if os.path.exists("output"):
        for fname in os.listdir("output"):
            if fname.endswith(".mp3"):
                src = os.path.join("output", fname)
                dst = os.path.join("docs/data", fname)
                try:
                    shutil.copy2(src, dst)
                    print(f"   ✓ Copied {fname}")
                except Exception as e:
                    print(f"   ⚠️  Failed to copy {fname}: {e}")


# ============ ذخیره خلاصه روزانه ============
def save_daily_summary(daily_summary: dict):
    """ذخیره خلاصه روزانه در output و docs/data"""
    os.makedirs("output", exist_ok=True)
    os.makedirs("docs/data", exist_ok=True)

    with open("output/today.json", "w", encoding="utf-8") as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2)

    with open("docs/data/today.json", "w", encoding="utf-8") as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2)

    # آرشیو روزانه
    date_str = daily_summary["date"]
    archive_path = f"output/archive_{date_str}.json"
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2)


# ============ ساخت پیام تلگرام ============
def build_telegram_message(daily_summary: dict, stats: dict, summary: dict) -> str:
    topic = daily_summary.get("topic", "-")
    new_words = daily_summary.get("new_words", 0)
    due_count = len(daily_summary.get("due_words", []))
    listening_title = daily_summary.get("listening", {}).get("title", "-")
    streak = summary.get("streak", 0)

    pages_url = os.getenv("PAGES_URL", "https://caspianmobadelamard.github.io/boiler-english-daily/")

    msg = (
        f"🔥 <b>Boiler English — {daily_summary['date']}</b>\n\n"
        f"📚 Topic: <i>{topic}</i>\n"
        f"🆕 New words: <b>{new_words}</b>\n"
        f"🔁 Due reviews: <b>{due_count}</b>\n"
        f"🎧 Listening: <i>{listening_title}</i>\n"
        f"📊 Total words: <b>{stats.get('total', 0)}</b>\n"
        f"🔥 Streak: <b>{streak} days</b>\n\n"
        f"➡️ <a href='{pages_url}'>Open Dashboard</a>"
    )
    return msg


# ============ اجرای اصلی ============
def run_daily_practice():
    print("=" * 60)
    print(f"🚀 Boiler English Daily — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    try:
        client = AIClient()
        print("✅ AI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AI client: {e}")
        print("   Check GEMINI_API_KEY environment variable / secret")
        sys.exit(1)

    topic = pick_daily_topic()
    category = pick_daily_category()
    print(f"\n📌 Today's topic: {topic}")
    print(f"🎭 Today's scenario: {category}\n")

    # ---------- ۱) واژگان جدید ----------
    print("📚 [1/5] Generating vocabulary...")
    vocab_data = {"words": []}
    try:
        vocab_prompt = VOCAB_PROMPT.format(count=5, topic=topic)
        vocab_data = client.generate_json(vocab_prompt)
        added = add_words(vocab_data.get("words", []), topic)
        print(f"   ✓ Added {added} new words")
    except Exception as e:
        print(f"   ⚠️  Vocabulary generation failed: {e}")
        added = 0

    # ---------- ۲) تمرین شنیداری ----------
    print("\n🎧 [2/5] Generating listening exercise...")
    listening = {}
    try:
        listening = generate_listening_exercise(topic, client)
        print(f"   ✓ Title: {listening.get('title', '-')}")
        print(f"   ✓ Audio: {listening.get('audio_file', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️  Listening generation failed: {e}")
        listening = {"title": "-", "text": "", "questions": [], "audio_file": None}

    # ---------- ۳) سناریوی روزانه ----------
    print("\n🎭 [3/5] Generating role-play scenario...")
    scenario = {}
    try:
        scenario = client.generate_json(DAILY_SCENARIO_PROMPT.format(category=category))
        scenario["date"] = datetime.now().strftime("%Y-%m-%d")

        scenarios_file = "data/scenarios.json"
        scenarios = []
        if os.path.exists(scenarios_file):
            with open(scenarios_file, "r", encoding="utf-8") as f:
                try:
                    scenarios = json.load(f)
                except json.JSONDecodeError:
                    scenarios = []

        scenarios.insert(0, scenario)
        scenarios = scenarios[:30]  # فقط ۳۰ سناریوی آخر

        os.makedirs("data", exist_ok=True)
        with open(scenarios_file, "w", encoding="utf-8") as f:
            json.dump(scenarios, f, ensure_ascii=False, indent=2)

        print(f"   ✓ Scenario: {scenario.get('title', '-')}")
    except Exception as e:
        print(f"   ⚠️  Scenario generation failed: {e}")
        scenario = {"title": "-", "context_persian": "", "opening_line": "", "key_phrases": [], "vocabulary": []}

    # ---------- ۴) کلمات در انتظار مرور ----------
    print("\n🔁 [4/5] Checking due words...")
    due = get_due_words(limit=10)
    print(f"   ✓ {len(due)} words due for review")

    # ---------- ۵) ثبت پیشرفت ----------
    print("\n📊 [5/5] Logging progress...")
    log_session("daily", score=100, details={
        "topic": topic,
        "new_words": added,
        "due_reviews": len(due),
    })

    stats = get_stats()
    summary = get_summary()
    weekly = get_weekly_scores()

    print(f"   ✓ Total words: {stats['total']} | Mastered: {stats['mastered']}")
    print(f"   ✓ Streak: {summary['streak']} days | Sessions: {summary['total_sessions']}")

    # ---------- ذخیره خلاصه روزانه ----------
    daily_summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "new_words": added,
        "listening": listening,
        "scenario": scenario,
        "due_words": due,
        "stats": stats,
        "summary": summary,
        "weekly": weekly,
    }

    print("\n💾 Saving daily summary...")
    save_daily_summary(daily_summary)

    # ---------- کپی به docs ----------
    print("\n📁 Copying data to docs/ for GitHub Pages...")
    copy_data_to_docs()

    # ---------- ارسال به تلگرام ----------
    print("\n📱 Sending Telegram notification...")
    telegram_msg = build_telegram_message(daily_summary, stats, summary)
    if send_telegram(telegram_msg):
        print("   ✓ Telegram notification sent")
    else:
        print("   ⚠️  Telegram not configured (skipped)")

    print("\n" + "=" * 60)
    print(f"✅ Done. Streak: {summary['streak']} | Total words: {stats['total']}")
    print("=" * 60)


# ============ Entry ============
if __name__ == "__main__":
    try:
        run_daily_practice()
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ FATAL ERROR: {e}")
        print("=" * 60)
        traceback.print_exc()
        sys.exit(1)