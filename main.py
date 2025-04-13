# 将资金表、增仓表、DDE表、板块监测、大盘监测表的每日股票信息，将excel文件自动导入数据库存起来

import pandas as pd
import os
import mysql.connector
import re
import numpy as np

# ------------------------
# 数据库连接信息
# ------------------------
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "stock_analysis",
}

# ------------------------
# Excel 文件存放目录
# ------------------------
directory = r"C:\Users\hucon\Desktop\stock_analysis\\"

# ------------------------
# 单位转换函数：将包含“万亿”、“亿”或“万”的字符串转换为统一单位（亿）
# ------------------------
def convert_to_yi(value):
    """
    将包含“万亿”、“亿”或“万”的字符串转换为统一单位（亿）
    - 例如： "1.80万亿" -> 1.80*10000 = 18000
    - "2.4亿"   -> 2.4
    - "150万"   -> 150/10000 = 0.015
    - 纯数字直接转换
    """
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
            if "万亿" in value:
                return float(value.replace("万亿", "")) * 10000
            elif "亿" in value:
                return float(value.replace("亿", ""))
            elif "万" in value:
                return float(value.replace("万", "")) / 10000
            else:
                return float(value)
        return float(value)
    except ValueError:
        return None

# ------------------------
# 需要转换单位的列（统一转换为“亿”）
# ------------------------
unit_conversion_columns = {
    "capital_flow": [
        '主力净流入', '集合竞价', '超大单流入', '超大单流出', '超大单净额',
        '大单流入', '大单流出', '大单净额', '中单流入', '中单流出', '中单净额',
        '小单流入', '小单流出', '小单净额'
    ],
    "market_trend": ['金额'],
    "sector_trend": ['成交量', '金额', '总市值', '流通市值', '平均股本'],
}

# ------------------------
# 表名与正确表头的映射
# 说明：预期表头中已包含“数据日期”。对于板块监测，预期表头中不再包含“涨跌家数”，而是拆分成“涨家数”和“跌家数”
# ------------------------
expected_columns = {
    "DDE分析": (
        "dde_analysis",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', 'DDX', 'DDY', 'DDZ',
         '5日DDX', '5日DDY', '10日DDX', '10日DDY', '连续', '5日内', '10日内',
         '特大买入%', '特大卖出%', '特大单净比%', '大单买入%', '大单卖出%', '大单净比%']
    ),
    "增仓分析": (
        "position_analysis",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', '今日增仓占比',
         '今日排名', '今日排名变化', '今日涨幅%', '3日增仓占比', '3日排名',
         '3日排名变化', '3日涨幅%', '5日增仓占比', '5日排名', '5日排名变化',
         '5日涨幅%', '10日增仓占比', '10日排名', '10日排名变化', '10日涨幅%']
    ),
    "大盘监测": (
        "market_trend",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', '涨跌',
         '金额', '最高', '最低', '开盘', '昨收']
    ),
    "板块监测": (
        "sector_trend",
        ['数据日期', '序', '名称', '涨幅%', '3日涨幅%', '涨速%', '领涨股',
         '涨家数', '跌家数', '涨跌比', '涨停家数', '换手%', '3日换手%',
         '成交量', '金额', '总市值', '流通市值', '平均收益', '平均股本', '市盈率']
    ),
    "资金流": (
        "capital_flow",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', '主力净流入', '集合竞价',
         '超大单流入', '超大单流出', '超大单净额', '超大单净占比%', '大单流入', '大单流出',
         '大单净额', '大单净占比%', '中单流入', '中单流出', '中单净额', '中单净占比%',
         '小单流入', '小单流出', '小单净额', '小单净占比%']
    ),
}

# ------------------------
# 连接数据库
# ------------------------
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# ------------------------
# 获取所有 Excel 文件（排除 ~$ 开头的临时文件）
# ------------------------
files = [f for f in os.listdir(directory) if f.endswith(".xlsx") and not f.startswith("~$")]

