# 每日追番记录

追番打卡仓库:哪天更新、哪天看完,都记录在这里。

## 追番日历

| 星期 | 番剧 | 平台 |
|:---:|------|------|
| 周一 | [仙逆](https://v.qq.com/) | 腾讯视频 |
| 周四 | [灵境行者](https://v.qq.com/) | 腾讯视频 |
| 周六 | [凡人修仙传](https://www.bilibili.com/) | 哔哩哔哩 |
| 周日 | [牧神记](https://www.bilibili.com/) | 哔哩哔哩 |

档期数据在 [`schedule.json`](schedule.json),换季、新番上档时改这个文件就行。
(链接目前是平台首页,可以随时换成番剧专页链接。)

## 日常使用

在仓库目录下运行(需要 Python 3.8+):

```bash
python today.py                    # 今天有什么更新?
python today.py week               # 本周追番日历
python today.py done 牧神记         # 看完了,打卡!
python today.py done 牧神记 第52集 名场面好评   # 打卡可以带备注(集数/感想)
python today.py log                # 查看本月打卡记录
```

打卡会自动追加到 `records/年-月.md`,格式如下:

```
# 2026-09 追番记录

- 2026-09-13(周日) ✅ 牧神记（哔哩哔哩） —— 第52集 名场面好评
```

## 想加新番?

在 `schedule.json` 的 `shows` 里照抄一条,改这几个字段:

- `title`:番剧名
- `platform`:平台(腾讯视频 / 哔哩哔哩 / …)
- `weekday`:更新日,0=周一、1=周二 …… 6=周日
- `url`:观看链接(可选)

`today.py` 和打卡记录会自动跟上,不用改代码。

## 目录结构

```
.
├── README.md        # 说明
├── schedule.json    # 追番日历(番剧、平台、更新日)
├── today.py         # 打卡小助手
└── records/         # 每月打卡记录(打卡后自动生成)
```
