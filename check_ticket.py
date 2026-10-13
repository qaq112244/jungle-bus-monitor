import os
import sys
import time
import json
from datetime import datetime, timezone, timedelta
import requests

URL = "https://africansafari.co.jp/jungle-bus/"
SOLD_OUT_KEYWORD = "完売"
FEW_LEFT_KEYWORD = "残りわずか"

STATE_FILE = "state.json"
HISTORY_LOG = "history.log"
INDEX_HTML = "index.html"
README_MD = "README.md"

# 時區設定：日本時間 JST (UTC+9)
TIMEZONE_OFFSET = int(os.environ.get("TIMEZONE_OFFSET", 9))
TARGET_TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))

WEEKDAY_MAP = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"讀取狀態檔失敗: {e}")
    return {"daily_records": []}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def append_history_log(entry: str):
    """將每一次的檢查（含未完售及完整通知句）記錄在 LOG 檔"""
    with open(HISTORY_LOG, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def fetch_latest_page() -> str:
    timestamp = int(time.time() * 1000)
    params = {"_t": timestamp}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
        ),
        "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    resp = requests.get(URL, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def generate_index_html(today_summary: str, current_box_class: str, daily_records: list):
    """產生專屬儀表板 HTML：顯示 日期、星期、剩餘少量時間、完售時間"""
    rows_html = ""
    for rec in reversed(daily_records):
        date_str = rec.get("date", "")
        weekday_str = rec.get("weekday", "")
        few_left_time = rec.get("few_left_time", "-")
        sold_out_time = rec.get("sold_out_time", "-")

        sold_out_display = f"<strong>{sold_out_time}</strong>" if sold_out_time != "-" else '<span style="color:#718096;">-</span>'
        few_left_display = f'<span style="color:#dd6b20; font-weight:600;">{few_left_time}</span>' if few_left_time != "-" else '<span style="color:#718096;">-</span>'

        rows_html += f"""
        <tr>
            <td class="date-cell">{date_str}</td>
            <td><span class="weekday-badge">{weekday_str}</span></td>
            <td class="time-cell">{few_left_display}</td>
            <td class="time-cell">{sold_out_display}</td>
        </tr>
        """

    if not rows_html:
        rows_html = '<tr><td colspan="4" style="text-align:center; color:#a0aec0; padding:24px;">尚無紀錄</td></tr>'

    html_content = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>九州自然動物園 Jungle Bus 票況歷史紀錄</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f7f9fa;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 760px;
            margin: 0 auto;
            background: #fff;
            padding: 28px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }}
        h1 {{
            font-size: 22px;
            margin-top: 0;
            color: #1a202c;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .current-box {{
            padding: 16px 20px;
            border-radius: 8px;
            margin: 16px 0 28px 0;
            border-left: 5px solid #3182ce;
            background: #ebf8ff;
        }}
        .current-box.soldout {{
            border-left-color: #e53e3e;
            background: #fff5f5;
        }}
        .current-box.fewleft {{
            border-left-color: #dd6b20;
            background: #fffaf0;
        }}
        .current-label {{
            font-size: 13px;
            color: #718096;
            margin-bottom: 4px;
        }}
        .current-status {{
            font-size: 17px;
            font-weight: bold;
            color: #2b6cb0;
        }}
        .current-box.soldout .current-status {{
            color: #c53030;
        }}
        .current-box.fewleft .current-status {{
            color: #dd6b20;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            text-align: left;
            padding: 12px 16px;
            border-bottom: 1px solid #edf2f7;
            font-size: 14px;
        }}
        th {{
            background-color: #f7fafc;
            color: #4a5568;
            font-weight: 600;
        }}
        .date-cell {{
            font-weight: 600;
            color: #2d3748;
            white-space: nowrap;
        }}
        .time-cell {{
            white-space: nowrap;
            font-size: 15px;
        }}
        .weekday-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            background: #edf2f7;
            color: #4a5568;
            font-size: 12px;
        }}
        .footer {{
            margin-top: 28px;
            font-size: 12px;
            line-height: 1.8;
            color: #a0aec0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🦁 九州自然動物園 Jungle Bus 每日票況紀錄</h1>
        
        <div class="current-box {current_box_class}">
            <div class="current-label">今日票況摘要</div>
            <div class="current-status">{today_summary}</div>
        </div>

        <h3>📅 每日歷史列表 (日本時間)</h3>
        <table>
            <thead>
                <tr>
                    <th>日期</th>
                    <th>星期</th>
                    <th>剩餘少量時間</th>
                    <th>完售時間</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="footer">
            官網連結: <a href="{URL}" target="_blank" rel="noopener">African Safari Jungle Bus</a><br>
            系統每 15 分鐘自動查詢官網一次 ｜ 頁面每 5 分鐘自動重整 ｜ 詳細紀錄請見 <a href="history.log">history.log</a>
        </div>
    </div>
</body>
</html>
"""
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_readme_md(today_summary: str, daily_records: list):
    """產生 GitHub 倉庫首頁 README.md"""
    rows = ""
    for rec in reversed(daily_records):
        date_str = rec.get("date", "")
        weekday_str = rec.get("weekday", "")
        few_left = rec.get("few_left_time", "-")
        sold_out = rec.get("sold_out_time", "-")
        sold_out_fmt = f"**{sold_out}**" if sold_out != "-" else "-"
        rows += f"| {date_str} | {weekday_str} | {few_left} | {sold_out_fmt} |\n"

    if not rows:
        rows = "| - | - | - | - |\n"

    md_content = f"""# 🦁 九州自然動物園 Jungle Bus 每日票況紀錄

> **官網連結**：[{URL}]({URL})  
> **今日狀態**：**{today_summary}**  
> *詳細的每次檢查紀錄可於 [history.log](history.log) 中查看。*

---

### 📅 每日歷史列表 (日本時間)

| 日期 | 星期 | 剩餘少量時間 | 完售時間 |
| :--- | :--- | :--- | :--- |
{rows}

---
*由 GitHub Actions 於每日 08:00 - 16:45 (JST) 每 15 分鐘自動查詢官網更新。*
"""
    with open(README_MD, "w", encoding="utf-8") as f:
        f.write(md_content)


def main():
    now = datetime.now(TARGET_TZ)
    today_str = now.strftime("%Y-%m-%d")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    time_str = now.strftime("%H:%M")
    weekday_str = WEEKDAY_MAP[now.weekday()]

    state = load_state()
    daily_records = state.get("daily_records", [])

    existing_today = next((r for r in daily_records if r.get("date") == today_str), None)

    # 1. 當日完售鎖定機制（若今日已完售，狀態永久鎖定，不受下班撤除字樣影響）
    if existing_today and existing_today.get("sold_out_time", "-") != "-":
        first_sold = existing_today["sold_out_time"]
        few_time = existing_today.get("few_left_time", "-")
        if few_time != "-":
            today_summary = f"今日已完售！在{now.year}年{now.month}月{now.day}日，{weekday_str}，Jungle Bus 票在{first_sold}賣完（於 {few_time} 首度剩餘少量）"
        else:
            today_summary = f"在{now.year}年{now.month}月{now.day}日，{weekday_str}，Jungle Bus 票在{first_sold}賣完"

        current_box_class = "soldout"
        log_line = f"[{now_str}] [已完售] 今日已於 {first_sold} 完售，維持今日完售狀態鎖定。"
        print(log_line)
        append_history_log(log_line)

        save_state(state)
        generate_index_html(today_summary, current_box_class, daily_records)
        generate_readme_md(today_summary, daily_records)
        return

    # 2. 抓取官網檢查最新狀態
    print(f"[{now_str}] 正在檢查官網最新狀態...")
    try:
        html = fetch_latest_page()
    except Exception as e:
        log_line = f"[{now_str}] [連線異常] 抓取官網失敗: {e}"
        print(log_line)
        append_history_log(log_line)
        return

    # 判斷完售
    if SOLD_OUT_KEYWORD in html:
        current_box_class = "soldout"
        if not existing_today:
            new_record = {
                "date": today_str,
                "weekday": weekday_str,
                "few_left_time": "-",
                "sold_out_time": time_str,
                "message": f"在{now.year}年{now.month}月{now.day}日，{weekday_str}，Jungle Bus 票在{time_str}賣完"
            }
            daily_records.append(new_record)
            log_line = f"[{now_str}] [完售] 首次偵測到完售: {new_record['message']}"
            today_summary = new_record["message"]
        else:
            existing_today["sold_out_time"] = time_str
            existing_today["message"] = f"在{now.year}年{now.month}月{now.day}日，{weekday_str}，Jungle Bus 票在{time_str}賣完"
            log_line = f"[{now_str}] [完售] 首次偵測到完售: {existing_today['message']}"
            
            few_time = existing_today.get("few_left_time", "-")
            if few_time != "-":
                today_summary = f"今日已完售！在{now.year}年{now.month}月{now.day}日，{weekday_str}，Jungle Bus 票在{time_str}賣完（於 {few_time} 首度剩餘少量）"
            else:
                today_summary = existing_today["message"]

        print(log_line)
        append_history_log(log_line)

    # 判斷剩餘少量
    elif FEW_LEFT_KEYWORD in html:
        current_box_class = "fewleft"
        if not existing_today:
            new_record = {
                "date": today_str,
                "weekday": weekday_str,
                "few_left_time": time_str,
                "sold_out_time": "-",
                "message": ""
            }
            daily_records.append(new_record)
            log_line = f"[{now_str}] [剩餘少量] 今日首次出現剩餘少量提示 (時間: {time_str})"
            today_summary = f"今日票券所剩無幾（於 {time_str} 首度出現剩餘少量提示，目前尚未完售）"
        else:
            if existing_today.get("few_left_time", "-") == "-":
                existing_today["few_left_time"] = time_str
                log_line = f"[{now_str}] [剩餘少量] 今日首次出現剩餘少量提示 (時間: {time_str})"
            else:
                first_few = existing_today["few_left_time"]
                log_line = f"[{now_str}] [剩餘少量] 維持剩餘少量狀態 (首次告急時間: {first_few})"

            first_few = existing_today.get("few_left_time", time_str)
            today_summary = f"今日票券所剩無幾（於 {first_few} 首度出現剩餘少量提示，目前尚未完售）"

        print(log_line)
        append_history_log(log_line)

    # 正常販售中
    else:
        current_box_class = ""
        log_line = f"[{now_str}] [尚未完售] 正常販售中 (未出現完售或告急提示)"
        print(log_line)
        append_history_log(log_line)

        if existing_today and existing_today.get("few_left_time", "-") != "-":
            first_few = existing_today["few_left_time"]
            today_summary = f"今日票券曾於 {first_few} 提示剩餘少量，目前持續販售中 (最後檢查: {time_str} JST)"
        else:
            today_summary = f"今日尚未完售 (正常販售中，最後檢查時間: {time_str} JST)"

    # 儲存與產生儀表板
    state["daily_records"] = daily_records
    save_state(state)

    generate_index_html(today_summary, current_box_class, daily_records)
    generate_readme_md(today_summary, daily_records)
    print("已成功更新儀表板 (index.html, README.md) 與 LOG (history.log)")


if __name__ == "__main__":
    main()
