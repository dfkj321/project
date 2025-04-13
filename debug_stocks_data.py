import pandas as pd
import pymysql
from sqlalchemy import create_engine
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

def get_db_connection():
    """创建数据库连接"""
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com"),
        user=os.getenv("DB_USER", "hucongyanRoot"),
        password=os.getenv("DB_PASSWORD", "Hu123456"),
        database=os.getenv("DB_DATABASE", "stock_analysis"),
        port=int(os.getenv("DB_PORT", "3306")),
        charset='utf8mb4',
        connect_timeout=30
    )
    return conn

def get_sqlalchemy_engine():
    """创建SQLAlchemy引擎"""
    db_uri = f"mysql+pymysql://{os.getenv('DB_USER', 'hucongyanRoot')}:{os.getenv('DB_PASSWORD', 'Hu123456')}@{os.getenv('DB_HOST', 'rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_DATABASE', 'stock_analysis')}?charset=utf8mb4"
    return create_engine(db_uri)

def debug_query(query):
    """执行查询并返回结果"""
    try:
        conn = get_db_connection()
        print(f"执行查询: {query}")
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"查询出错: {e}")
        return None

def main():
    # 测试数据库连接
    try:
        conn = get_db_connection()
        print("数据库连接成功")
        conn.close()
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return
        
    # 查询merged_data_specified表中的所有板块
    sectors_query = """
    SELECT DISTINCT 代码 as stock_code, 名称 as stock_name 
    FROM merged_data_specified 
    ORDER BY 代码
    """
    sectors_df = debug_query(sectors_query)
    if sectors_df is not None and not sectors_df.empty:
        print("\n当前跟踪的板块:")
        print(sectors_df)
    else:
        print("未查询到板块数据或查询出错")
    
    # 查询贵金属板块的数据
    gold_query = """
    SELECT * FROM merged_data_specified 
    WHERE 名称='贵金属' OR 代码='BK0732'
    LIMIT 5
    """
    
    gold_df = debug_query(gold_query)
    if gold_df is not None and not gold_df.empty:
        print("\n贵金属板块数据:")
        print(gold_df)
        print(f"行数: {len(gold_df)}")
        print(f"列数: {len(gold_df.columns)}")
        print(f"列名: {gold_df.columns.tolist()}")
    else:
        print("未查询到贵金属板块数据或查询出错")
    
    # 查询所有表名
    tables_query = """
    SHOW TABLES
    """
    tables_df = debug_query(tables_query)
    if tables_df is not None and not tables_df.empty:
        print("\n数据库中的表:")
        print(tables_df)
    else:
        print("未查询到表列表或查询出错")

if __name__ == "__main__":
    main() 