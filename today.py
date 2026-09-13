#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日追番记录小助手。

用法:
  python today.py                              查看今天的更新
  python today.py week                         查看本周追番日历(✅ = 已打卡)
  python today.py done <番剧> [备注] [-d 日期]  看完后打卡(默认今天;-d 可补卡)
  python today.py undo <番剧> [-d 日期]         撤销一次打卡
  python today.py log [YYYY-MM]                查看打卡记录(默认本月)
  python today.py stats [YYYY-MM]              查看追番统计(默认本月)
  python today.py open [番剧]                  打开观看链接(不带番剧 = 打开今天待看的)
"""
from __future__ import annotations

import json
import re
import sys
import webbrowser
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE_FILE = ROOT / "schedule.json"
RECORDS_DIR = ROOT / "records"
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
# 打卡行格式:- 2026-09-13(周日) ✅ 牧神记（哔哩哔哩） —— 备注
ENTRY_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})\(周[一二三四五六日]\) ✅ (.+)$")


def _ensure_utf8_console() -> None:
    # Windows 的 cmd/PowerShell 默认可能是 gbk,切到 utf-8 避免打印 ✅ 时报错
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def load_schedule() -> list[dict]:
    try:
        with SCHEDULE_FILE.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"找不到 schedule.json,请在仓库目录下运行(脚本位置:{ROOT})")
    except json.JSONDecodeError as e:
        sys.exit(f"schedule.json 不是合法的 JSON:{e}")
    shows = data.get("shows")
    if not isinstance(shows, list):
        sys.exit("schedule.json 里缺少 shows 列表")
    for s in shows:
        if not s.get("title"):
            sys.exit("schedule.json 里有番剧缺 title 字段")
        if s.get("weekday") not in range(7):
            sys.exit(f"《{s['title']}》的 weekday 必须是 0-6(0=周一、6=周日),现在是 {s.get('weekday')!r}")
    return sorted(shows, key=lambda s: s["weekday"])


def shows_on(weekday: int) -> list[dict]:
    return [s for s in load_schedule() if s["weekday"] == weekday]


def month_file(month: str) -> Path:
    return RECORDS_DIR / f"{month}.md"


def parse_month(month: str) -> list[tuple[date, str, str, str]]:
    """把某个月的打卡文件解析成 (日期, 番剧, 平台, 备注) 列表;文件不存在返回空。"""
    entries: list[tuple[date, str, str, str]] = []
    f = month_file(month)
    if not f.exists():
        return entries
    for line in f.read_text(encoding="utf-8").splitlines():
        m = ENTRY_RE.match(line)
        if not m:
            continue
        rest, _, note = m.group(2).partition(" —— ")
        title, _, platform = rest.partition("（")
        entries.append((date.fromisoformat(m.group(1)), title.strip(), platform.rstrip("）"), note.strip()))
    return entries


def watched_on(d: date) -> set[str]:
    """某天已经打过卡的番剧标题。"""
    return {t for dt, t, _, _ in parse_month(f"{d:%Y-%m}") if dt == d}


def parse_date_arg(s: str) -> date:
    if s in ("昨天", "yesterday"):
        return date.today() - timedelta(days=1)
    if s in ("今天", "today"):
        return date.today()
    try:
        return date.fromisoformat(s)
    except ValueError:
        sys.exit(f"日期看不懂:「{s}」。写成 YYYY-MM-DD(比如 2026-09-12)或「昨天」")


def extract_date(args: list[str]) -> tuple[date | None, list[str]]:
    """从参数里取出 -d/--date 选项,返回 (日期或 None, 其余参数)。"""
    target: date | None = None
    rest: list[str] = []
    i = 0
    while i < len(args):
        if args[i] in ("-d", "--date"):
            if i + 1 >= len(args):
                sys.exit(f"{args[i]} 后面要跟日期,比如:python today.py done 牧神记 -d 昨天")
            target = parse_date_arg(args[i + 1])
            i += 2
        else:
            rest.append(args[i])
            i += 1
    return target, rest


def month_arg(args: list[str]) -> str:
    """log/stats 的月份参数,默认当月。"""
    if not args:
        return f"{date.today():%Y-%m}"
    m = re.fullmatch(r"(\d{4})-(\d{2})", args[0])
    if m and 1 <= int(m.group(2)) <= 12:
        return args[0]
    sys.exit(f"月份格式不对:「{args[0]}」,应写成 YYYY-MM(比如 2026-09)")


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
    done = watched_on(today)
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
        done = watched_on(d)
        tag = "  ← 今天" if d == today else ""
        if shows:
            names = "  ".join(
                ("✅ " if s["title"] in done else "") + f"《{s['title']}》({s['platform']})"
                for s in shows
            )
            print(f"{d:%m-%d} {WEEKDAY_NAMES[i]}  {names}{tag}")
        else:
            print(f"{d:%m-%d} {WEEKDAY_NAMES[i]}  (无更新){tag}")


def cmd_done(args: list[str]) -> None:
    target, rest = extract_date(args)
    if not rest:
        print("用法:python today.py done <番剧> [备注] [-d 日期]")
        sys.exit(1)
    target = target or date.today()
    if target > date.today():
        print(f"还没到 {target:%Y-%m-%d} 呢,不能提前打卡 😅")
        sys.exit(1)
    query, note = rest[0], " ".join(rest[1:]).strip()
    show = find_show(query, load_schedule())
    if show["title"] in watched_on(target):
        print(f"{target:%Y-%m-%d} 已经打过《{show['title']}》的卡啦,不用重复记录 ✅")
        return
    f = month_file(f"{target:%Y-%m}")
    if not f.exists():
        RECORDS_DIR.mkdir(exist_ok=True)
        f.write_text(f"# {target:%Y-%m} 追番记录\n\n", encoding="utf-8")
    line = f"- {target:%Y-%m-%d}({WEEKDAY_NAMES[target.weekday()]}) ✅ {show['title']}（{show['platform']}）"
    if note:
        line += f" —— {note}"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    when = "今天" if target == date.today() else f"{target:%Y-%m-%d}"
    print(f"打卡成功:{when} {WEEKDAY_NAMES[target.weekday()]} 《{show['title']}》")
    if note:
        print(f"备注:{note}")


def cmd_undo(args: list[str]) -> None:
    target, rest = extract_date(args)
    if not rest:
        print("用法:python today.py undo <番剧> [-d 日期]")
        sys.exit(1)
    show = find_show(rest[0], load_schedule())
    target = target or date.today()
    f = month_file(f"{target:%Y-%m}")
    if not f.exists():
        print(f"{target:%Y-%m} 没有任何打卡记录")
        sys.exit(1)
    prefix = f"- {target:%Y-%m-%d}("
    marker = f"✅ {show['title']}（"
    lines = f.read_text(encoding="utf-8").splitlines()
    kept = [ln for ln in lines if not (ln.startswith(prefix) and marker in ln)]
    if len(kept) == len(lines):
        print(f"{target:%Y-%m-%d} 没打过《{show['title']}》的卡,没什么可撤销")
        sys.exit(1)
    f.write_text("".join(ln + "\n" for ln in kept), encoding="utf-8")
    print(f"已撤销 {target:%Y-%m-%d} 《{show['title']}》的打卡")


def cmd_log(args: list[str]) -> None:
    month = month_arg(args)
    f = month_file(month)
    if not f.exists():
        print(f"{month} 还没有打卡记录(records/{f.name})")
        return
    print(f.read_text(encoding="utf-8").rstrip())


def cmd_stats(args: list[str]) -> None:
    month = month_arg(args)
    entries = parse_month(month)
    if not entries:
        print(f"{month} 还没有打卡记录")
        return
    days = {d for d, _, _, _ in entries}
    counts = Counter(title for _, title, _, _ in entries)
    print(f"📊 {month} 追番统计")
    print()
    print(f"共打卡 {len(entries)} 次,覆盖 {len(days)} 天")
    for title, n in counts.most_common():
        print(f"  《{title}》 × {n}")
    noted = [(d, t, note) for d, t, _, note in entries if note]
    if noted:
        d, t, note = noted[-1]
        print()
        print(f"最近感想:{d:%m-%d} 《{t}》 —— {note}")


def cmd_open(args: list[str]) -> None:
    if args:
        show = find_show(args[0], load_schedule())
        url = show.get("url")
        if not url:
            print(f"《{show['title']}》还没配置观看链接(schedule.json 里的 url 字段)")
            sys.exit(1)
        webbrowser.open(url)
        print(f"已打开《{show['title']}》:{url}")
        return
    today = date.today()
    done = watched_on(today)
    todays = [s for s in shows_on(today.weekday()) if s["title"] not in done]
    if not todays:
        print("今天没有待看的更新,好好休息 🍵")
        return
    for s in todays:
        if s.get("url"):
            webbrowser.open(s["url"])
    names = "、".join(f"《{s['title']}》" for s in todays)
    print(f"已打开今天的待看:{names}")
    if not all(s.get("url") for s in todays):
        print("(有些番没配 url,去 schedule.json 里补一下)")


def main(argv: list[str]) -> None:
    _ensure_utf8_console()
    cmd, args = (argv[0] if argv else "today"), argv[1:]
    if cmd == "today":
        cmd_today()
    elif cmd == "week":
        cmd_week()
    elif cmd == "done":
        cmd_done(args)
    elif cmd == "undo":
        cmd_undo(args)
    elif cmd == "log":
        cmd_log(args)
    elif cmd == "stats":
        cmd_stats(args)
    elif cmd == "open":
        cmd_open(args)
    elif cmd in ("help", "-h", "--help"):
        print(__doc__)
    else:
        print(f"不认识的命令:{cmd}\n{__doc__}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
