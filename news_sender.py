import requests
import os
import re  # 移到顶部

def get_news_data():
    """获取新闻数据（修正URL，使用JSON格式）"""
    # ✅ 去掉 ?encoding=text，使用默认 JSON 格式
    url = "https://60s.viki.moe/v2/60s"
    # url = "http://excerpt.rubaoo.com/toolman/getMiniNews?"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.6031.113 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()  # 现在可以正常解析JSON了
        print(f"✅ API请求成功，状态码: {response.status_code}")

        # 检查返回结构是否包含 data 字段
        if "data" in data and isinstance(data["data"], dict):
            return data["data"]
        else:
            print("❌ API返回结构异常，未找到data字段")
            print("完整响应:", data)  # 调试输出
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
    
    # ===================== 新闻区 =====================
    for idx, news in enumerate(news_list, 1):
        # 去除API自带的序号（如果有）
        clean_news = re.sub(r'^\d+、', '', news).rstrip("；").strip()
        text += f"🔹 {idx}、{clean_news}\n\n"
    
    # ===================== 微语区 =====================
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
    # 从环境变量读取 Webhook（GitHub Actions 中设置）
    WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")
    if not WECHAT_WEBHOOK:
        print("❌ 错误：未设置环境变量 WECHAT_WEBHOOK")
        exit(1)

    print("🚀 开始执行每日新闻推送...")
    news_data = get_news_data()

    if news_data:
        news_text = build_news_text(news_data)
        print(f"✅ 成功构造{len(news_data.get('news', []))}条新闻早报")
        send_text_to_wecom(news_text, WECHAT_WEBHOOK)
    else:
        print("❌ 获取新闻数据失败，程序结束")

    print("✅ 执行完成")
