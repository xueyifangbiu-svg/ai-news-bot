# AI 资讯机器人 - Mac 用户完整部署包

> 📅 创建时间：2026年03月02日
> 🎯 目标：每天自动采集 AI 行业资讯，生成分析报告，并推送到飞书

---

## 🎉 恭喜！你已经完成了飞书机器人配置

**你的飞书 Webhook 地址**：`https://open.feishu.cn/open-apis/bot/v2/hook/98fe5f02-3851-46d2-8155-a40e71d90ea3`

现在按照以下步骤，5分钟内完成整个系统的部署！

---

## 📦 第一步：创建项目文件夹（1分钟）

在 Mac 上打开**终端**（Terminal），执行以下命令：

```bash
# 创建项目文件夹
cd ~
mkdir -p ai_news_bot
cd ai_news_bot

# 创建项目结构
mkdir -p src/collectors src/processors src/reporters config
```

---

## 📄 第二步：创建代码文件（3分钟）

### 1. 创建 RSS 采集器

```bash
cat > src/collectors/rss_collector.py << 'EOF'
"""
RSS 资讯采集器
从 RSS 订阅源采集最新资讯
"""

import feedparser
import requests
from datetime import datetime
from typing import List, Dict
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSCollector:
    """RSS 资讯采集器"""
    
    def __init__(self, sources: List[Dict]):
        self.sources = sources
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def collect_all(self) -> List[Dict]:
        """采集所有资讯源"""
        all_news = []
        logger.info(f"开始采集 {len(self.sources)} 个资讯源...")
        
        for i, source in enumerate(self.sources, 1):
            logger.info(f"[{i}/{len(self.sources)}] 采集: {source['name']}")
            try:
                news = self._collect_source(source)
                all_news.extend(news)
                logger.info(f"  ✓ 获取 {len(news)} 条资讯")
                time.sleep(1)
            except Exception as e:
                logger.error(f"  ✗ 采集失败: {str(e)}")
                continue
        
        logger.info(f"✓ 采集完成，共获取 {len(all_news)} 条资讯")
        return all_news
    
    def _collect_source(self, source: Dict) -> List[Dict]:
        """采集单个资讯源"""
        url = source['url']
        name = source.get('name', 'Unknown')
        category = source.get('category', 'Uncategorized')
        priority = source.get('priority', 5)
        max_items = source.get('max_items', 15)
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        news_list = []
        
        for entry in feed.entries[:max_items]:
            try:
                news = {
                    'title': entry.get('title', '').strip(),
                    'link': entry.get('link', ''),
                    'summary': self._clean_html(entry.get('summary', entry.get('description', ''))),
                    'published': datetime.now(),
                    'source': name,
                    'category': category,
                    'priority': priority,
                    'author': entry.get('author', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])]
                }
                
                if news['title'] and news['link']:
                    news_list.append(news)
            except Exception as e:
                continue
        
        return news_list
    
    def _clean_html(self, html: str) -> str:
        """清理 HTML 标签"""
        if not html:
            return ''
        
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        clean = clean.strip()
        
        if len(clean) > 500:
            clean = clean[:500] + '...'
        
        return clean
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
EOF
```

### 2. 创建资讯处理器

