"""مدیریت واژگان با مرور فاصله‌دار SM-2"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict


DATA_FILE = "data/vocabulary.json"


def load_vocabulary() -> Dict:
    if not os.path.exists(DATA_FILE):
        return {"words": [], "topics_covered": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_vocabulary(data: Dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_words(new_words: List[Dict], topic: str) -> int:
    data = load_vocabulary()
    existing = {w["word"].lower() for w in data["words"]}
    added = 0
    for w in new_words:
        if w["word"].lower() in existing:
            continue
        w["topic"] = topic
        w["added_at"] = datetime.now().isoformat()
        w["next_review"] = datetime.now().isoformat()
        w["interval"] = 1
        w["ease"] = 2.5
        w["repetitions"] = 0
        w["mastery"] = 0  # 0-100
        data["words"].append(w)
        added += 1
    if topic not in data["topics_covered"]:
        data["topics_covered"].append(topic)
    save_vocabulary(data)
    return added


def get_due_words(limit: int = 10) -> List[Dict]:
    data = load_vocabulary()
    now = datetime.now()
    due = []
    for w in data["words"]:
        nr = datetime.fromisoformat(w.get("next_review", now.isoformat()))
        if nr <= now:
            due.append(w)
    due.sort(key=lambda x: x.get("mastery", 0))
    return due[:limit]


def review_word(word: str, quality: int) -> Dict:
    """quality: 0=فراموش، 3=سخت، 4=خوب، 5=راحت"""
    data = load_vocabulary()
    for w in data["words"]:
        if w["word"].lower() == word.lower():
            if quality < 3:
                w["repetitions"] = 0
                w["interval"] = 1
            else:
                w["repetitions"] += 1
                if w["repetitions"] == 1:
                    w["interval"] = 1
                elif w["repetitions"] == 2:
                    w["interval"] = 6
                else:
                    w["interval"] = int(w["interval"] * w["ease"])
                w["ease"] = max(1.3, w["ease"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            w["next_review"] = (datetime.now() + timedelta(days=w["interval"])).isoformat()
            w["mastery"] = min(100, w["repetitions"] * 20)
            save_vocabulary(data)
            return w
    return {}


def get_stats() -> Dict:
    data = load_vocabulary()
    words = data["words"]
    total = len(words)
    mastered = sum(1 for w in words if w.get("mastery", 0) >= 80)
    learning = sum(1 for w in words if 0 < w.get("mastery", 0) < 80)
    return {
        "total": total,
        "mastered": mastered,
        "learning": learning,
        "new": total - mastered - learning,
        "topics": len(data.get("topics_covered", [])),
    }