from datetime import date, timedelta
from lunardate import LunarDate
import re


ICS_FILE = "china-rest-days.ics"


# =========================
# ICS 文本转义
# =========================
def ics_escape(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


# =========================
# 生成全天事件
# =========================
def make_event(event_date, title, category):
    end_date = event_date + timedelta(days=1)

    uid = f"festival-{event_date.strftime('%Y%m%d')}-{abs(hash(title))}@china-rest-calendar"

    return "\n".join([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{date.today().strftime('%Y%m%d')}T000000Z",
        f"DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}",
        f"SUMMARY:{ics_escape(title)}",
        f"DESCRIPTION:{ics_escape(category)}",
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ])


# =========================
# 农历节日
# =========================
LUNAR_FESTIVALS = [
    (1, 1, "春节"),
    (1, 15, "元宵节"),
    (5, 5, "端午节"),
    (7, 7, "七夕"),
    (7, 15, "中元节"),
    (8, 15, "中秋节"),
    (9, 9, "重阳节"),
    (12, 8, "腊八节"),
    (12, 23, "小年"),
]


# =========================
# 固定公历节日
# =========================
SOLAR_FESTIVALS = {
    (1, 1): "元旦",
    (2, 14): "情人节",
    (3, 8): "妇女节",
    (3, 12): "植树节",
    (3, 15): "消费者权益日",
    (3, 22): "世界水日",
    (3, 23): "世界气象日",
    (4, 7): "世界卫生日",
    (4, 22): "世界地球日",
    (5, 1): "劳动节",
    (5, 4): "青年节",
    (6, 1): "儿童节",
    (6, 5): "世界环境日",
    (7, 1): "建党节",
    (8, 1): "建军节",
    (9, 10): "教师节",
    (10, 1): "国庆节",
    (10, 16): "世界粮食日",
    (10, 24): "联合国日",
    (11, 8): "记者节",
    (11, 9): "全国消防日",
    (12, 1): "世界艾滋病日",
    (12, 10): "世界人权日",
    (12, 13): "国家公祭日",
    (12, 20): "澳门回归纪念日",
    (12, 25): "圣诞节",
}


# =========================
# 获取 ICS 中已有年份
# =========================
def get_years_from_ics(content):
    years = set()

    for match in re.findall(
        r"DTSTART;VALUE=DATE:(\d{4})\d{4}",
        content
    ):
        years.add(int(match))

    if not years:
        current_year = date.today().year
        return range(current_year, current_year + 3)

    return range(min(years), max(years) + 1)


# =========================
# 母亲节：5月第二个星期日
# =========================
def get_mothers_day(year):
    d = date(year, 5, 1)

    while d.weekday() != 6:
        d += timedelta(days=1)

    return d + timedelta(days=7)


# =========================
# 父亲节：6月第三个星期日
# =========================
def get_fathers_day(year):
    d = date(year, 6, 1)

    while d.weekday() != 6:
        d += timedelta(days=1)

    return d + timedelta(days=14)


# =========================
# 除夕
# =========================
def get_lunar_new_year_eve(lunar_year):
    next_new_year = LunarDate(
        lunar_year + 1,
        1,
        1
    ).toSolarDate()

    return next_new_year - timedelta(days=1)


# =========================
# 主程序
# =========================
def main():

    with open(ICS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    years = list(get_years_from_ics(content))

    events = []

    # ---------------------------------
    # 1. 公历固定节日
    # ---------------------------------
    for year in years:
        for (month, day), name in SOLAR_FESTIVALS.items():

            event_date = date(year, month, day)

            events.append(
                make_event(
                    event_date,
                    name,
                    "公历节日/纪念日"
                )
            )

        # 母亲节
        events.append(
            make_event(
                get_mothers_day(year),
                "母亲节",
                "公历节日"
            )
        )

        # 父亲节
        events.append(
            make_event(
                get_fathers_day(year),
                "父亲节",
                "公历节日"
            )
        )

    # ---------------------------------
    # 2. 农历节日
    # ---------------------------------
    #
    # 多计算一年，避免农历节日在公历年初漏掉
    #
    lunar_years = range(
        min(years) - 1,
        max(years) + 1
    )

    for lunar_year in lunar_years:

        # 除夕
        try:
            eve = get_lunar_new_year_eve(lunar_year)

            if min(years) <= eve.year <= max(years):
                events.append(
                    make_event(
                        eve,
                        "除夕",
                        "中国农历传统节日"
                    )
                )
        except Exception:
            pass

        # 其他农历节日
        for month, day, name in LUNAR_FESTIVALS:

            try:
                event_date = LunarDate(
                    lunar_year,
                    month,
                    day
                ).toSolarDate()

                if min(years) <= event_date.year <= max(years):

                    events.append(
                        make_event(
                            event_date,
                            name,
                            f"中国农历传统节日（农历{month}月{day}）"
                        )
                    )

            except Exception as e:
                print(
                    f"跳过农历节日 {lunar_year}-{month}-{day}-{name}: {e}"
                )

    # ---------------------------------
    # 3. 插入到 END:VCALENDAR 前
    # ---------------------------------
    festival_text = "\n".join(events)

    content = content.replace(
        "END:VCALENDAR",
        festival_text + "\nEND:VCALENDAR"
    )

    with open(ICS_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    print(
        f"成功增加 {len(events)} 个节日/纪念日事件。"
    )


if __name__ == "__main__":
    main()