```bash
cat > src/processors/news_processor.py << 'EOF'
"""
资讯处理器
对采集的资讯进行去重、分类、评分等处理
"""

import logging
from datetime import datetime
from typing import List, Dict
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsProcessor:
    """资讯处理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.enable_dedup = self.config.get('enable_deduplication', True)
        self.enable_categorization = self.config.get('enable_categorization', True)
    
    def process(self, news_list: List[Dict]) -> List[Dict]:
        """处理资讯列表"""
        if not news_list:
            return []
        
        logger.info(f"开始处理 {len(news_list)} 条资讯...")
        
        # 1. 去重
        if self.enable_dedup:
            news_list = self._deduplicate(news_list)
            logger.info(f"  ✓ 去重后剩余 {len(news_list)} 条")
        
        # 2. 分类
        if self.enable_categorization:
            news_list = self._categorize(news_list)
            logger.info(f"  ✓ 分类完成")
        
        # 3. 评分和排序
        news_list = self._score_and_sort(news_list)
        logger.info(f"  ✓ 评分和排序完成")
        
        return news_list
    
    def _deduplicate(self, news_list: List[Dict]) -> List[Dict]:
        """去除重复资讯"""
        seen_titles = set()
        seen_urls = set()
        unique_news = []
        
        for news in news_list:
            title_key = news['title'].lower().strip()
            title_hash = hashlib.md5(title_key.encode()).hexdigest()
            url_hash = hashlib.md5(news['link'].encode()).hexdigest()
            
            if title_hash not in seen_titles and url_hash not in seen_urls:
                seen_titles.add(title_hash)
                seen_urls.add(url_hash)
                unique_news.append(news)
        
        return unique_news
    
    def _categorize(self, news_list: List[Dict]) -> List[Dict]:
        """对资讯进行分类"""
        category_keywords = {
            'LLM': ['gpt', 'llm', '大模型', 'transformer', 'bert', 'claude', 'gemini', 
                   'language model', '语言模型', 'openai', 'deepseek'],
            'Agent': ['agent', '智能体', 'autogen', 'crewai', 'multi-agent', '代理'],
            'AI Tool': ['工具', 'tool', 'api', 'sdk', 'framework', 'library', '开源'],
            'Research': ['paper', '论文', '研究', 'arxiv', '发布', '突破'],
            'Industry': ['公司', '融资', '投资', '收购', '企业', '财报', '业务'],
            'Application': ['应用', '落地', '场景', '案例', '产品', '发布'],
        }
        
        for news in news_list:
            title = news['title'].lower()
            summary = news['summary'].lower()
            text = f"{title} {summary}"
            
            matched_categories = []
            for category, keywords in category_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        matched_categories.append(category)
                        break
            
            if matched_categories:
                news['ai_category'] = matched_categories[0]
                news['all_categories'] = matched_categories
            else:
                news['ai_category'] = news.get('category', 'General')
                news['all_categories'] = [news['ai_category']]
        
        return news_list
    
    def _score_and_sort(self, news_list: List[Dict]) -> List[Dict]:
        """对资讯进行评分和排序"""
        for news in news_list:
            score = 0
            score += news.get('priority', 5) * 2
            
            hot_keywords = ['发布', '突破', '重磅', '最新', 'launch', 'release', 
                          'breakthrough', 'announces', 'unveils']
            for keyword in hot_keywords:
                if keyword in news['title']:
                    score += 3
            
            if len(news['summary']) > 100:
                score += 2
            
            if news['source'] in ['OpenAI Blog', 'Google DeepMind', 'MIT Technology Review']:
                score += 5
            
            news['score'] = score
        
        news_list.sort(key=lambda x: x['score'], reverse=True)
        return news_list
EOF
```

### 3. 创建飞书报告生成器

