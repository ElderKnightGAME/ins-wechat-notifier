import os
import json
import requests
import feedparser

# ================= 配置项 =================
# 替换为你要监控的 Instagram 账号用户名
INSTAGRAM_USERNAME = "kith"

# RSSHub 节点（如果公共实例受限，可替换为你自建或第三方稳定的 RSSHub 地址）
RSS_URL = f"https://rsshub.app/instagram/user/{INSTAGRAM_USERNAME}"

SERVER_CHAN_KEY = os.environ.get("SERVERCHAN_SENDKEY")
HISTORY_FILE = "last_post.json"
# =========================================

def send_wechat_notice(title, content, link):
    """通过 Server酱 推送消息至微信"""
    if not SERVER_CHAN_KEY:
        print("未配置 SERVERCHAN_SENDKEY，跳过推送")
        return
    
    api_url = f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send"
    data = {
        "title": f"📷 Ins 更新: {title[:20]}",
        "desp": f"### [{title}]({link})\n\n{content}\n\n[点击查看原帖]({link})"
    }
    resp = requests.post(api_url, data=data)
    print("微信推送响应:", resp.json())

def get_last_seen_id():
    """读取上次记录的最新的帖子链接/ID"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_id")
        except Exception:
            return None
    return None

def save_last_seen_id(post_id):
    """保存本次最新的帖子链接/ID"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_id": post_id}, f)

def main():
    print(f"正在拉取 @{INSTAGRAM_USERNAME} 的更新...")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("未获取到动态内容，可能源受限或无更新。")
        return

    # 获取最新的一条动态
    latest_entry = feed.entries[0]
    post_id = latest_entry.id or latest_entry.link
    post_title = latest_entry.title or f"@{INSTAGRAM_USERNAME} 发布了新动态"
    post_link = latest_entry.link
    post_content = latest_entry.description or ""

    last_seen_id = get_last_seen_id()

    if last_seen_id is None:
        print(f"首次初始化运行，记录最新帖子为: {post_id}")
        save_last_seen_id(post_id)
        # 如果你想首次部署就测试一次微信通知，取消下一行的注释：
        # send_wechat_notice("测试推送: " + post_title, post_content, post_link)
    elif last_seen_id != post_id:
        print("发现新发布动态，正在推送到微信...")
        send_wechat_notice(post_title, post_content, post_link)
        save_last_seen_id(post_id)
    else:
        print("暂无新动态。")

if __name__ == "__main__":
    main()
