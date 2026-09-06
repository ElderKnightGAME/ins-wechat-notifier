import os
import json
import requests
from bs4 import BeautifulSoup

# ================= 配置项 =================
INSTAGRAM_USERNAME = "kith"  # 目标账号
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
        "title": f"📷 Kith 更新: {title[:20]}",
        "desp": f"### [{title}]({link})\n\n{content}\n\n[点击查看原帖]({link})"
    }
    resp = requests.post(api_url, data=data)
    print("微信推送响应:", resp.json())

def get_last_seen_id():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_id")
        except Exception:
            return None
    return None

def save_last_seen_id(post_id):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_id": post_id}, f)

def fetch_latest_post():
    url = f"https://www.picuki.com/profile/{INSTAGRAM_USERNAME}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"请求失败，状态码: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.text, "html.parser")
        post_box = soup.select_one(".box-photo")
        if not post_box:
            print("未能解析到帖子列表")
            return None
        
        link_tag = post_box.select_one("a")
        post_link = link_tag.get("href") if link_tag else ""
        
        # 提取文字描述
        desc_tag = post_box.select_one(".photo-description")
        desc_text = desc_tag.get_text(strip=True) if desc_tag else "无文字描述"
        
        # 提取缩略图
        img_tag = post_box.select_one("img.post-image")
        img_url = img_tag.get("src") if img_tag else ""
        
        post_id = post_link.strip("/").split("/")[-1] if post_link else "latest"
        return {
            "id": post_id,
            "title": desc_text[:40] if desc_text else "发布了新动态",
            "desc": f"![封面]({img_url})\n\n{desc_text}",
            "link": post_link
        }
    except Exception as e:
        print(f"抓取异常: {e}")
        return None

def main():
    print(f"正在拉取 @{INSTAGRAM_USERNAME} 的最新动态...")
    post = fetch_latest_post()

    if not post:
        print("未获取到动态内容。")
        return

    post_id = post["id"]
    post_title = post["title"]
    post_link = post["link"]
    post_content = post["desc"]

    last_seen_id = get_last_seen_id()

    # 首次运行或有新帖子时触发
    if last_seen_id is None:
        print(f"首次初始化运行，记录最新帖子为: {post_id}")
        save_last_seen_id(post_id)
        print("首次测试：正在发送微信通知...")
        send_wechat_notice("测试推送: " + post_title, post_content, post_link)
    elif last_seen_id != post_id:
        print("发现新动态，正在推送到微信...")
        send_wechat_notice(post_title, post_content, post_link)
        save_last_seen_id(post_id)
    else:
        print("暂无新动态。")

if __name__ == "__main__":
    main()
