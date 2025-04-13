from backend.db import db
import pandas as pd

# 表名列表
tables = [
    "capital_flow",      # 资金流
    "dde_analysis",      # DDE分析
    "position_analysis", # 持仓分析
    "sector_trend",      # 板块趋势
    "market_trend",      # 大盘趋势
    "merged_data_specified"  # 合并数据
]

# 获取并打印各表的日期分布
print("=== 各表日期分布情况 ===")
for table in tables:
    try:
        # 获取日期分布
        query = f"SELECT DISTINCT 数据日期 FROM {table} ORDER BY 数据日期"
        df = db.query_to_dataframe(query)
        date_count = len(df)
        
        if not df.empty:
            earliest_date = df.iloc[0]['数据日期']
            latest_date = df.iloc[-1]['数据日期']
            
            # 打印表的日期信息
            print(f"\n{table} 表:")
            print(f"  - 数据日期数量: {date_count}")
            print(f"  - 最早日期: {earliest_date}")
            print(f"  - 最新日期: {latest_date}")
            print("  - 所有日期:")
            for date in df['数据日期']:
                print(f"    * {date}")
                
            # 检查是否有重复日期或异常日期
            df['数据日期'] = pd.to_datetime(df['数据日期'])
            date_counts = df['数据日期'].value_counts()
            if len(date_counts) != len(df):
                print("  - 警告: 发现重复日期!")
                for date, count in date_counts.items():
                    if count > 1:
                        print(f"    * {date}: {count}次")
        else:
            print(f"\n{table} 表: 无数据")
    except Exception as e:
        print(f"\n{table} 表查询出错: {str(e)}")

# 特别比较资金流表和板块趋势表
print("\n\n=== 资金流表与板块趋势表对比 ===")
try:
    capital_flow_dates = set(db.query_to_dataframe("SELECT DISTINCT 数据日期 FROM capital_flow")['数据日期'].astype(str))
    sector_trend_dates = set(db.query_to_dataframe("SELECT DISTINCT 数据日期 FROM sector_trend")['数据日期'].astype(str))
    
    # 比较两个表的日期差异
    print(f"资金流表日期数量: {len(capital_flow_dates)}")
    print(f"板块趋势表日期数量: {len(sector_trend_dates)}")
    
    # 找出板块趋势表有但资金流表没有的日期
    sector_only_dates = sector_trend_dates - capital_flow_dates
    if sector_only_dates:
        print("\n板块趋势表有但资金流表没有的日期:")
        for date in sorted(sector_only_dates):
            print(f"  * {date}")
    
    # 找出资金流表有但板块趋势表没有的日期
    capital_only_dates = capital_flow_dates - sector_trend_dates
    if capital_only_dates:
        print("\n资金流表有但板块趋势表没有的日期:")
        for date in sorted(capital_only_dates):
            print(f"  * {date}")
            
except Exception as e:
    print(f"比较过程出错: {str(e)}") 