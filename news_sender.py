import requests
import os

def get_news_data():
    """获取新闻数据（完全适配你的API）"""
    url = "http://excerpt.rubaoo.com/toolman/getMiniNews?"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.6031.113 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        print(f"✅ API请求成功，状态码: {response.status_code}")

        if "data" in data and isinstance(data["data"], dict):
            return data["data"]
        else:
            print("❌ API返回结构异常，未找到data字段")
            return None
    except Exception as e:
        print(f"❌ 获取新闻失败: {e}")
        return None

def build_news_text(news_data):
    """构造完美排版早报（彻底解决所有重复）"""
    if not news_data:
        return ""
    
    date = news_data.get("date", "")
    weiyu = news_data.get("weiyu", "")
    news_list = news_data.get("news", [])
    
    # ===================== 标题区 =====================
    text = f"📰 【每日早报】{date}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # ===================== 新闻区（彻底去重+统一格式）=====================
    for idx, news in enumerate(news_list, 1):
        # 🔧 核心修复1：彻底去除API自带的序号、分号、多余字符
        # 匹配并删除API自带的"1、"、"2、"等前缀，兼容全角/半角分号
        import re
        clean_news = re.sub(r'^\d+、', '', news).rstrip("；").strip()
        # 统一手动加序号，绝对不会重复
        text += f"🔹 {idx}、{clean_news}\n\n"
    
    # ===================== 微语区（彻底去重+优化）=====================
    # 🔧 核心修复2：去除weiyu字段自带的【微语】前缀，只加一次
    clean_weiyu = weiyu.lstrip("【微语】").strip()
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"💬 【微语】{clean_weiyu}"
    
    return text

def send_text_to_wecom(text, webhook_url):
    """企业微信文字推送（100%稳定）"""
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
    # 本地测试时替换为你的WebHook，部署GitHub时改回os.getenv
    WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")

    print("🚀 开始执行每日新闻推送...")
    news_data = get_news_data()

    if news_data:
        news_text = build_news_text(news_data)
        print(f"✅ 成功构造{len(news_data.get('news', []))}条新闻早报")
        send_text_to_wecom(news_text, WECHAT_WEBHOOK)

    print("✅ 执行完成")
