#查询 continuous_inflow_records 表，获取符合三日连续净流入股票，并且从各个分表调出其近60日所有历史数据，并且生成excel文件

import mysql.connector
import pandas as pd
import datetime

# ---------------------
# 1. 从 continuous_inflow_records 表中获取股票列表
# ---------------------
def get_stocks_from_cir(db_config):
    """
    查询 continuous_inflow_records 表，获取当日符合条件的股票代码和名称
    """
    conn = mysql.connector.connect(**db_config)
    query = "SELECT DISTINCT 代码, 名称 FROM continuous_inflow_records"
    df = pd.read_sql(query, conn)
    conn.close()
    # 不存在 "序" 字段的就不用处理
    return df

# ---------------------
# 2. 分别查询其他相关表中的数据
# ---------------------
def query_capital_flow(db_config, codes):
    """
    查询资金流表（capital_flow）
    字段包括：数据日期, 序, 代码, 名称, 最新, 涨幅%, 主力净流入, 集合竞价,
              超大单流入, 超大单流出, 超大单净额, 超大单净占比%, 大单流入, 大单流出,
              大单净额, 大单净占比%, 中单流入, 中单流出, 中单净额, 中单净占比%,
              小单流入, 小单流出, 小单净额, 小单净占比%
    """
    if not codes:
        return pd.DataFrame()
    
    conn = mysql.connector.connect(**db_config)
    query = f"""
        SELECT *
        FROM capital_flow
        WHERE 代码 IN ({','.join(["'" + code + "'" for code in codes])})
    """
    df = pd.read_sql(query, conn)
    conn.close()
    # 重命名日期字段，并删除不需要的"序"列
    df.rename(columns={"数据日期": "日期"}, inplace=True)
    df.drop(columns=["序"], errors="ignore", inplace=True)
    return df

def query_dde_analysis(db_config, codes):
    """
    查询 DDE分析 表（dde_analysis）
    字段包括：数据日期, 序, 代码, 名称, 最新, 涨幅%, DDX, DDY, DDZ,
              5日DDX, 5日DDY, 10日DDX, 10日DDY, 连续, 5日内, 10日内,
              特大买入%, 特大卖出%, 特大单净比%, 大单买入%, 大单卖出%, 大单净比%
    优化后删除 "序", "最新", "涨幅%" 列
    """
    if not codes:
        return pd.DataFrame()
    
    conn = mysql.connector.connect(**db_config)
    query = f"""
        SELECT *
        FROM dde_analysis
        WHERE 代码 IN ({','.join(["'" + code + "'" for code in codes])})
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df.rename(columns={"数据日期": "日期"}, inplace=True)
    df.drop(columns=["序", "最新", "涨幅%"], errors="ignore", inplace=True)
    return df

def query_position_analysis(db_config, codes):
    """
    查询 增仓分析 表（position_analysis）
    字段包括：数据日期, 序, 代码, 名称, 最新, 涨幅%, 今日增仓占比,
              今日排名, 今日排名变化, 今日涨幅%, 3日增仓占比, 3日排名,
              3日排名变化, 3日涨幅%, 5日增仓占比, 5日排名, 5日排名变化,
              5日涨幅%, 10日增仓占比, 10日排名, 10日排名变化, 10日涨幅%
    优化后删除 "序", "最新", "涨幅%" 列
    """
    if not codes:
        return pd.DataFrame()
    
    conn = mysql.connector.connect(**db_config)
    query = f"""
        SELECT *
        FROM position_analysis
        WHERE 代码 IN ({','.join(["'" + code + "'" for code in codes])})
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df.rename(columns={"数据日期": "日期"}, inplace=True)
    df.drop(columns=["序", "最新", "涨幅%"], errors="ignore", inplace=True)
    return df

def query_sector_trend(db_config, names):
    """
    查询 板块监测 表（sector_trend）
    字段包括：数据日期, 序, 名称, 涨幅%, 3日涨幅%, 涨速%, 领涨股,
              涨家数, 跌家数, 涨跌比, 涨停家数, 换手%, 3日换手%,
              成交量, 金额, 总市值, 流通市值, 平均收益, 平均股本, 市盈率
    优化后删除 "序" 列（保留其他全部字段，用于精确匹配 "名称" 和 "日期"）
    """
    if not names:
        return pd.DataFrame()
    
    conn = mysql.connector.connect(**db_config)
    query = f"""
        SELECT *
        FROM sector_trend
        WHERE 名称 IN ({','.join(["'" + name + "'" for name in names])})
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df.rename(columns={"数据日期": "日期"}, inplace=True)
    df.drop(columns=["序"], errors="ignore", inplace=True)
    return df

# ---------------------
# 3. 合并各表数据
# ---------------------
def merge_all_data(cir_df, cf_df, dde_df, pa_df, st_df):
    """
    合并各表数据：
    - 资金流、DDE分析、增仓分析基于"代码+日期"合并
    - 板块监测基于"名称+日期"合并，因此需要利用 continuous_inflow_records 中的代码→名称映射补充名称信息
    """
    # 以资金流数据为主干
    merged = cf_df.copy()
    
    # 合并 DDE分析数据（按 代码, 日期）
    merged = pd.merge(merged, dde_df, on=["代码", "日期"], how="outer", suffixes=("", "_dde"))
    
    # 合并 增仓分析数据（按 代码, 日期）
    merged = pd.merge(merged, pa_df, on=["代码", "日期"], how="outer", suffixes=("", "_pa"))
    
    # 补充 continuous_inflow_records 中的名称（代码→名称映射）
    merged = pd.merge(merged, cir_df, on="代码", how="left", suffixes=("", "_cir"))
    
    # 合并 板块监测数据（按 名称, 日期）
    merged = pd.merge(merged, st_df, on=["名称", "日期"], how="outer", suffixes=("", "_st"))
    
    # 按代码和日期排序
    merged.sort_values(by=["代码", "日期"], inplace=True)
    merged.reset_index(drop=True, inplace=True)
    return merged

# ---------------------
# 4. 主函数：查询数据并合并展示，生成带有日期的新Excel文件
# ---------------------
def main():
    db_config = {
        "host": "rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com",
        "user": "hucongyanRoot",
        "password": "Hu123456",
        "database": "stock_analysis",
        "port": 3306,
        "charset": "utf8mb4"
    }
    # 1. 获取 continuous_inflow_records 中的股票列表
    cir_df = get_stocks_from_cir(db_config)
    if cir_df.empty:
        print("continuous_inflow_records 表中没有数据！")
        return
    codes = cir_df["代码"].unique().tolist()
    names = cir_df["名称"].unique().tolist()
    
    # 2. 查询各相关表数据
    cf_df = query_capital_flow(db_config, codes)
    dde_df = query_dde_analysis(db_config, codes)
    pa_df = query_position_analysis(db_config, codes)
    st_df = query_sector_trend(db_config, names)
    
    # 3. 合并所有数据
    merged_df = merge_all_data(cir_df, cf_df, dde_df, pa_df, st_df)
    
    # 4. 生成Excel文件，文件名带上当日日期
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    filename = f"merged_stock_data_{date_str}.xlsx"
    
    print("合并后的数据预览：")
    print(merged_df.head(10))
    merged_df.to_excel(filename, index=False)
    print(f"结果已保存到 {filename}")

if __name__ == "__main__":
    main()
