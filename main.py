#!/usr/bin/env python3
"""AI 资讯机器人 - 完整单文件版本"""

import feedparser
import requests
import json
from datetime import datetime
from collections import Counter
import hashlib

# 配置
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/98fe5f02-3851-46d2-8155-a40e71d90ea3"

SOURCES = [
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "priority": 10},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "priority": 8},
]

def collect_news():
    """采集资讯"""
    all_news = []
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    for source in SOURCES:
        try:
            print(f"📡 采集: {source['name']}")
            response = requests.get(source['url'], headers=headers, timeout=30)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                news = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', '')[:200],
                    'source': source['name'],
                    'priority': source['priority']
                }
                if news['title'] and news['link']:
                    all_news.append(news)
            print(f"  ✓ 获取 {len(feed.entries[:10])} 条")
        except Exception as e:
            print(f"  ✗ 失败: {str(e)}")
    
    return all_news

def process_news(news_list):
    """处理资讯：去重、评分"""
    # 去重
    seen = set()
    unique_news = []
    for news in news_list:
        title_hash = hashlib.md5(news['title'].lower().encode()).hexdigest()
        if title_hash not in seen:
            seen.add(title_hash)
            # 评分
            score = news['priority']
            if '发布' in news['title'] or '发布' in news['title']:
                score += 5
            if 'OpenAI' in news['title'] or 'DeepSeek' in news['title']:
                score += 3
            news['score'] = score
            unique_news.append(news)
    
    # 按分数排序
    unique_news.sort(key=lambda x: x['score'], reverse=True)
    return unique_news[:10]

def send_to_feishu(news_list):
    """发送到飞书"""
    if not news_list:
        print("⚠️ 没有资讯可发送")
        return
    
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"📰 AI 资讯日报 - {datetime.now().strftime('%Y-%m-%d')}"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**今日数据概览**\n\n• 采集总数: {len(news_list)} 条\n• 来源数: {len(set(n['source'] for n in news_list))} 个\n\n**🔥 热门资讯**\n\n"
                }
            }
        ]
    }
    
    for i, news in enumerate(news_list, 1):
        title = news['title'][:40] + '...' if len(news['title']) > 40 else news['title']
        card["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{i}.  **{title}** \n   来源: {news['source']}\n   [查看详情]({news['link']})\n\n"
            }
        })
    
    try:
        response = requests.post(FEISHU_WEBHOOK, json={"msg_type": "interactive", "card": card})
        result = response.json()
        if result.get('code') == 0:
            print("✅ 推送成功！")
        else:
            print(f"❌ 推送失败: {result}")
    except Exception as e:
        print(f"❌ 发送异常: {e}")

def main():
    print("=" * 50)
    print("🤖 AI 资讯机器人启动")
    print("=" * 50)
    
    news = collect_news()
    print(f"\n📊 共采集 {len(news)} 条资讯")
    
    processed = process_news(news)
    print(f"⚙️  处理后剩余 {len(processed)} 条有效资讯")
    
    print("\n📤 正在推送到飞书...")
    send_to_feishu(processed)
    
    print("\n" + "=" * 50)
    print("🎉 运行完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
