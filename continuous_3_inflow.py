# 获取最近 3 个交易日净流入的股票并写入continuous_inflow_records表格

import datetime
import chinese_calendar as cc
import mysql.connector
import pandas as pd

def get_last_trading_days(n):
    """
    返回最近 n 个交易日的日期字符串列表（格式 YYYY-MM-DD）。
    利用 chinese_calendar 判断工作日（非节假日且非周末）。
    """
    today = datetime.date.today()
    # 如果今天不是交易日，则回溯到最近的交易日
    while not cc.is_workday(today):
        today -= datetime.timedelta(days=1)
    trading_days = []
    current = today
    while len(trading_days) < n:
        if cc.is_workday(current):
            trading_days.append(current.strftime("%Y-%m-%d"))
        current -= datetime.timedelta(days=1)
    trading_days.reverse()  # 最早的在前
    return trading_days

# 获取最近 3 个交易日
trading_days = get_last_trading_days(3)
print("最近三个交易日：", trading_days)

# ------------------------
# 数据库连接信息
# ------------------------
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "stock_analysis",
}

# 连接数据库
conn = mysql.connector.connect(**db_config)

# 查询指定交易日内的数据
# 假设 capital_flow 表中有字段：数据日期, 代码, 名称, 主力净流入
query = f"""
SELECT 数据日期, 代码, 名称, 主力净流入
FROM capital_flow
WHERE 数据日期 IN ({','.join(["'" + d + "'" for d in trading_days])})
ORDER BY 代码, 数据日期
"""
df = pd.read_sql(query, conn)
print("查询到的原始数据：")
print(df)

# ------------------------
# 按股票代码分组，过滤出连续三个交易日主力净流入均大于0的股票
# 并提取三个交易日的净流入数据：
#   inflow_t2：倒数第三日（最早的）
#   inflow_t1：昨日
#   inflow_t0：当日
# ------------------------
results = []
for code, group in df.groupby("代码"):
    if len(group) == 3 and (group["主力净流入"] > 0).all():
        # 按日期排序确保顺序正确
        group_sorted = group.sort_values("数据日期")
        inflow_t2 = group_sorted.iloc[0]["主力净流入"]  # 倒数第三日
        inflow_t1 = group_sorted.iloc[1]["主力净流入"]  # 昨日
        inflow_t0 = group_sorted.iloc[2]["主力净流入"]  # 当日
        record_date = group_sorted.iloc[2]["数据日期"]   # 以当日为记录日期
        stock_name = group_sorted.iloc[2]["名称"]
        results.append((record_date, stock_name, code, inflow_t0, inflow_t1, inflow_t2))

result_df = pd.DataFrame(results, columns=["日期", "名称", "代码", "inflow_t0", "inflow_t1", "inflow_t2"])
print("连续三个交易日主力净流入大于0的股票记录：")
print(result_df)

# ------------------------
# 插入数据到 continuous_inflow_records 表之前：
# 先清空表中之前的记录（假设只保留当天最新计算结果）
# ------------------------
cursor = conn.cursor()
truncate_sql = "TRUNCATE TABLE continuous_inflow_records"
cursor.execute(truncate_sql)
conn.commit()
print("已清空 continuous_inflow_records 表的数据。")

# 插入最新计算的数据
insert_sql = """
INSERT INTO continuous_inflow_records (日期, 名称, 代码, inflow_t0, inflow_t1, inflow_t2)
VALUES (%s, %s, %s, %s, %s, %s)
"""
cursor.executemany(insert_sql, results)
conn.commit()
print("已将最新连续三日主力净流入的股票记录插入 continuous_inflow_records 表。")

cursor.close()
conn.close()
