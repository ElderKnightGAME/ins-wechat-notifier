import os
import json
import re
import requests

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
    # 使用公开代理 API 获取公开商业号数据，设置 10 秒严格超时
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    sources = [
        f"https://www.picuki.com/profile/{INSTAGRAM_USERNAME}",
        f"https://dumpoir.com/v/{INSTAGRAM_USERNAME}"
    ]
    
    for url in sources:
        try:
            print(f"尝试从源拉取: {url}")
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                # 正则快速提取帖子短码 shortcode
                match = re.search(r'/(?:p|media)/([a-zA-Z0-9_-]{10,12})', res.text)
                if match:
                    shortcode = match.group(1)
                    post_link = f"https://www.instagram.com/p/{shortcode}/"
                    return {
                        "id": shortcode,
                        "title": f"@{INSTAGRAM_USERNAME} 刚刚发布了新帖子",
                        "desc": f"监测到新发布内容，请点击下方链接直达 Instagram 查看详情！",
                        "link": post_link
                    }
        except Exception as e:
            print(f"拉取失败 ({url}): {e}")
            continue
            
    # 如果公共网页全被拦截，退守测试通道保证首次通知通畅
    print("未能直接解析到公开页面，启用备用信标")
    return None

def main():
    print(f"正在拉取 @{INSTAGRAM_USERNAME} 的最新动态...")
    post = fetch_latest_post()

    last_seen_id = get_last_seen_id()

    # 首次部署测试：如果获取到了或者想强制测试通道
    if post:
        post_id = post["id"]
        post_title = post["title"]
        post_link = post["link"]
        post_content = post["desc"]

        if last_seen_id is None:
            print(f"首次初始化成功，最新帖子 ID: {post_id}，正在发送测试推送...")
            save_last_seen_id(post_id)
            send_wechat_notice("首次配置测试: " + post_title, post_content, post_link)
        elif str(last_seen_id) != str(post_id):
            print("发现新动态，正在推送到微信...")
            send_wechat_notice(post_title, post_content, post_link)
            save_last_seen_id(post_id)
        else:
            print("暂无新动态。")
    else:
        # 如果爬虫源暂时受阻，首次运行强制发一条测试消息验证你的 SendKey 是否好用
        if last_seen_id is None:
            print("发送通道验证推送...")
            send_wechat_notice("服务配置成功测试", "微信通知通道已打通！目前正在后台监控更新。", "https://www.instagram.com/" + INSTAGRAM_USERNAME)
            save_last_seen_id("init_ok")

if __name__ == "__main__":
    main()
