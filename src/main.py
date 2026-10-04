"""نقطه ورود اصلی برنامه"""
import os
import json
from datetime import datetime
from .ai_client import AIClient
from .prompts import VOCAB_PROMPT, DAILY_SCENARIO_PROMPT
from .vocabulary import add_words, get_due_words, get_stats
from .listening import generate_listening_exercise
from .progress import log_session, get_summary, get_weekly_scores
from .notifier import send_telegram


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
]

CATEGORIES = [
    "customer requesting a quotation for a 10-ton steam boiler",
    "ASME inspector asking about WPS and PQR documents",
    "operator reporting low water level in the boiler",
    "site engineer discussing hydrotest procedure",
    "manager reviewing project timeline and delivery",
    "supplier negotiating spare parts prices",
]


def pick_daily_topic() -> str:
    day = datetime.now().timetuple().tm_yday
    return TOPICS[day % len(TOPICS)]


def pick_daily_category() -> str:
    day = datetime.now().timetuple().tm_yday
    return CATEGORIES[day % len(CATEGORIES)]


def copy_data_to_docs():
    """کپی داده‌ها برای GitHub Pages"""
    os.makedirs("docs/data", exist_ok=True)
    for fname in ["vocabulary.json", "progress.json", "curriculum.json", "scenarios.json"]:
        src = f"data/{fname}"
        if os.path.exists(src):
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()
            with open(f"docs/data/{fname}", "w", encoding="utf-8") as f:
                f.write(content)


def run_daily_practice():
    print("=" * 60)
    print(f"🚀 Daily English Practice — {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)

    client = AIClient()
    topic = pick_daily_topic()
    category = pick_daily_category()

    # ۱) واژگان جدید
    print(f"\n📚 Generating vocabulary on: {topic}")
    vocab_prompt = VOCAB_PROMPT.format(count=5, topic=topic)
    vocab_data = client.generate_json(vocab_prompt)
    added = add_words(vocab_data.get("words", []), topic)
    print(f"   → Added {added} new words")

    # ۲) تمرین شنیداری
    print(f"\n🎧 Generating listening exercise on: {topic}")
    listening = generate_listening_exercise(topic, client)
    print(f"   → Title: {listening.get('title')}")

    # ۳) سناریوی روزانه
    print(f"\n🎭 Generating role-play scenario")
    scenario = client.generate_json(DAILY_SCENARIO_PROMPT.format(category=category))
    scenarios_file = "data/scenarios.json"
    scenarios = []
    if os.path.exists(scenarios_file):
        with open(scenarios_file, "r", encoding="utf-8") as f:
            scenarios = json.load(f)
    scenario["date"] = datetime.now().strftime("%Y-%m-%d")
    scenarios.insert(0, scenario)
    scenarios = scenarios[:30]
    with open(scenarios_file, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)

    # ۴) کلمات در انتظار مرور
    due = get_due_words(limit=10)
    print(f"\n🔁 Words due for review: {len(due)}")

    # ۵) ثبت پیشرفت
    log_session("daily", score=100, details={
        "topic": topic,
        "new_words": added,
        "due_reviews": len(due),
    })

    # ۶) آمار کلی
    stats = get_stats()
    summary = get_summary()
    weekly = get_weekly_scores()

    # ۷) ذخیره خلاصه روزانه برای فرانت
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
    os.makedirs("output", exist_ok=True)
    with open("output/today.json", "w", encoding="utf-8") as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2)

    # ۸) کپی به docs
    copy_data_to_docs()
    with open("docs/data/today.json", "w", encoding="utf-8") as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2)

    # ۹) ارسال به تلگرام
    msg = (
        f"🔥 <b>Daily English — {daily_summary['date']}</b>\n\n"
        f"📚 Topic: <i>{topic}</i>\n"
        f"🆕 New words: {added}\n"
        f"🔁 Due reviews: {len(due)}\n"
        f"🎧 Listening: {listening.get('title', '-')}\n"
        f"🎯 Streak: {summary['streak']} days\n\n"
        f"➡️ https://YOUR_USERNAME.github.io/boiler-english-daily/"
    )
    if send_telegram(msg):
        print("\n✅ Telegram notification sent")
    else:
        print("\n⚠️  Telegram not configured")

    print("\n" + "=" * 60)
    print(f"✅ Done. Streak: {summary['streak']} | Total words: {stats['total']}")
    print("=" * 60)


if __name__ == "__main__":
    run_daily_practice()