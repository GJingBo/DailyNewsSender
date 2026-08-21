import requests
import os
import re

def get_news_data():
    """获取新闻数据（使用默认JSON格式）"""
    #url = "https://60s.viki.moe/v2/60s"
    url = "http://excerpt.rubaoo.com/toolman/getMiniNews?"
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        print(f"✅ API请求成功，状态码: {response.status_code}")

        if "data" in data and isinstance(data["data"], dict):
            # 可选：打印所有字段名，方便调试
            # print("API返回的字段:", list(data["data"].keys()))
            return data["data"]
        else:
            print("❌ API返回结构异常，未找到data字段")
            print("完整响应:", data)
            return None
    except Exception as e:
        print(f"❌ 获取新闻失败: {e}")
        return None

def build_news_text(news_data):
    """构造完美排版早报（兼容 tip 和 weiyu 字段）"""
    if not news_data:
        return ""
    
    date = news_data.get("date", "")
    # 🔥 修复：微语字段名为 tip，兼容旧名 weiyu
    weiyu = news_data.get("tip") or news_data.get("weiyu", "")
    news_list = news_data.get("news", [])
    
    # 标题区
    text = f"📰 【每日早报】{date}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # 新闻区
    for idx, news in enumerate(news_list, 1):
        clean_news = re.sub(r'^\d+、', '', news).rstrip("；").strip()
        text += f"🔹 {idx}、{clean_news}\n\n"
    
    # 微语区
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if weiyu:
        # API 返回的 tip 本身不带 "【微语】" 前缀，所以直接拼接
        text += f"💬 【微语】{weiyu}"
    else:
        text += "💬 【微语】今日无特别微语，愿你保持好心情~"
    
    return text

def send_text_to_wecom(text, webhook_url):
    """企业微信文字推送"""
    try:
        payload = {
            "msgtype": "text",
            "text": {
                "content": text
            }
        }
        resp = requests.post(webhook_url, json=payload, timeout=15)
        result = resp.json()

        if result.get("errcode") == 0:
            print("✅ 企业微信文字推送成功！")
            return True
        else:
            print(f"❌ 推送失败，错误码: {result.get('errcode')}, 错误信息: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"❌ 推送异常: {e}")
        return False

# ========== 主程序 ==========
if __name__ == "__main__":
    WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")

    print("🚀 开始执行每日新闻推送...")
    news_data = get_news_data()

    if news_data:
        news_text = build_news_text(news_data)
        print(f"✅ 成功构造{len(news_data.get('news', []))}条新闻早报")

        # 本地测试模式：有 Webhook 则发送，否则只打印
        if WECHAT_WEBHOOK:
            send_text_to_wecom(news_text, WECHAT_WEBHOOK)
        else:
            print("\n" + "=" * 50)
            print("📝 【本地测试模式】未设置 WECHAT_WEBHOOK，仅打印新闻内容：")
            print("=" * 50)
            print(news_text)
            print("=" * 50 + "\n")
    else:
        print("❌ 获取新闻数据失败，程序结束")

    print("✅ 执行完成")