```bash
cat > src/reporters/feishu_reporter.py << 'EOF'
"""
飞书报告生成器
生成并向飞书推送资讯报告
"""

import requests
import json
import logging
from datetime import datetime
from typing import List, Dict
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeishuReporter:
    """飞书报告生成器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()
    
    def send_daily_report(self, news_list: List[Dict], max_news: int = 10) -> bool:
        """发送每日报告"""
        if not news_list:
            logger.warning("没有资讯需要推送")
            return False
        
        top_news = news_list[:max_news]
        card = self._build_daily_report_card(top_news, news_list)
        return self._send_card(card)
    
    def _build_daily_report_card(self, top_news: List[Dict], all_news: List[Dict]) -> Dict:
        """构建每日报告卡片"""
        total_count = len(all_news)
        category_stats = Counter([news.get('ai_category', 'Other') for news in all_news])
        source_stats = Counter([news['source'] for news in all_news])
        
        # 统计信息
        stats_text = f"📊 **今日数据概览**\n\n"
        stats_text += f"• 采集总数：{total_count} 条\n"
        
        if category_stats:
            stats_text += "• 分类统计：\n"
            for cat, count in category_stats.most_common(5):
                stats_text += f"  - {cat}: {count} 条\n"
        
        # 热门资讯
        news_text = f"\n🔥 **今日热门资讯**\n\n"
        
        for i, news in enumerate(top_news, 1):
            emoji = self._get_emoji_by_category(news.get('ai_category', ''))
            
            title = news['title']
            if len(title) > 40:
                title = title[:40] + '...'
            
            news_text += f"{i}. {emoji} **{title}**\n"
            news_text += f"   来源: {news['source']}\n"
            
            summary = news['summary']
            if summary:
                if len(summary) > 60:
                    summary = summary[:60] + '...'
                news_text += f"   {summary}\n"
            
            news_text += f"   [查看详情]({news['link']})\n\n"
        
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
                        "content": stats_text
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": news_text
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"_推送时间: {datetime.now().strftime('%H:%M:%S')}_"
                    }
                }
            ]
        }
        
        return card
    
    def _get_emoji_by_category(self, category: str) -> str:
        """根据分类返回对应 emoji"""
        emoji_map = {
            'LLM': '🤖',
            'Agent': '🎯',
            'AI Tool': '🛠️',
            'Research': '🔬',
            'Industry': '💼',
            'Application': '🚀',
            'Chinese': '🇨🇳',
            'Official': '🏢',
            'Media': '📺'
        }
        return emoji_map.get(category, '📄')
    
    def _send_card(self, card: Dict) -> bool:
        """发送卡片到飞书"""
        message = {
            "msg_type": "interactive",
            "card": card
        }
        
        try:
            logger.info("正在发送报告到飞书...")
            response = self.session.post(self.webhook_url, json=message, timeout=10)
            result = response.json()
            
            if result.get('code') == 0:
                logger.info("✓ 报告发送成功")
                return True
            else:
                logger.error(f"✗ 报告发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"✗ 发送异常: {str(e)}")
            return False
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
EOF
```

### 4. 创建配置文件

```bash
cat > config/config.py << 'EOF'
# AI 资讯机器人配置文件

# 飞书机器人配置
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/98fe5f02-3851-46d2-8155-a40e71d90ea3"

# 资讯源配置
NEWS_SOURCES = [
    # 官方动态
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category": "Official",
        "priority": 10
    },
    {
        "name": "Google DeepMind",
        "url": "https://deepmind.com/blog/feed/basic",
        "category": "Official",
        "priority": 10
    },
    
    # 技术媒体
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/feed/",
        "category": "Media",
        "priority": 8
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "category": "Media",
        "priority": 7
    },
    
    # 中文媒体
    {
        "name": "量子位",
        "url": "https://www.qbitai.com/feed",
        "category": "Chinese",
        "priority": 9
    },
    {
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com/rss",
        "category": "Chinese",
        "priority": 9
    },
    
    # 开发者社区
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "category": "Community",
        "priority": 6,
        "max_items": 8
    },
]

# 采集配置
COLLECTOR_CONFIG = {
    "timeout": 30,
    "max_items_per_source": 15,
    "retry_times": 3,
}

# 处理配置
PROCESSOR_CONFIG = {
    "enable_deduplication": True,
    "enable_categorization": True,
}

# 推送配置
PUSH_CONFIG = {
    "daily_push_time": "09:00",
    "max_daily_news": 12,
}
EOF
```

### 5. 创建主程序

```bash
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
AI 资讯机器人 - 主程序
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.collectors.rss_collector import RSSCollector
from src.processors.news_processor import NewsProcessor
from src.reporters.feishu_reporter import FeishuReporter
from config.config import FEISHU_WEBHOOK, NEWS_SOURCES

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 AI 资讯机器人启动")
    print("=" * 60)
    
    try:
        # 1. 采集资讯
        print("\n📡 步骤 1/3: 采集资讯...")
        collector = RSSCollector(NEWS_SOURCES)
        news_list = collector.collect_all()
        print(f"✓ 采集完成，共获取 {len(news_list)} 条资讯")
        
        if not news_list:
            print("\n⚠️  未采集到任何资讯")
            return
        
        # 2. 处理资讯
        print("\n⚙️  步骤 2/3: 处理资讯...")
        processor = NewsProcessor()
        processed_news = processor.process(news_list)
        print(f"✓ 处理完成，剩余 {len(processed_news)} 条有效资讯")
        
        # 3. 生成报告
        print("\n📊 步骤 3/3: 生成并发送报告...")
        reporter = FeishuReporter(FEISHU_WEBHOOK)
        result = reporter.send_daily_report(processed_news, max_news=10)
        
        if result:
            print("✅ 报告推送成功！")
        else:
            print("❌ 报告推送失败")
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("📈 数据统计")
        print("=" * 60)
        
        from collections import Counter
        category_stats = Counter([n.get('ai_category', 'Other') for n in processed_news])
        print("\n分类统计:")
        for cat, count in category_stats.most_common():
            print(f"  {cat}: {count} 条")
        
    except Exception as e:
        print(f"\n❌ 程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 运行完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
EOF
```

