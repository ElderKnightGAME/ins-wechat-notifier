import os
import json
import requests
import instaloader

# ================= 配置项 =================
INSTAGRAM_USERNAME = "kith"
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
    try:
        resp = requests.post(api_url, data=data, timeout=10)
        print("微信推送响应:", resp.json())
    except Exception as e:
        print("推送请求异常:", e)

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
        json.dump({"last_id": str(post_id)}, f)

def fetch_latest_post():
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False
    )
    
    try:
        profile = instaloader.Profile.from_username(L.context, INSTAGRAM_USERNAME)
        # 获取第一条最新帖子
        for post in profile.get_posts():
            caption = post.caption if post.caption else "发布了新动态"
            title = caption.split("\n")[0][:40]
            link = f"https://www.instagram.com/p/{post.shortcode}/"
            img_url = post.url
            
            return {
                "id": post.mediaid,
                "title": title,
                "desc": f"![封面]({img_url})\n\n{caption[:300]}...",
                "link": link
            }
        return None
    except Exception as e:
        print(f"获取动态异常: {e}")
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

    # 首次运行或有新动态时推送到微信
    if last_seen_id is None:
        print(f"首次初始化运行，记录最新帖子为: {post_id}")
        save_last_seen_id(post_id)
        print("首次测试：正在发送微信通知...")
        send_wechat_notice("测试推送: " + post_title, post_content, post_link)
    elif str(last_seen_id) != str(post_id):
        print("发现新动态，正在推送到微信...")
        send_wechat_notice(post_title, post_content, post_link)
        save_last_seen_id(post_id)
    else:
        print("暂无新动态。")

if __name__ == "__main__":
    main()
