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
    return {"sold_out_records": []}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def append_history_log(entry: str):
    """將每一次的檢查（含未完售）寫入 LOG 檔"""
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


def generate_index_html(today_summary: str, is_sold_out_today: bool, sold_out_records: list):
    """產生專屬儀表板 HTML：僅記錄每日完售歷史"""
    rows_html = ""
    for rec in reversed(sold_out_records):
        date_str = rec.get("date", "")
        weekday_str = rec.get("weekday", "")
        time_str = rec.get("time", "")
        msg = rec.get("message", "")

        rows_html += f"""
        <tr>
            <td class="date-cell">{date_str}</td>
            <td><span class="weekday-badge">{weekday_str}</span></td>
            <td class="time-cell"><strong>{time_str}</strong></td>
            <td>{msg}</td>
        </tr>
        """

    if not rows_html:
        rows_html = '<tr><td colspan="4" style="text-align:center; color:#a0aec0; padding:24px;">尚無完售紀錄</td></tr>'

    html_content = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>九州自然動物園 Jungle Bus 每日完售紀錄</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f7f9fa;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 820px;
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
            border-left: 5px solid {"#e53e3e" if is_sold_out_today else "#3182ce"};
            background: {"#fff5f5" if is_sold_out_today else "#ebf8ff"};
        }}
        .current-label {{
            font-size: 13px;
            color: #718096;
            margin-bottom: 4px;
        }}
        .current-status {{
            font-size: 17px;
            font-weight: bold;
            color: {"#c53030" if is_sold_out_today else "#2b6cb0"};
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            text-align: left;
            padding: 12px 14px;
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
            color: #c53030;
            font-size: 15px;
            white-space: nowrap;
        }}
        .weekday-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            background: #edf2f7;
            color: #4a5568;
            font-size: 12px;
        }}
        .footer {{
            margin-top: 28px;
            font-size: 12px;
            color: #a0aec0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🦁 九州自然動物園 Jungle Bus 每日完售紀錄</h1>
        
        <div class="current-box">
            <div class="current-label">今日票況摘要</div>
            <div class="current-status">{today_summary}</div>
        </div>

        <h3>📅 每日完售歷史列表</h3>
        <table>
            <thead>
                <tr>
                    <th>日期</th>
                    <th>星期</th>
                    <th>完售時間</th>
                    <th>紀錄內容</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="footer">
            官網連結: <a href="{URL}" target="_blank" rel="noopener">African Safari Jungle Bus</a><br>
            詳細的每一次檢查紀錄請見 <a href="history.log">history.log</a> | 頁面每 5 分鐘自動重整
        </div>
    </div>
</body>
</html>
"""
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_readme_md(today_summary: str, sold_out_records: list):
    """產生 GitHub 倉庫首頁 README.md"""
    rows = ""
    for rec in reversed(sold_out_records):
        rows += f"| {rec.get('date')} | {rec.get('weekday')} | **{rec.get('time')}** | {rec.get('message')} |\n"

    if not rows:
        rows = "| - | - | - | 尚無完售紀錄 |\n"

    md_content = f"""# 🦁 九州自然動物園 Jungle Bus 每日完售紀錄

> **官網連結**：[{URL}]({URL})  
> **今日狀態**：**{today_summary}**  
> *詳細的每次 15 分鐘檢查紀錄可於 [history.log](history.log) 中查看。*

---

### 📅 每日完售歷史清單

| 日期 | 星期 | 完售時間 | 紀錄內容 |
| :--- | :--- | :--- | :--- |
{rows}

---
*由 GitHub Actions 於每日 08:00 - 16:45 (JST) 每 15 分鐘自動更新。*
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
    sold_out_records = state.get("sold_out_records", [])

    print(f"[{now_str}] 正在檢查官網最新狀態...")
    try:
        html = fetch_latest_page()
    except Exception as e:
        log_line = f"[{now_str}] [連線異常] 抓取官網失敗: {e}"
        print(log_line)
        append_history_log(log_line)
        return

    # 1. 判斷完售
    if SOLD_OUT_KEYWORD in html:
        # 檢查今天是否已經記錄過
        existing_today = next((r for r in sold_out_records if r.get("date") == today_str), None)

        if not existing_today:
            # 今日第一次發現完售：新增今日紀錄
            msg = (
                f"在{now.year}年{now.month}月{now.day}日，{weekday_str}，"
                f"Jungle Bus 票在{time_str}賣完"
            )
            new_record = {
                "date": today_str,
                "weekday": weekday_str,
                "time": time_str,
                "message": msg
            }
            sold_out_records.append(new_record)
            state["sold_out_records"] = sold_out_records
            save_state(state)

            log_line = f"[{now_str}] [完售] 首次偵測到完售: {msg}"
            print(log_line)
            append_history_log(log_line)
            today_summary = msg
        else:
            # 今日先前已經記錄過完售
            first_time = existing_today.get("time", time_str)
            today_summary = f"在{now.year}年{now.month}月{now.day}日，{weekday_str}，Jungle Bus 票在{first_time}賣完"
            log_line = f"[{now_str}] [完售] 維持完售狀態 (首度完售時間: {first_time})"
            print(log_line)
            append_history_log(log_line)

        is_sold_out_today = True

    # 2. 尚未完售 (票券剩餘少量 或 正常販售)
    else:
        is_sold_out_today = False
        if FEW_LEFT_KEYWORD in html:
            status_desc = "剩餘少量 (本日のジャングルバスは残りわずかです)"
        else:
            status_desc = "正常販售中 (未出現完售提示)"

        # 寫入每次的詳細 LOG
        log_line = f"[{now_str}] [尚未完售] {status_desc}"
        print(log_line)
        append_history_log(log_line)

        today_summary = f"今日尚未完售 ({status_desc}，最後檢查時間: {time_str} JST)"

    # 更新儀表板 HTML 與 README
    generate_index_html(today_summary, is_sold_out_today, sold_out_records)
    generate_readme_md(today_summary, sold_out_records)
    print("已成功更新儀表板 (index.html, README.md) 與 LOG (history.log)")


if __name__ == "__main__":
    main()
