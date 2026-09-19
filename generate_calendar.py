#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成中国大陆“休息日”iCalendar。"""

import json
import urllib.request
from datetime import date, timedelta

DATA_URL = "https://cdn.jsdelivr.net/npm/chinese-days/dist/chinese-days.json"
OUT = "china-rest-days.ics"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "china-rest-calendar/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def dates_from_section(section):
    if not isinstance(section, dict):
        return set()
    out = set()
    for key in section.keys():
        if len(key) == 10 and key[4] == "-" and key[7] == "-":
            try:
                out.add(date.fromisoformat(key))
            except ValueError:
                pass
    return out

def main():
    today = date.today()
    start_year, end_year = today.year, today.year + 2
    data = fetch_json(DATA_URL)

    holidays = dates_from_section(data.get("holidays", {}))
    workdays = dates_from_section(data.get("workdays", {}))

    # 兼容部分旧/替代数据格式
    if not holidays and isinstance(data.get("Years"), dict):
        for year_data in data["Years"].values():
            if not isinstance(year_data, list):
                continue
            for item in year_data:
                if not isinstance(item, dict):
                    continue
                start = item.get("StartDate")
                end = item.get("EndDate", start)
                if start:
                    try:
                        a, b = date.fromisoformat(start), date.fromisoformat(end)
                        while a <= b:
                            holidays.add(a)
                            a += timedelta(days=1)
                    except Exception:
                        pass
                for w in item.get("CompDays", []) or []:
                    try:
                        workdays.add(date.fromisoformat(w))
                    except Exception:
                        pass

    rest_days = set()
    d = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    while d <= end:
        if d.weekday() >= 5:  # 周六/周日
            rest_days.add(d)
        d += timedelta(days=1)

    rest_days.update(holidays)
    rest_days.difference_update(workdays)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//China Rest Days//CN//Apple Calendar//",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:中国休息日",
        "X-WR-TIMEZONE:Asia/Shanghai",
    ]

    for d in sorted(rest_days):
        ds = d.strftime("%Y%m%d")
        next_ds = (d + timedelta(days=1)).strftime("%Y%m%d")
        lines += [
            "BEGIN:VEVENT",
            f"UID:restday-{d.isoformat()}@china-rest-calendar",
            f"DTSTAMP:{ds}T000000Z",
            f"DTSTART;VALUE=DATE:{ds}",
            f"DTEND;VALUE=DATE:{next_ds}",
            "SUMMARY:休息日",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")

    print(f"已生成 {OUT}：{start_year}-{end_year}，共 {len(rest_days)} 个休息日")

if __name__ == "__main__":
    main()
