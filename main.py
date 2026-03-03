#!/usr/bin/env python3
"""AI 资讯机器人 - 完整版本（含 Word 深度分析报告）"""

import feedparser
import requests
import json
from datetime import datetime
from collections import Counter
import hashlib
import logging
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入深度分析报告模块
from src.reporters.deep_analysis_report import DeepAnalysisReport

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 飞书 Webhook 配置
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/98fe5f02-3851-46d2-8155-a40e71d90ea3"

# 资讯源配置（按优先级和分类排序）
SOURCES = [
    # ========== 官方动态（最高优先级，第一手信息）==========
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "priority": 12, "category": "Official"},
    {"name": "Google DeepMind", "url": "https://deepmind.com/blog/feed/basic", "priority": 12, "category": "Official"},
    {"name": "Meta AI", "url": "https://ai.meta.com/blog/feed/", "priority": 11, "category": "Official"},
    {"name": "Anthropic", "url": "https://www.anthropic.com/news/rss", "priority": 11, "category": "Official"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/rss", "priority": 10, "category": "LLM"},
    
    # ========== 中文媒体（快速报道）==========
    {"name": "量子位", "url": "https://www.qbitai.com/feed", "priority": 10, "category": "Chinese"},
    {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss", "priority": 9, "category": "Chinese"},
    {"name": "新智元", "url": "https://rss.sourcegraph.com/newswire", "priority": 9, "category": "Chinese"},
    {"name": "AI前线", "url": "https://www.infoq.cn/topic/AI", "priority": 8, "category": "Chinese"},
    
    # ========== 国际媒体（技术深度）==========
    {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/feed/", "priority": 9, "category": "Media"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/", "priority": 8, "category": "Media"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "priority": 8, "category": "Media"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "priority": 7, "category": "Media"},
    
    # ========== 技术社区（开发者视角）==========
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage", "priority": 7, "category": "Community", "max_items": 8},
    {"name": "Reddit r/MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/.rss", "priority": 6, "category": "Community", "max_items": 6},
    {"name": "AI News", "url": "https://artificialintelligence-news.com/feed/", "priority": 6, "category": "Media"},
]

# Word 报告配置
ENABLE_WORD_REPORT = True  # 是否生成 Word 报告
WORD_REPORT_FILE = "AI_深度分析报告.docx"

def collect_news():
    """采集资讯"""
    all_news = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    logger.info("开始采集资讯...")

    for source in SOURCES:
        try:
            logger.info(f"📡 采集: {source['name']}")
            response = requests.get(source['url'], headers=headers, timeout=30)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            for entry in feed.entries[:10]:
                news = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', ''))[:200],
                    'source': source['name'],
                    'priority': source['priority']
                }

                if news['title'] and news['link']:
                    all_news.append(news)

            logger.info(f"  ✓ 获取 {len(feed.entries[:10])} 条")

        except Exception as e:
            logger.error(f"  ✗ 失败: {str(e)}")
            continue

    logger.info(f"✓ 采集完成，共获取 {len(all_news)} 条资讯")
    return all_news

def process_news(news_list):
    """处理资讯：去重、评分、分类"""
    logger.info("开始处理资讯...")

    # 去重
    seen = set()
    unique_news = []

    for news in news_list:
        title_hash = hashlib.md5(news['title'].lower().encode()).hexdigest()
        if title_hash not in seen:
            seen.add(title_hash)

            # 评分
            score = news['priority']

            # 标题包含热词加分
            hot_keywords = ['发布', '突破', '重磅', '最新', 'launch', 'release', 'breakthrough']
            for keyword in hot_keywords:
                if keyword in news['title']:
                    score += 3
                    break

            # 提及重要公司加分
            important_companies = ['OpenAI', 'DeepSeek', 'Google', 'Microsoft', 'Meta']
            for company in important_companies:
                if company in news['title']:
                    score += 2
                    break

            # 简单分类
            news['category'] = classify_news(news)
            news['score'] = score
            unique_news.append(news)

    logger.info(f"✓ 去重后剩余 {len(unique_news)} 条")

    # 按分数排序
    unique_news.sort(key=lambda x: x['score'], reverse=True)

    # 限制数量
    result = unique_news[:12]

    logger.info(f"✓ 处理完成，推送 {len(result)} 条资讯")
    return result

def classify_news(news):
    """简单分类"""
    title = news['title'].lower()
    summary = news.get('summary', '').lower()
    text = f"{title} {summary}"
    
    keywords = {
        'LLM': ['gpt', 'llm', '大模型', 'transformer', 'language model'],
        'Agent': ['agent', '智能体', 'autonomous'],
        'AI Tool': ['工具', 'tool', 'api', 'sdk'],
        'Research': ['paper', '论文', '研究', '发布'],
        'Industry': ['公司', '融资', '投资', '企业']
    }
    
    for category, kw_list in keywords.items():
        for keyword in kw_list:
            if keyword in text:
                return category
    
    return 'General'

