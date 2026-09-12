# -*- coding: utf-8 -*-
"""Jadval bilan ishlash va real vaqtni hisoblash uchun yordamchi funksiyalar."""

import datetime as dt
from zoneinfo import ZoneInfo

from data import SCHEDULE, DAYS

TZ = ZoneInfo("Asia/Tashkent")

# Python weekday(): Dushanba=0 ... Yakshanba=6
WEEKDAY_INDEX_TO_DAY = {
    0: "Dushanba",
    1: "Seshanba",
    2: "Chorshanba",
    3: "Payshanba",
    4: "Juma",
    5: "Shanba",
    6: None,  # Yakshanba - dars yo'q
}


def now_tashkent() -> dt.datetime:
    return dt.datetime.now(TZ)


def today_day_name():
    """Bugungi kun nomini qaytaradi, Yakshanba bo'lsa None."""
    return WEEKDAY_INDEX_TO_DAY.get(now_tashkent().weekday())


def _parse_time_range(time_range: str):
    start_s, end_s = [p.strip() for p in time_range.split("-")]
    start = dt.datetime.strptime(start_s, "%H:%M").time()
    end = dt.datetime.strptime(end_s, "%H:%M").time()
    return start, end


def _is_now_within(time_range: str, now_time: dt.time) -> bool:
    start, end = _parse_time_range(time_range)
    return start <= now_time <= end


def get_all_classes():
    return list(SCHEDULE.keys())


def get_class_schedule(class_name: str, day: str):
    return SCHEDULE.get(class_name, {}).get(day, [])


def get_all_teachers():
    teachers = set()
    for days in SCHEDULE.values():
        for lessons in days.values():
            for lesson in lessons:
                teachers.add(lesson["teacher"])
    return sorted(teachers)


def get_teacher_subject(teacher_name: str):
    for days in SCHEDULE.values():
        for lessons in days.values():
            for lesson in lessons:
                if lesson["teacher"] == teacher_name:
                    return lesson["subject"]
    return "Noma'lum"


def get_teacher_classes(teacher_name: str):
    classes = set()
    for class_name, days in SCHEDULE.items():
        for lessons in days.values():
            for lesson in lessons:
                if lesson["teacher"] == teacher_name:
                    classes.add(class_name)
    return sorted(classes)


def get_teacher_schedule(teacher_name: str):
    """{day: [{time, class, subject, room}, ...]} ko'rinishida qaytaradi."""
    result = {d: [] for d in DAYS}
    for class_name, days in SCHEDULE.items():
        for day, lessons in days.items():
            for lesson in lessons:
                if lesson["teacher"] == teacher_name:
                    result[day].append(
                        {
                            "time": lesson["time"],
                            "class": class_name,
                            "subject": lesson["subject"],
                            "room": lesson["room"],
                        }
                    )
    for d in result:
        result[d].sort(key=lambda x: x["time"])
    return result


def current_lesson_for_class(class_name: str):
    """Hozirgi vaqtda shu sinfda ketayotgan darsni topadi."""
    day = today_day_name()
    if day is None:
        return None, "Bugun Yakshanba — dam olish kuni, darslar yo'q."
    now_t = now_tashkent().time()
    for lesson in get_class_schedule(class_name, day):
        if _is_now_within(lesson["time"], now_t):
            return lesson, None
    return None, "Hozir dars yo'q (tanaffus yoki darslar tugagan)."


def current_status_for_teacher(teacher_name: str):
    """Hozirgi vaqtda o'qituvchi qayerda ekanini topadi."""
    day = today_day_name()
    if day is None:
        return None, "Bugun Yakshanba — dam olish kuni, darslar yo'q."
    now_t = now_tashkent().time()
    schedule = get_teacher_schedule(teacher_name)
    for lesson in schedule.get(day, []):
        if _is_now_within(lesson["time"], now_t):
            return lesson, None
    return None, "Hozir darsi yo'q."
