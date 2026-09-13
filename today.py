#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日追番记录小助手。

用法:
  python today.py                  查看今天的更新
  python today.py week             查看本周追番日历
  python today.py done <番剧> [备注]  看完后打卡(记录到 records/当月.md)
  python today.py log              查看本月的打卡记录
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE_FILE = ROOT / "schedule.json"
RECORDS_DIR = ROOT / "records"
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _ensure_utf8_console() -> None:
    # Windows 的 cmd/PowerShell 默认可能是 gbk,切到 utf-8 避免打印 ✅ 时报错
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def load_schedule() -> list[dict]:
    with SCHEDULE_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return sorted(data["shows"], key=lambda s: s["weekday"])


def shows_on(weekday: int) -> list[dict]:
    return [s for s in load_schedule() if s["weekday"] == weekday]


def month_file(d: date) -> Path:
    return RECORDS_DIR / f"{d:%Y-%m}.md"


def watched_today() -> set[str]:
    """返回今天已经打过卡的番剧标题。"""
    today = date.today()
    f = month_file(today)
    if not f.exists():
        return set()
    done: set[str] = set()
    prefix = f"- {today:%Y-%m-%d}("
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix) and "✅" in line:
            after = line.split("✅", 1)[1]
            title = after.split("（", 1)[0].strip()
            if title:
                done.add(title)
    return done


def find_show(query: str, shows: list[dict]) -> dict:
    exact = [s for s in shows if s["title"] == query]
    if exact:
        return exact[0]
    fuzzy = [s for s in shows if query in s["title"] or s["title"] in query]
    if len(fuzzy) == 1:
        return fuzzy[0]
    titles = "、".join(f"《{s['title']}》" for s in shows)
    if fuzzy:
        print(f"「{query}」匹配到多部:{titles},请写全一点")
    else:
        print(f"番剧表里没有「{query}」。目前的番剧有:{titles}")
    sys.exit(1)


def cmd_today() -> None:
    today = date.today()
    print(f"今天是 {today:%Y-%m-%d} {WEEKDAY_NAMES[today.weekday()]}")
    done = watched_today()
    todays = shows_on(today.weekday())
    if not todays:
        print("今天没有追的番更新,好好休息 🍵")
        return
    for s in todays:
        mark = "✅ 已看" if s["title"] in done else "⏳ 待看"
        line = f"  {mark} 《{s['title']}》 {s['platform']}"
        if s.get("url"):
            line += f"  {s['url']}"
        print(line)


def cmd_week() -> None:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    for i in range(7):
        d = monday + timedelta(days=i)
        shows = shows_on(i)
        tag = "  ← 今天" if d == today else ""
        if shows:
            names = "  ".join(f"《{s['title']}》({s['platform']})" for s in shows)
            print(f"{d:%m-%d} {WEEKDAY_NAMES[i]}  {names}{tag}")
        else:
            print(f"{d:%m-%d} {WEEKDAY_NAMES[i]}  (无更新){tag}")


def cmd_done(query: str, note: str) -> None:
    today = date.today()
    show = find_show(query, load_schedule())
    if show["title"] in watched_today():
        print(f"今天已经打过《{show['title']}》的卡啦,不用重复记录 ✅")
        return
    f = month_file(today)
    if not f.exists():
        RECORDS_DIR.mkdir(exist_ok=True)
        f.write_text(f"# {today:%Y-%m} 追番记录\n\n", encoding="utf-8")
    line = f"- {today:%Y-%m-%d}({WEEKDAY_NAMES[today.weekday()]}) ✅ {show['title']}（{show['platform']}）"
    if note:
        line += f" —— {note}"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(f"打卡成功:{today:%Y-%m-%d} {WEEKDAY_NAMES[today.weekday()]} 《{show['title']}》")
    if note:
        print(f"备注:{note}")


def cmd_log() -> None:
    f = month_file(date.today())
    if not f.exists():
        print(f"本月还没有打卡记录(records/{f.name})")
        return
    print(f.read_text(encoding="utf-8").rstrip())


def main(argv: list[str]) -> None:
    _ensure_utf8_console()
    cmd, args = (argv[0] if argv else "today"), argv[1:]
    if cmd == "today":
        cmd_today()
    elif cmd == "week":
        cmd_week()
    elif cmd == "done":
        if not args:
            print("用法:python today.py done <番剧> [备注]")
            sys.exit(1)
        cmd_done(args[0], " ".join(args[1:]).strip())
    elif cmd == "log":
        cmd_log()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
