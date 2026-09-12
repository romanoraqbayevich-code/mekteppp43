# -*- coding: utf-8 -*-
"""
Oddiy JSON asosidagi saqlash: foydalanuvchilar ro'yxati, texnik ishlar rejimi,
statistika. E'TIBOR: bu ma'lumotlar server qayta ishga tushganda (masalan,
Render'da qayta deploy qilinganda) yo'qolishi mumkin - bu qasddan shunday,
chunki asosiy jadval ma'lumotlari data.py faylida alohida saqlanadi.
"""

import json
import os
import threading

_LOCK = threading.Lock()
_FILE_PATH = os.path.join(os.path.dirname(__file__), "state.json")

_DEFAULT_STATE = {
    "users": [],  # chat_id lar ro'yxati (broadcast uchun)
    "maintenance": False,  # texnik ishlar rejimi
    "action_counts": {},  # {"stu:schedule": 12, ...} - statistika uchun
}


def _load():
    if not os.path.exists(_FILE_PATH):
        return dict(_DEFAULT_STATE)
    try:
        with open(_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, value in _DEFAULT_STATE.items():
            data.setdefault(key, value)
        return data
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_STATE)


def _save(state):
    with open(_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def register_user(chat_id: int):
    with _LOCK:
        state = _load()
        if chat_id not in state["users"]:
            state["users"].append(chat_id)
            _save(state)


def get_all_users():
    with _LOCK:
        return list(_load()["users"])


def is_maintenance() -> bool:
    with _LOCK:
        return bool(_load()["maintenance"])


def toggle_maintenance() -> bool:
    with _LOCK:
        state = _load()
        state["maintenance"] = not state["maintenance"]
        _save(state)
        return state["maintenance"]


def log_action(action: str):
    with _LOCK:
        state = _load()
        state["action_counts"][action] = state["action_counts"].get(action, 0) + 1
        _save(state)


def get_stats():
    with _LOCK:
        state = _load()
        return {
            "user_count": len(state["users"]),
            "action_counts": dict(state["action_counts"]),
        }
