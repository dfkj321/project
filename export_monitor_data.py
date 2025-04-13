# ----------------- 重点监控板块数据导出 -----------------
import pandas as pd
import pymysql
from datetime import datetime
import os
import glob

# ----------------- 数据库连接配置 -----------------
host = 'localhost'
port = 3306  # 端口号
user = 'root'
password = '123456'
database = 'stock_analysis'
table_name = 'merged_data_specified'  # 例如：merged_data_specified

# ----------------- 删除旧的导出文件 -----------------
# 匹配当前目录下以“重点监控板块数据-”开头，以“.xlsx”结尾的文件
for file in glob.glob("重点监控板块数据-*.xlsx"):
    try:
        os.remove(file)
        print(f"🗑️ 已删除旧文件：{file}")
    except Exception as e:
        print(f"⚠️ 删除文件失败：{file}，原因：{e}")

# ----------------- 获取数据 -----------------
# 创建连接
connection = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    charset='utf8mb4'
)

# 查询语句（可根据需要筛选字段）
query = f"SELECT * FROM {table_name}"
df = pd.read_sql(query, connection)

# 关闭连接
connection.close()

# ----------------- 数据处理：排序 -----------------
df['数据日期'] = pd.to_datetime(df['数据日期'])  # 日期格式转换
df_sorted = df.sort_values(by=['名称', '数据日期'], ascending=[True, False])

# 👉 格式化日期，只保留“2025年03月20日”格式
df_sorted['数据日期'] = df_sorted['数据日期'].dt.strftime('%Y年%m月%d日')

# ----------------- 补充单位到列名 -----------------
unit_mapping = {
    '主力净流入': '主力净流入/亿',
    '集合竞价': '集合竞价/亿',
    '超大单流入': '超大单流入/亿',
    '超大单流出': '超大单流出/亿',
    '超大单净额': '超大单净额/亿',
    '大单流入': '大单流入/亿',
    '大单流出': '大单流出/亿',
    '大单净额': '大单净额/亿',
    '中单流入': '中单流入/亿',
    '中单流出': '中单流出/亿',
    '中单净额': '中单净额/亿',
    '小单流入': '小单流入/亿',
    '小单流出': '小单流出/亿',
    '小单净额': '小单净额/亿',
    '成交量': '成交量/亿',
    '金额': '金额/亿',
    '总市值': '总市值/亿',
    '流通市值': '流通市值/亿',
    '平均股本': '平均股本/亿',
    

}

# 重命名列名
df_sorted.rename(columns=unit_mapping, inplace=True)


# ----------------- 文件命名与导出 -----------------
today = datetime.today().strftime('%Y年%m月%d日')
filename = f'重点监控板块数据-{today}.xlsx'
df_sorted.to_excel(filename, index=False)

print(f"✅ 数据已导出为：{filename}")
