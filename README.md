# 股票数据分析系统

## 🎯 产品定位

为个人量化投资者、资深股民、小型基金等提供一个基于 Streamlit 前端 + MySQL 后端的股票数据交互分析平台，实现：
- 策略驱动的选股与重点池管理
- 多维度数据趋势图可视化
- 多表数据自动合并与导出
- 前端页面采用苹果设计风格，交互体验世界领先，适应多列数据展示及查看
- 我希望这个系统架构具备三个特性：模块清晰、易扩展、好调试

## 📦 项目结构

```
stock-data-app/
├── app.py                       # 主入口
├── start_app.bat               # 👈 双击运行的文件
├── pages/                      # 多页面模块
│   ├── 1_条件选股.py
│   ├── 2_股票池管理.py
│   ├── 3_可视化分析.py
│   └── 4_数据导出.py
├── backend/                    # 后端脚本
│   ├── db.py                   # 数据库连接
│   ├── selector.py             # 条件选股逻辑
│   ├── merger.py               # 合并数据逻辑
│   ├── visualizer.py           # 可视化数据提取
│   └── exporter.py             # 导出逻辑
├── config/
│   └── chart_config.py         # 图表默认字段配置
└── exported/
    └── [导出的Excel文件]
```

## 🗃️ 数据库配置

```
host: localhost
user: root
password: 123456
database: stock_analysis
```

### 核心数据表

| 表名 | 用途 |
|------|------|
| capital_flow | 个股资金流（主力/大单/中单/小单）|
| dde_analysis | 主力行为指标 DDX/DDY/DDZ 等 |
| position_analysis | 多周期增仓情况 |
| sector_trend | 板块热度、换手、涨跌等 |
| market_trend | 大盘指数表现，如上证、创业板等 |
| continuous_inflow_records| 暂存符合筛选条件的股票 |
| merged_data_specified | 合并后的多表数据（导出 + 可视化使用）|

## 🧩 核心功能模块


### 📊 2. 条件选股筛选器

- 条件设置：
  - 可从各数据表选择字段设置条件
  - 支持多条件组合（且关系）
  - 条件设置自动保存
- 明细展示：展示符合条件的股票及详细数据
- 支持一键加入重点池

### 📌 3. 重点股票池管理

- 当前股票池展示（代码、名称、最新日期、涨幅、主力净流入）
- 支持添加新股票
- 支持删除股票操作

### 📈 4. 可视化分析

#### 图表配置

| 图表名称 |  默认字段 |
|----------|----------|
| 主力资金图 | 主力净流入 |
| DDE 行为图 |  DDX、DDY、DDZ |
| 增仓结构图 | 今日/3日/5日/10日增仓占比 |
| 板块情绪图 |  成交量 |
| 大盘监测图 | 最新（默认上证指数）|

#### 交互功能

- [✓] 自动展示全部5类图卡
- [✓] 支持当前标的选择
- [✓] 默认字段展示，可修改保存
- [✓] 多字段下拉选择
- [✓] 折线图/柱状图切换
- [✓] 支持30/60/180日数据展示
- [✓] 动态单位值自适应

### 📦 5. 股票导出功能

- 数据来源：merged_data_specified
- 支持勾选导出
- 导出格式：Excel（如：重点股票池-2025年04月06日.xlsx）

## 🚀 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动应用：
- 双击运行 `start_app.bat`
- 或通过命令行：`streamlit run app.py --server.port=8600`
- 访问 http://localhost:8600

## 💻 开发说明

### 环境要求

- Python 3.8+
- MySQL 5.7+
- Windows 系统（Excel处理依赖win32com）

### 开发步骤

2. ✅ 条件选股 + 明细展示 + 重点池加入
3. ✅ 股票池管理 + 自动合并
4. ✅ 股票导出功能
5. ✅ 可视化五图卡模块

### 注意事项

1. Excel文件命名规范：
   - 包含数据类型关键词（如：资金流、DDE分析等）
   - 包含日期信息（YYYY-MM-DD）
   - 示例：`资金流_2024-03-20.xlsx`

2. 数据格式要求：
   - 表头需符合预定义格式
   - 数值统一使用亿为单位
   - 日期格式：YYYY-MM-DD
