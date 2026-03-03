# GitHub 上传操作指南 - 数据源扩充更新

## 当前状态

✅ 本地文件已更新完成：
- `main.py` - 已扩充至16个数据源，优化热度评分
- `数据源扩充更新指南.md` - 已存在

⚠️ 需要推送到 GitHub 才能生效

---

## 方法一：通过 GitHub 网页界面（最简单）

### 第一步：上传数据源扩充更新指南.md

1. **访问仓库**
   - 打开浏览器：https://github.com/xueyifangbiu-svg/ai-news-bot

2. **上传文件**
   - 点击右上绿色按钮 **"Add file"** → 选择 **"Upload files"**

3. **拖拽上传**
   - 在本地找到 `数据源扩充更新指南.md` 文件
   - 直接拖拽到上传区域

4. **填写提交信息**
   - 在 "Commit changes" 下方填写：
   ```
   docs: 添加数据源扩充更新指南
   ```

5. **提交**
   - 点击绿色按钮 **"Commit changes"**

### 第二步：更新 main.py

1. **找到 main.py**
   - 在仓库首页找到 `main.py` 文件
   - 点击文件名进入

2. **编辑文件**
   - 点击右上角 ✏️ 铅笔图标

3. **替换内容**
   - 全选现有内容（Ctrl+A 或 Cmd+A）
   - 删除所有内容
   - 复制以下完整代码并粘贴：

```python
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

# 热度评分权重配置
HOT_KEYWORDS = {
    # 超级热词（+6分）
    'super': ['发布', '推出', '重磅', '全球首发', '发布', 'launch', 'release', 'announces', 'unveils', 'introduces'],
    # 高级热词（+4分）
    'high': ['突破', '创新', '革命性', '突破性', 'breakthrough', 'innovation', 'revolutionary'],
    # 中级热词（+3分）
    'medium': ['最新', '更新', '升级', 'v2', 'v3', 'v4', 'update', 'upgrade'],
    # 公司热词（+3分）
    'company': ['OpenAI', 'Google', 'Microsoft', 'Meta', 'Anthropic', 'DeepSeek', 'NVIDIA', 'Apple'],
    # 技术热词（+2分）
    'tech': ['GPT-5', 'GPT-4', 'Claude 3', 'LLM', '大模型', 'AGI', 'Transformer']
}

# Word 报告配置
ENABLE_WORD_REPORT = True  # 是否生成 Word 报告
WORD_REPORT_FILE = "AI_深度分析报告.docx"
MAX_NEWS_TO_PUSH = 15  # 推送的最大资讯数量

def collect_news():
    """采集资讯"""
    all_news = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    logger.info(f"开始采集 {len(SOURCES)} 个资讯源...")

    for i, source in enumerate(SOURCES, 1):
        try:
            logger.info(f"[{i}/{len(SOURCES)}] 📡 采集: {source['name']}")
            response = requests.get(source['url'], headers=headers, timeout=30)
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            max_items = source.get('max_items', 10)
            
            for entry in feed.entries[:max_items]:
                news = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', ''))[:200],
                    'source': source['name'],
                    'priority': source['priority'],
                    'category': source['category']
                }

                if news['title'] and news['link']:
                    all_news.append(news)

            logger.info(f"  ✓ 获取 {min(len(feed.entries), max_items)} 条")

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

            # 基础分数
            score = news['priority']

            # 热度评分
            score += calculate_hot_score(news)

            # 简单分类
            news['sub_category'] = classify_news(news)
            news['score'] = score
            unique_news.append(news)

    logger.info(f"✓ 去重后剩余 {len(unique_news)} 条")

    # 按分数排序
    unique_news.sort(key=lambda x: x['score'], reverse=True)

    # 限制数量
    result = unique_news[:MAX_NEWS_TO_PUSH]

    logger.info(f"✓ 处理完成，推送 {len(result)} 条资讯")
    return result

def calculate_hot_score(news):
    """计算热度分数"""
    score = 0
    title = news['title'].lower()
    summary = news.get('summary', '').lower()
    text = f"{title} {summary}"
    
    # 检查超级热词
    for keyword in HOT_KEYWORDS['super']:
        if keyword in title:
            score += 6
            logger.debug(f"  超级热词: {keyword} (+6分)")
            break
    
    # 检查高级热词
    for keyword in HOT_KEYWORDS['high']:
        if keyword in title:
            score += 4
            logger.debug(f"  高级热词: {keyword} (+4分)")
            break
    
    # 检查中级热词
    for keyword in HOT_KEYWORDS['medium']:
        if keyword in title:
            score += 3
            logger.debug(f"  中级热词: {keyword} (+3分)")
            break
    
    # 检查公司热词
    for company in HOT_KEYWORDS['company']:
        if company in title:
            score += 3
            logger.debug(f"  公司热词: {company} (+3分)")
    
    # 检查技术热词
    for tech in HOT_KEYWORDS['tech']:
        if tech in title:
            score += 2
            logger.debug(f"  技术热词: {tech} (+2分)")
    
    # 链接热度（如果链接来自高权重域名）
    if 'github.com' in news['link'] and 'stars' in title.lower():
        score += 2
        logger.debug("  GitHub 热门项目 (+2分)")
    
    return round(score, 1)

def classify_news(news):
    """简单分类"""
    title = news['title'].lower()
    summary = news.get('summary', '').lower()
    text = f"{title} {summary}"
    
    keywords = {
        'LLM': ['gpt', 'llm', '大模型', 'transformer', 'language model', 'claude', 'gemini'],
        'Agent': ['agent', '智能体', 'autonomous', 'multi-agent', 'crewai', 'langchain'],
        'AI Tool': ['工具', 'tool', 'api', 'sdk', 'library', 'framework'],
        'Research': ['paper', '论文', '研究', '发布', 'arxiv', 'breakthrough'],
        'Industry': ['公司', '融资', '投资', '企业', '财报', 'ipo', 'valuation'],
        'Application': ['应用', '落地', '场景', '产品', '发布', 'launch', 'product']
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
    category_stats = Counter([n.get('sub_category', 'Other') for n in news_list])
    source_stats = Counter([n['source'] for n in news_list])

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
                               f"• **来源数**: {len(source_stats)} 个\n"
                               f"• **分类数**: {len(category_stats)} 个\n"
                               f"• **Word 报告**: {'✅ 已生成' if word_report_file else '❌ 未生成'}\n\n"
                               f"### 🔥 今日热门资讯（按热度排序）\n\n"
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
                           f"   📅 分类: {news.get('sub_category', '未分类')}\n"
                           f"   🔥 热度: {news['score']}\n"
            }
        }

        if summary:
            news_element["text"]["content"] += f"   📝 {summary}\n"

        news_element["text"]["content"] += f"   🔗 [查看详情]({news['link']})\n\n"

        card["elements"].append(news_element)

        # 添加分隔线（最后一条除外）
        if i < len(news_list):
            card["elements"].append({"tag": "hr"})

    # 添加来源统计
    source_text = "\n\n**主要来源**:\n"
    for source, count in source_stats.most_common(5):
        source_text += f"• {source}: {count} 条\n"

    # 如果有 Word 报告，添加下载提示
    if word_report_file:
        source_text += f"\n📄 **深度分析报告**: Word 报告已生成，包含热点话题分析、重要资讯解读、趋势分析和行动建议。\n\n请在 GitHub Actions Artifacts 中下载完整报告。"

    card["elements"].append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": source_text
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
        category_stats = Counter([n.get('sub_category', 'Other') for n in processed_news])
        
        logger.info(f"\n来源统计 (共 {len(source_stats)} 个来源):")
        for source, count in source_stats.most_common():
            logger.info(f"  {source}: {count} 条")
        
        logger.info(f"\n分类统计 (共 {len(category_stats)} 个分类):")
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
```

