import pandas as pd
import datetime
from sqlalchemy import create_engine
import sys
import os

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from key_stocks_tracker import get_engine, get_key_stocks, query_capital_flow, query_dde_analysis, query_position_analysis, query_sector_trend

def debug_key_stocks_tracker():
    # 数据库配置
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "123456",
        "database": "stock_analysis",
    }
    
    # 创建引擎
    print("创建数据库引擎...")
    engine = get_engine(db_config)
    
    # 获取所有表名
    try:
        tables_query = "SHOW TABLES"
        tables_df = pd.read_sql(tables_query, engine)
        print("\n数据库中的表:")
        print(tables_df)
    except Exception as e:
        print(f"查询表名时出错: {e}")
    
    # 获取重点股票
    print("\n获取重点股票...")
    key_df, stock_dict = get_key_stocks()
    codes = key_df["代码"].unique().tolist()
    names = key_df["名称"].unique().tolist()
    
    print(f"重点股票代码: {codes}")
    print(f"重点股票名称: {names}")
    
    # 检查DDE_analysis表结构
    try:
        print("\n检查DDE_analysis表结构...")
        dde_structure_query = "SHOW COLUMNS FROM dde_analysis"
        dde_structure_df = pd.read_sql(dde_structure_query, engine)
        print("DDE_analysis表结构:")
        print(dde_structure_df)
    except Exception as e:
        print(f"检查DDE_analysis表结构时出错: {e}")
    
    # 检查DDE_analysis表数据
    try:
        print("\n检查DDE_analysis表数据...")
        dde_data_query = "SELECT COUNT(*) as count FROM dde_analysis"
        dde_count_df = pd.read_sql(dde_data_query, engine)
        print(f"DDE_analysis表中有 {dde_count_df.iloc[0]['count']} 条记录")
        
        if dde_count_df.iloc[0]['count'] > 0:
            dde_sample_query = "SELECT * FROM dde_analysis LIMIT 1"
            dde_sample_df = pd.read_sql(dde_sample_query, engine)
            print("DDE_analysis表数据样例:")
            print(dde_sample_df)
            
            # 检查股票代码列表中的记录
            for code in codes:
                code_query = f"SELECT COUNT(*) as count FROM dde_analysis WHERE 代码 = '{code}'"
                code_count_df = pd.read_sql(code_query, engine)
                print(f"代码 {code} 在DDE_analysis表中有 {code_count_df.iloc[0]['count']} 条记录")
    except Exception as e:
        print(f"检查DDE_analysis表数据时出错: {e}")
    
    # 查询各相关表数据
    print("\n查询各相关表数据...")
    cf_df = query_capital_flow(engine, codes)
    print(f"资金流数据: {len(cf_df)} 条记录")
    
    dde_df = query_dde_analysis(engine, codes)
    print(f"DDE分析数据: {len(dde_df)} 条记录")
    
    pa_df = query_position_analysis(engine, codes)
    print(f"持仓分析数据: {len(pa_df)} 条记录")
    
    st_df = query_sector_trend(engine, names)
    print(f"板块趋势数据: {len(st_df)} 条记录")
    
    # 如果DDE分析数据为空，检查原因
    if dde_df.empty:
        print("\n调试DDE分析数据查询...")
        try:
            # 尝试手动构建查询
            codes_str = ','.join([f"'{code}'" for code in codes])
            test_query = f"SELECT * FROM dde_analysis WHERE 代码 IN ({codes_str}) LIMIT 5"
            print(f"测试查询: {test_query}")
            test_df = pd.read_sql(test_query, engine)
            print(f"测试查询结果: {len(test_df)} 条记录")
            if not test_df.empty:
                print("测试查询样例:")
                print(test_df.head())
            else:
                print("测试查询没有返回任何记录")
                
                # 检查是否存在任何记录
                any_query = "SELECT * FROM dde_analysis LIMIT 5"
                any_df = pd.read_sql(any_query, engine)
                print(f"表中任意5条记录: {len(any_df)}")
                if not any_df.empty:
                    print("记录样例:")
                    print(any_df.head())
                    print("检查这些记录中的代码:")
                    print(any_df['代码'].unique())
                    
                    # 提出可能的修复方案
                    print("\n可能的问题:")
                    print("1. 代码格式不匹配: 检查代码前缀或格式")
                    print("2. 表中没有对应代码的数据: 需要先导入对应的数据")
                    print("3. 表名大小写问题: 检查表名是否正确")
        except Exception as e:
            print(f"调试DDE分析数据查询时出错: {e}")

if __name__ == "__main__":
    debug_key_stocks_tracker() 