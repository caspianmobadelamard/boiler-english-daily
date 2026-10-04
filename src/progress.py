"""مدیریت پیشرفت و آمار"""
import json
import os
from datetime import datetime, timedelta


PROGRESS_FILE = "data/progress.json"


def load_progress() -> dict:
    if not os.path.exists(PROGRESS_FILE):
        return {
            "streak": 0,
            "last_session": None,
            "total_sessions": 0,
            "sessions": [],
            "daily_scores": {},
        }
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(data: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_session(session_type: str, score: int, details: dict = None) -> dict:
    data = load_progress()
    today = datetime.now().strftime("%Y-%m-%d")

    # به‌روزرسانی استریک
    if data["last_session"]:
        last = datetime.fromisoformat(data["last_session"]).date()
        delta = (datetime.now().date() - last).days
        if delta == 1:
            data["streak"] += 1
        elif delta > 1:
            data["streak"] = 1
    else:
        data["streak"] = 1

    data["last_session"] = datetime.now().isoformat()
    data["total_sessions"] += 1

    session = {
        "date": today,
        "type": session_type,
        "score": score,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
    }
    data["sessions"].append(session)
    data["daily_scores"][today] = score

    save_progress(data)
    return data


def get_weekly_scores() -> list:
    data = load_progress()
    today = datetime.now().date()
    result = []
    for i in range(6, -1, -1):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({
            "date": day,
            "score": data["daily_scores"].get(day, 0)
        })
    return result


def get_summary() -> dict:
    data = load_progress()
    return {
        "streak": data["streak"],
        "total_sessions": data["total_sessions"],
        "average_score": (
            sum(s["score"] for s in data["sessions"]) / len(data["sessions"])
            if data["sessions"] else 0
        ),
        "last_session": data["last_session"],
    }