def generate_word_report(news_list, output_file):
    """生成 Word 深度分析报告"""
    if not ENABLE_WORD_REPORT:
        logger.info("Word 报告生成功能已禁用")
        return None
    
    try:
        logger.info("正在生成 Word 深度分析报告...")
        report_generator = DeepAnalysisReport(news_list)
        report_file = report_generator.generate(output_file)
        logger.info(f"✓ Word 报告已生成: {report_file}")
        return report_file
    except Exception as e:
        logger.error(f"✗ Word 报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def send_to_feishu(news_list, word_report_file=None):
    """发送到飞书"""
    if not news_list:
        logger.warning("⚠️ 没有资讯可发送")
        return False

    logger.info("正在构建飞书消息卡片...")

    # 统计数据
    category_stats = Counter([n.get('category', 'Other') for n in news_list])

    # 构建卡片
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"📰 AI 资讯日报 - {datetime.now().strftime('%Y年%m月%d日')}"
            },
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"### 📊 今日数据概览\n\n"
                               f"• **采集总数**: {len(news_list)} 条\n"
                               f"• **来源数**: {len(set(n['source'] for n in news_list))} 个\n"
                               f"• **分类数**: {len(category_stats)} 个\n"
                               f"• **Word 报告**: {'✅ 已生成' if word_report_file else '❌ 未生成'}\n\n"
                               f"### 🔥 今日热门资讯\n\n"
                }
            }
        ]
    }

    # 添加新闻列表
    for i, news in enumerate(news_list, 1):
        # 截断标题
        title = news['title']
        if len(title) > 45:
            title = title[:45] + '...'

        # 格式化摘要
        summary = news['summary']
        if summary and len(summary) > 80:
            summary = summary[:80] + '...'

        # 添加新闻项
        news_element = {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{i}. **{title}**\n"
                           f"   📌 来源: {news['source']}\n"
                           f"   📅 分类: {news.get('category', '未分类')}\n"
                           f"   📈 评分: {news['score']}\n"
        }
        }

        if summary:
            news_element["text"]["content"] += f"   📝 {summary}\n"

        news_element["text"]["content"] += f"   🔗 [查看详情]({news['link']})\n\n"

        card["elements"].append(news_element)

        # 添加分隔线（最后一条除外）
        if i < len(news_list):
            card["elements"].append({"tag": "hr"})

    # 如果有 Word 报告，添加下载提示
    if word_report_file:
        card["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"\n📄 **深度分析报告**: Word 报告已生成，包含热点话题分析、重要资讯解读、趋势分析和行动建议。\n\n请在 GitHub Actions Artifacts 中下载完整报告。"
            }
        })

    # 添加底部信息
    card["elements"].append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"_推送时间: {datetime.now().strftime('%H:%M:%S')} | AI 资讯机器人 © {datetime.now().year}_"
        }
    })

    logger.info("正在发送到飞书...")

    try:
        response = requests.post(
            FEISHU_WEBHOOK,
            json={"msg_type": "interactive", "card": card},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if result.get('code') == 0:
            logger.info("✅ 推送成功！")
            return True
        else:
            logger.error(f"❌ 推送失败: {result}")
            return False

    except Exception as e:
        logger.error(f"❌ 发送异常: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🤖 AI 资讯机器人启动（含 Word 深度分析）")
    logger.info("=" * 60)

    word_report_file = None

    try:
        # 第一步：采集资讯
        logger.info("\n📡 步骤 1/4: 采集资讯")
        news = collect_news()

        if not news:
            logger.warning("未采集到任何资讯，程序退出")
            return

        # 第二步：处理资讯
        logger.info("\n⚙️  步骤 2/4: 处理资讯")
        processed_news = process_news(news)

        # 第三步：生成 Word 深度分析报告
        if ENABLE_WORD_REPORT:
            logger.info("\n📄 步骤 3/4: 生成 Word 深度分析报告")
            word_report_file = generate_word_report(processed_news, WORD_REPORT_FILE)

        # 第四步：推送资讯
        logger.info("\n📊 步骤 4/4: 推送资讯")
        success = send_to_feishu(processed_news, word_report_file)

        if success:
            logger.info("\n✅ 今日资讯推送完成！")
        else:
            logger.error("\n❌ 推送失败，请检查配置")

        # 输出统计信息
        logger.info("\n" + "=" * 60)
        logger.info("📈 数据统计")
        logger.info("=" * 60)

        source_stats = Counter([n['source'] for n in processed_news])
        category_stats = Counter([n.get('category', 'Other') for n in processed_news])
        
        logger.info("\n来源统计:")
        for source, count in source_stats.most_common():
            logger.info(f"  {source}: {count} 条")
        
        logger.info("\n分类统计:")
        for category, count in category_stats.most_common():
            logger.info(f"  {category}: {count} 条")
        
        if word_report_file:
            logger.info(f"\nWord 报告: {word_report_file}")

    except Exception as e:
        logger.error(f"\n❌ 程序运行出错: {str(e)}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("🎉 运行完成！")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
