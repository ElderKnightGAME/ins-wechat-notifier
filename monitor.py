import os
import json
import re
import requests

# ================= 配置项 =================
# 在列表中添加你想监控的所有 Instagram 账号用户名（无需加 @）
TARGET_ACCOUNTS = [
    "kith",
    "ronniefieg",
    "kithandkin",
    "kithtreats",
    # 可以继续往下加，例如: "apple"
]

SERVER_CHAN_KEY = os.environ.get("SERVERCHAN_SENDKEY")
HISTORY_FILE = "last_post.json"
# =========================================

def send_wechat_notice(username, title, content, link):
    """通过 Server酱 推送消息至微信"""
    if not SERVER_CHAN_KEY:
        print("未配置 SERVERCHAN_SENDKEY，跳过推送")
        return
    
    api_url = f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send"
    data = {
        "title": f"📷 @{username} 更新: {title[:18]}",
        "desp": f"### [@{username} 新动态: {title}]({link})\n\n{content}\n\n[点击查看原帖]({link})"
    }
    try:
        resp = requests.post(api_url, data=data, timeout=10)
        print(f"[@{username}] 微信推送响应:", resp.json())
    except Exception as e:
        print(f"[@{username}] 推送请求异常:", e)

def load_history():
    """读取所有账号的历史记录字典 {username: last_id}"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history):
    """保存所有账号的历史记录"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_latest_post(username):
    """抓取指定账号的最新一条动态"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    sources = [
        f"https://www.picuki.com/profile/{username}",
        f"https://dumpoir.com/v/{username}"
    ]
    
    for url in sources:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                match = re.search(r'/(?:p|media)/([a-zA-Z0-9_-]{10,12})', res.text)
                if match:
                    shortcode = match.group(1)
                    post_link = f"https://www.instagram.com/p/{shortcode}/"
                    return {
                        "id": shortcode,
                        "title": f"发布了新帖子",
                        "desc": f"监测到 @{username} 发布了新动态，点击链接直达查看！",
                        "link": post_link
                    }
        except Exception:
            continue
            
    return None

def check_account(username, history):
    """巡检单个账号"""
    print(f"\n--- 正在拉取 @{username} 的动态 ---")
    post = fetch_latest_post(username)
    last_id = history.get(username)

    if not post:
        print(f"[@{username}] 未能解析到动态内容（可能源受限或该账号无公开贴）。")
        return

    post_id = post["id"]
    post_title = post["title"]
    post_link = post["link"]
    post_content = post["desc"]

    # 首次遇到该账号：记录底稿并发送一次初始测试
    if last_id is None:
        print(f"[@{username}] 首次收录，最新帖子 ID: {post_id}，正在发送初次关联提醒...")
        history[username] = post_id
        send_wechat_notice(username, "首次监控成功: " + post_title, post_content, post_link)
    # 检测到新帖子发布
    elif str(last_id) != str(post_id):
        print(f"[@{username}] 发现新动态！正在推送微信...")
        send_wechat_notice(username, post_title, post_content, post_link)
        history[username] = post_id
    else:
        print(f"[@{username}] 暂无新动态。")

def main():
    history = load_history()
    
    # 循环检查列表中的每个博主
    for username in TARGET_ACCOUNTS:
        username = username.strip().lstrip("@")
        if not username:
            continue
        check_account(username, history)
    
    # 将更新后的所有博主状态统一保存
    save_history(history)

if __name__ == "__main__":
    main()