4. **填写提交信息**
   - 在 "Commit changes" 下方填写：
   ```
   feat: 扩充数据源至16个，优化热度评分算法

- 新增12个优质资讯源（OpenAI、DeepMind、机器之心等）
- 优化热度评分算法（多维度综合评分）
- 推送数量提升至15条
   ```

5. **提交**
   - 点击绿色按钮 **"Commit changes"**

---

## 方法二：使用 Git 命令行（推荐）

打开终端，依次执行以下命令：

```bash
# 1. 进入项目目录
cd ~/ai_news_bot

# 2. 拉取最新代码
git pull origin main

# 3. 添加文件
git add 数据源扩充更新指南.md
git add main.py

# 4. 提交更改
git commit -m "feat: 扩充数据源至16个，优化热度评分算法

- 新增12个优质资讯源（OpenAI、DeepMind、机器之心等）
- 优化热度评分算法（多维度综合评分）
- 推送数量提升至15条
- 添加数据源扩充更新指南"

# 5. 推送到 GitHub
git push origin main
```

---

## 验证更新

### 手动测试

1. **访问 Actions 页面**
   - 打开：https://github.com/xueyifangbiu-svg/ai-news-bot/actions

2. **手动触发工作流**
   - 找到 "Daily AI News - 8:00 AM" 工作流
   - 点击右侧的 "Run workflow" 按钮
   - 选择 "main" 分支
   - 点击绿色 "Run workflow" 按钮

3. **等待运行完成**
   - 通常需要 2-3 分钟
   - 可以点击运行记录查看详细日志

4. **检查飞书推送**
   - 打开飞书群
   - 确认收到了新的资讯推送
   - 检查是否包含多个新的资讯源

### 检查清单

✅ **资讯来源**
- 包含 OpenAI Blog、机器之心、新智元等新渠道
- 不再只有量子位一个来源

✅ **热度排序**
- 资讯按热度从高到低排列
- 每条资讯显示热度评分

✅ **推送数量**
- 总共推送 15 条（而不是之前的 10 条）

✅ **分类统计**
- 显示多个分类（LLM、Agent、Research 等）

---

## 常见问题

### Q1: 推送失败怎么办？
**A:** 
1. 检查网络连接
2. 重新执行推送命令
3. 如果使用 Git 命令，尝试 `git push -f origin main` 强制推送

### Q2: main.py 运行报错怎么办？
**A:** 
1. 检查是否安装了依赖：`pip install -r requirements.txt`
2. 查看 GitHub Actions 运行日志
3. 确认代码没有语法错误

### Q3: 如何回滚到之前的版本？
**A:** 
1. 在 GitHub 网页上打开 main.py
2. 点击右上角 "History" 查看历史版本
3. 选择之前的版本，点击 "..." → "Revert this commit"

### Q4: 明天会自动运行新配置吗？
**A:** 
是的！只要成功推送到 GitHub，明天 8:00 AM 的定时任务会自动使用新配置运行。

### Q5: 如何调整推送数量？
**A:** 
在 main.py 中修改 `MAX_NEWS_TO_PUSH` 参数（当前为 15），然后重新提交推送。

---

## 更新内容总结

| 项目 | 更新前 | 更新后 |
|------|--------|--------|
| 资讯源数量 | 4 个 | 16 个 |
| 推送数量 | 10 条 | 15 条 |
| 热度评分 | 简单关键词 | 多维度综合评分 |
| 来源多样性 | 低 | 高 |
| 更新时间 | - | 2026年3月3日 |

---

**祝你操作顺利！** 🎉

如有问题，请检查 GitHub Actions 日志获取详细错误信息。