for file in files:
    file_path = os.path.join(directory, file)

    # ------------------------
    # 根据文件名关键词匹配目标数据库表和预期表头
    # ------------------------
    table_name = None
    expected_table_cols = None
    for keyword, (db_table, exp_cols) in expected_columns.items():
        if keyword in file:
            table_name = db_table
            expected_table_cols = exp_cols  # 保存预期表头
            break
    if not table_name:
        print(f"⚠️ 未找到匹配的数据库表，跳过文件：{file}")
        continue

    try:
        print(f"📌 处理文件：{file}")

        # ------------------------
        # 从文件名中解析数据日期（假设文件名中包含 YYYY-MM-DD 格式的日期）
        # ------------------------
        match = re.search(r"(\d{4}-\d{2}-\d{2})", file)
        if not match:
            print(f"⚠️ 无法解析文件日期，跳过文件：{file}")
            continue
        data_date = match.group(1)

        # ------------------------
        # 读取 Excel 文件
        # ------------------------
        df = pd.read_excel(file_path, sheet_name=0)

        # ------------------------
        # 标准化列名：去除前后空格、替换多个空格，并填充空值
        # ------------------------
        df.columns = df.columns.astype(str).str.strip().str.replace(r"\s+", "", regex=True).fillna("")

        # ------------------------
        # 删除完全为空的列，避免多余空列
        # ------------------------
        df = df.dropna(axis=1, how="all")

        # ------------------------
        # 确保“数据日期”列存在：如果Excel中没有，则插入；如果已存在则覆盖
        # ------------------------
        if "数据日期" not in df.columns:
            df.insert(0, "数据日期", data_date)
        else:
            df["数据日期"] = data_date

        # ------------------------
        # 强制“代码”列为字符串，并补齐前导零（假设代码应为6位）
        # ------------------------
        if "代码" in df.columns:
            df["代码"] = df["代码"].astype(str).str.strip()
            df["代码"] = df["代码"].apply(lambda x: x.zfill(6) if x.isdigit() else x)

        # ------------------------
        # 删除“序”列（假设数据库“序”字段为自增主键，不参与插入）
        # ------------------------
        if "序" in df.columns:
            df = df.drop(columns=["序"])
            expected_table_cols = [col for col in expected_table_cols if col != "序"]

        # ------------------------
        # 针对板块监测表：拆分“涨跌家数”为“涨家数”和“跌家数”
        # ------------------------
        if table_name == "sector_trend" and "涨跌家数" in df.columns:
            df[['涨家数', '跌家数']] = df['涨跌家数'].str.split('/', expand=True)
            df['涨家数'] = pd.to_numeric(df['涨家数'].astype(str).str.strip(), errors='coerce')
            df['跌家数'] = pd.to_numeric(df['跌家数'].astype(str).str.strip(), errors='coerce')
            df.drop(columns=['涨跌家数'], inplace=True)

        # ------------------------
        # 数据单位转换：对于需要转换单位的字段，统一转换为“亿”
        # ------------------------
        if table_name in unit_conversion_columns:
            for col in unit_conversion_columns[table_name]:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: convert_to_yi(x) if pd.notnull(x) else None)

        # ------------------------
        # 替换 DataFrame 中的 NaN 为 None，防止 SQL 错误
        # ------------------------
        df = df.replace({np.nan: None})

        # ------------------------
        # 如果是板块监测，需要重新排序列以符合预期顺序
        # ------------------------
        if table_name == "sector_trend":
            df = df[expected_table_cols]
        else:
            if list(df.columns) != list(expected_table_cols):
                print(f"❌ 表头不匹配，跳过文件：{file}")
                print(f"  读取的表头：{list(df.columns)}")
                print(f"  预期的表头：{expected_table_cols}")
                continue

        # ------------------------
        # 删除旧数据（相同数据日期）
        # ------------------------
        cursor.execute(f"DELETE FROM `{table_name}` WHERE `数据日期` = %s", (data_date,))
        conn.commit()
        print(f"🗑️ 已清除 {data_date} 的旧数据")

        # ------------------------
        # 构建 INSERT SQL 语句，自动为所有字段加反引号
        # ------------------------
        columns_str = ", ".join([f"`{col}`" for col in df.columns])
        values_placeholder = ", ".join(["%s"] * len(df.columns))
        insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_placeholder})"

        # ------------------------
        # 批量插入数据
        # ------------------------
        cursor.executemany(insert_query, df.values.tolist())
        conn.commit()

        print(f"✅ 成功导入：{file} -> {table_name}")

    except Exception as e:
        print(f"❌ 解析 Excel 失败：{file}，错误：{e}")

cursor.close()
conn.close()
print("🚀 所有数据导入完成！")
