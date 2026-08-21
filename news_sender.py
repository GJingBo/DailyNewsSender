import requests
import os
import re

def try_fetch_news(url, headers, timeout=20):
    """
    尝试从单个API获取新闻数据。
    返回 (news_data, error_msg)，news_data为成功提取的data字段，若失败则为None。
    """
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"

        data = resp.json()
        # 尝试提取 data 字段（兼容主API的 {"code":200, "data":{...}} 和备用API的 {"success":1, "data":{...}}）
        news_data = data.get("data")
        if not news_data or not isinstance(news_data, dict):
            return None, "缺少data字段或类型错误"

        # 检查 news 列表是否存在且非空
        news_list = news_data.get("news")
        if not isinstance(news_list, list) or len(news_list) == 0:
            return None, "news列表为空或类型错误"

        # 若存在 weiyu 字段，统一映射为 tip（便于后续处理）
        if "weiyu" in news_data and "tip" not in news_data:
            news_data["tip"] = news_data["weiyu"]

        return news_data, None

    except requests.exceptions.RequestException as e:
        return None, f"网络异常: {e}"
    except ValueError as e:
        return None, f"JSON解析错误: {e}"
    except Exception as e:
        return None, f"未知错误: {e}"


def get_news_data():
    """
    尝试多个API，直到获取到有效的新闻数据。
    返回 (news_data, error_summary)，news_data为成功提取的数据，失败时为None。
    error_summary为所有API失败时的汇总错误信息。
    """
    # 按优先级排列的API列表（主域名不可用，暂不添加）
    api_urls = [
        "https://60s.crystelf.top/v2/60s",
        "https://api.elysiayanyu.top/v2/60s",
        "https://api.cczo.cc/60s/v2/60s",
        "https://60s.zellon.top/v2/60s",
        "https://60s.superjeason.qzz.io/v2/60s",
        "http://excerpt.rubaoo.com/toolman/getMiniNews?",  # 备用API
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
    }

    errors = []  # 记录每个API的失败原因

    for idx, url in enumerate(api_urls, 1):
        print(f"🔄 尝试 API #{idx}: {url}")
        news_data, err = try_fetch_news(url, headers)

        if news_data is not None:
            print(f"✅ 成功从 {url} 获取新闻，共 {len(news_data.get('news', []))} 条")
            return news_data, None  # 成功，返回数据

        # 失败则记录错误
        error_msg = f"API #{idx} ({url}) 失败: {err}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)

    # 所有API均失败
    error_summary = "所有新闻源均不可用。\n" + "\n".join(errors)
    print(f"❌ {error_summary}")
    return None, error_summary


def build_news_text(news_data):
    """构造完美排版早报（兼容 tip 和 weiyu 字段）"""
    if not news_data:
        return ""

    date = news_data.get("date", "")
    weiyu = news_data.get("tip") or news_data.get("weiyu", "")
    news_list = news_data.get("news")

    # 确保 news_list 是列表
    if not isinstance(news_list, list):
        news_list = []
        print("⚠️ 警告：news字段不是列表，已置空")

    # 标题区
    text = f"📰 【每日早报】{date}\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # 新闻区（自动去除可能自带的序号）
    for idx, news in enumerate(news_list, 1):
        if not isinstance(news, str):
            news = str(news)
        clean_news = re.sub(r'^\d+、', '', news).rstrip("；").strip()
        text += f"🔹 {idx}、{clean_news}\n\n"

    # 微语区
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if weiyu:
        # 去除可能自带的 "【微语】" 前缀，避免重复
        clean_weiyu = weiyu.lstrip("【微语】").strip()
        text += f"💬 【微语】{clean_weiyu}"
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

    # 获取新闻（同时获取错误摘要）
    news_data, error_summary = get_news_data()

    if news_data:
        # 成功获取，构造并发送/打印
        news_text = build_news_text(news_data)
        news_count = len(news_data.get("news", [])) if isinstance(news_data.get("news"), list) else 0
        print(f"✅ 成功构造 {news_count} 条新闻早报")

        if WECHAT_WEBHOOK:
            send_text_to_wecom(news_text, WECHAT_WEBHOOK)
        else:
            print("\n" + "=" * 50)
            print("📝 【本地测试模式】未设置 WECHAT_WEBHOOK，仅打印新闻内容：")
            print("=" * 50)
            print(news_text)
            print("=" * 50 + "\n")
    else:
        # 所有API均失败
        print("❌ 获取新闻数据失败，程序结束")
        if WECHAT_WEBHOOK:
            # 发送错误通知（限制长度，避免超限）
            error_notice = f"⚠️ 新闻推送失败\n\n{error_summary[:200]}{'……' if len(error_summary)>200 else ''}"
            print("📤 尝试发送错误通知到企业微信……")
            send_text_to_wecom(error_notice, WECHAT_WEBHOOK)
        else:
            print("\n" + "=" * 50)
            print("📝 【本地测试模式】错误详情：")
            print(error_summary)
            print("=" * 50 + "\n")

    print("✅ 执行完成")
