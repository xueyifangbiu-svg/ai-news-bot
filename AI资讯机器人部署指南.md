# AI 资讯自动化机器人 - 完整部署指南

> 🎯 目标：每天自动采集 AI 行业资讯，生成分析报告，并推送到飞书

---

## ✅ 已完成的工作

### 1. 飞书机器人配置 ✓
- 已创建飞书自定义机器人
- Webhook 地址：`https://open.feishu.cn/open-apis/bot/v2/hook/98fe5f02-3851-46d2-8155-a40e71d90ea3`
- 已测试消息推送成功 ✓

### 2. 项目代码开发 ✓
- 完整的项目结构已创建
- 核心功能模块已开发：
  - RSS 采集器：支持多源并发采集
  - 资讯处理器：去重、分类、评分
  - 报告生成器：生成飞书卡片格式报告
- 已测试完整流程成功 ✓

### 3. 资讯源配置 ✓
- 配置了 10 个高质量资讯源
- 包含官方动态、技术媒体、中文媒体、开发者社区
- 已验证部分源可正常访问 ✓

---

## 📦 项目文件说明

```
ai_news_bot/
├── config/
│   └── config.py          # 配置文件（包含 Webhook 地址和资讯源）
├── src/
│   ├── collectors/
│   │   └── rss_collector.py    # RSS 采集模块
│   ├── processors/
│   │   └── news_processor.py   # 资讯处理模块（去重、分类、评分）
│   └── reporters/
│       └── feishu_reporter.py # 飞书推送模块
├── main.py                 # 主程序入口
├── requirements.txt        # Python 依赖包
└── README.md              # 项目说明
```

---

## 🚀 快速开始（3 步运行）

### 第一步：安装依赖

```bash
pip install feedparser requests python-dateutil beautifulsoup4 lxml
```

### 第二步：运行程序

```bash
cd ai_news_bot
python main.py
```

### 第三步：查看飞书推送

程序运行完成后，检查你的飞书群，应该能看到类似这样的资讯日报：

```
📰 AI 资讯日报 - 2026年03月02日

📊 今日数据概览
• 采集总数：20 条
• 分类统计：
  - Media: 10 条
  - Chinese: 7 条
  - LLM: 3 条

🔥 今日热门资讯
1. 🤖 OpenAI 发布最新研究
   来源: OpenAI Blog
   [查看详情](https://openai.com/blog/...)
```

---

## 🔄 如何实现自动推送

### 方案 1：GitHub Actions（推荐，免费）

**优点**：
- 完全免费
- 无需服务器
- 稳定可靠
- 可视化管理

**步骤**：

1. **创建 GitHub 仓库**
   - 访问 https://github.com/new
   - 创建新仓库（例如：`ai-news-bot`）
   - 设置为公开或私有

2. **上传代码**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/你的用户名/ai-news-bot.git
   git push -u origin main
   ```

3. **配置 GitHub Actions**

   在仓库中创建 `.github/workflows/daily_news.yml`：

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

4. **设置时间**
   - `cron: '0 1 * * *'` 表示 UTC 时间 01:00
   - UTC + 8 小时 = 北京时间 09:00
   - 可以根据你的时区调整

### 方案 2：服务器 Cron（如果有服务器）

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 9:00 运行）
0 9 * * * cd /path/to/ai_news_bot && /usr/bin/python3 main.py >> logs/cron.log 2>&1
```

### 方案 3：本地定时任务（Windows/Mac）

**Windows 任务计划程序**：
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置每天 9:00 运行 `python main.py`

**Mac/Linux**：
```bash
# 添加到 crontab
0 9 * * * cd /path/to/ai_news_bot && python3 main.py
```

---

## ⚙️ 配置说明

### 修改资讯源

编辑 `config/config.py`，修改 `NEWS_SOURCES`：