### 6. 创建依赖文件

```bash
cat > requirements.txt << 'EOF'
feedparser>=6.0.10
requests>=2.31.0
python-dateutil>=2.8.2
EOF
```

### 7. 创建初始化文件

```bash
touch src/__init__.py
touch src/collectors/__init__.py
touch src/processors/__init__.py
touch src/reporters/__init__.py
touch config/__init__.py
```

---

## 🚀 第三步：安装依赖并运行（1分钟）

```bash
# 安装依赖
pip3 install -r requirements.txt

# 运行程序
python3 main.py
```

**预期结果**：
- 程序开始采集资讯
- 处理完成后，飞书群会收到推送
- 你会看到完整的运行日志

---

## 🔄 第四步：配置自动运行（GitHub Actions）

### 1. 创建 GitHub 仓库

访问 https://github.com/new，创建新仓库（例如：`ai-news-bot`）

### 2. 初始化 Git 并推送

```bash
# 初始化 Git
git init
git add .
git commit -m "Initial commit: AI News Bot"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的GitHub用户名/ai-news-bot.git

# 推送代码
git branch -M main
git push -u origin main
```

### 3. 创建 GitHub Actions 工作流

在 GitHub 仓库中创建 `.github/workflows/daily_news.yml`：

```yaml
name: Daily AI News Bot

on:
  schedule:
    - cron: '0 1 * * *'  # UTC 时间 01:00 = 北京时间 09:00
  workflow_dispatch:    # 允许手动触发

jobs:
  collect-and-push:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install feedparser requests python-dateutil beautifulsoup4 lxml
      
      - name: Run news collector
        run: python main.py
```

### 4. 提交并推送

```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push
```

**完成！** 从现在开始，每天北京时间 09:00，你的机器人会自动采集并推送 AI 资讯！

---

## ⚙️ 自定义配置

### 修改推送时间

编辑 `.github/workflows/daily_news.yml`，修改 cron 表达式：
```yaml
schedule:
  - cron: '0 2 * * *'  # 修改为你希望的时间（UTC）
```

### 添加更多资讯源

编辑 `config/config.py`，在 `NEWS_SOURCES` 中添加：
```python
{
    "name": "你的资讯源",
    "url": "https://example.com/feed.xml",
    "category": "分类",
    "priority": 8
}
```

### 修改每日推送数量

编辑 `config/config.py`：
```python
PUSH_CONFIG = {
    "max_daily_news": 15,  # 修改数量
}
```

---

## 🎯 快速启动脚本（可选）

如果你想在本地快速运行，创建 `run.sh`：

```bash
cat > run.sh << 'EOF'
#!/bin/bash
cd ~/ai_news_bot
python3 main.py
EOF

chmod +x run.sh
```

以后直接运行 `./run.sh` 即可。

---

## 📊 查看运行状态

### 本地运行
直接查看终端输出的日志

### GitHub Actions
1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 查看工作流运行记录和日志

---

## 🔧 常见问题

### Q: 为什么有些源抓取失败？
A: 网络问题或网站限制，检查日志文件

### Q: 如何修改推送时间？
A: 修改 `.github/workflows/daily_news.yml` 中的 cron 表达式

### Q: 推送失败怎么办？
A: 检查飞书 Webhook 地址是否正确，机器人是否在群中

---

## 🎉 完成！

现在你已经拥有了一个完整的 AI 资讯自动化系统！

每天自动：
- 📡 采集最新 AI 资讯
- ⚙️ 智能去重、分类、评分
- 📊 生成数据分析报告
- 📱 自动推送到飞书

**享受每天准时送达的 AI 资讯日报吧！**