```python
NEWS_SOURCES = [
    {
        "name": "你的资讯源名称",
        "url": "https://example.com/feed.xml",
        "category": "分类",
        "priority": 10,  # 优先级（1-10）
        "max_items": 15  # 最多抓取多少条
    },
    # 添加更多...
]
```

### 修改推送时间

编辑 `config/config.py`，修改 `PUSH_CONFIG`：

```python
PUSH_CONFIG = {
    "daily_push_time": "09:00",  # 修改为你希望的时间
    "max_daily_news": 12,        # 修改每日推送数量
}
```

### 修改 Webhook 地址

如果需要更换机器人，修改 `config/config.py`：

```python
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/你的新地址"
```

---

## 🎨 自定义功能

### 添加更多分类

编辑 `src/processors/news_processor.py`，在 `_categorize` 方法中添加：

```python
category_keywords = {
    'LLM': ['gpt', 'llm', '大模型', ...],
    'Agent': ['agent', '智能体', ...],
    '你的新分类': ['关键词1', '关键词2', ...],
}
```

### 自定义报告格式

编辑 `src/reporters/feishu_reporter.py`，修改 `_build_daily_report_card` 方法。

---

## 📊 数据分析功能

### 查看分类统计
程序运行后会自动输出：
- 按分类统计（LLM、Agent、Research 等）
- 按来源统计（OpenAI、量子位等）

### 趋势分析
程序会为每条资讯评分，排序优先推送：
- 权威来源（OpenAI、DeepMind）+5 分
- 热度关键词（发布、突破）+3 分
- 时效性（24小时内）+4 分

---

## 🔧 常见问题

### Q1: 为什么有些源抓取失败？
**A**: 可能原因：
- 网络问题（国外网站可能需要代理）
- 网站反爬虫机制
- RSS 地址变更

**解决方法**：
- 检查网络连接
- 尝试更换为其他源
- 查看日志文件：`logs/*.log`

### Q2: 如何添加更多资讯源？
**A**: 找到可靠的 RSS 地址，添加到 `config/config.py` 的 `NEWS_SOURCES` 列表中。

### Q3: 推送时间不对怎么办？
**A**: 
- GitHub Actions：修改 `.github/workflows/daily_news.yml` 中的 cron 表达式
- Cron 任务：修改 crontab 中的时间设置

### Q4: 如何查看历史数据？
**A**:
- 当前版本数据保存在内存中
- 如需持久化，可以修改代码将数据保存到数据库或文件

### Q5: 飞书推送失败怎么办？
**A**:
- 检查 Webhook 地址是否正确
- 检查机器人是否在群中
- 查看错误日志

---

## 📈 进阶功能建议

### 1. 数据持久化
- 将采集的资讯保存到数据库
- 支持历史查询和趋势分析

### 2. AI 增强功能
- 使用 OpenAI/Claude API 生成智能摘要
- 自动提取关键观点和影响分析
- 情感分析（正面/负面倾向）

### 3. 多平台推送
- 支持推送到微信群
- 支持发送邮件
- 支持推送到 Slack

### 4. 可视化增强
- 生成词云图
- 时间轴可视化
- 趋势图表

---

## 🎉 项目特色

✅ **完全免费**：GitHub Actions 免费运行
✅ **易于维护**：代码结构清晰，易于扩展
✅ **稳定可靠**：自动重试机制，错误处理完善
✅ **智能处理**：自动去重、分类、评分
✅ **美观报告**：飞书卡片格式，交互友好

---

## 📞 技术支持

如果遇到问题：
1. 检查日志文件：`logs/*.log`
2. 查看错误堆栈信息
3. 确认网络连接正常
4. 验证飞书 Webhook 地址正确

---

## 🚀 下一步

1. **测试运行**：在本地运行几次，确保一切正常
2. **部署上线**：使用 GitHub Actions 实现自动运行
3. **持续优化**：根据实际效果调整配置和功能
4. **扩展功能**：添加更多你想要的功能

---

**祝使用愉快！🎊**
