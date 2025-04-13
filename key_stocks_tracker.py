# 监控重点股票数据，四个分表数据合并存入数据库

import pandas as pd
import datetime
from sqlalchemy import create_engine

# ----------------------------------------------------------------------
# 1. 从数据库获取所有板块股票（代码和名称）
# ----------------------------------------------------------------------
def get_key_stocks(engine):
    """从数据库中获取所有板块股票"""
    try:
        # 从merged_data_specified表获取所有唯一的板块代码和名称
        query = """
            SELECT DISTINCT 代码, 名称 
            FROM merged_data_specified
            WHERE 代码 LIKE 'BK%'
        """
        print("从数据库获取所有板块...")
        df = pd.read_sql(query, engine)
        
        # 如果没有记录，使用备用的默认板块
        if df.empty:
            print("未从数据库找到板块数据，使用默认板块")
            stock_dict = {
                'BK1090': '机器人概念',
                'BK0711': '券商概念',
                'BK1037': '消费电子',
                'BK1036': '半导体',
                'BK0579': '云计算'
            }
            df = pd.DataFrame({
                '代码': list(stock_dict.keys()),
                '名称': list(stock_dict.values())
            })
        else:
            print(f"从数据库获取到 {len(df)} 个板块")
            # 创建字典用于其他函数
            stock_dict = dict(zip(df['代码'], df['名称']))
        
        # 统一清洗名称：去除空格并转换为大写
        df["名称"] = df["名称"].astype(str).str.strip().str.upper()
        return df, stock_dict
    except Exception as e:
        print(f"获取板块数据时出错: {e}")
        # 发生错误时使用默认板块
        print("使用默认的5个板块作为备选")
        stock_dict = {
            'BK1090': '机器人概念',
            'BK0711': '券商概念',
            'BK1037': '消费电子',
            'BK1036': '半导体',
            'BK0579': '云计算'
        }
        df = pd.DataFrame({
            '代码': list(stock_dict.keys()),
            '名称': list(stock_dict.values())
        })
        df["名称"] = df["名称"].astype(str).str.strip().str.upper()
        return df, stock_dict

# ----------------------------------------------------------------------
# 2. 创建 SQLAlchemy 引擎
# ----------------------------------------------------------------------
def get_engine(db_config):
    # 创建MySQL连接字符串
    conn_str = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset=utf8mb4"
    engine = create_engine(conn_str, echo=False)
    return engine

# ----------------------------------------------------------------------
# 辅助函数：检查数据框结构
# ----------------------------------------------------------------------
def inspect_dataframe(df, name):
    print(f"\n检查 {name} 数据结构:")
    print(f"行数: {len(df)}")
    print(f"列名: {list(df.columns)}")
    if not df.empty:
        print(f"数据样本:\n{df.head(1).T}")
    print("="*50)

# ----------------------------------------------------------------------
# 检查目标表结构
# ----------------------------------------------------------------------
def check_target_table(engine, table_name):
    try:
        query = f"SHOW COLUMNS FROM `{table_name}`"
        columns_df = pd.read_sql(query, engine)
        print(f"\n目标表 {table_name} 结构:")
        print(columns_df)
        return True
    except Exception as e:
        print(f"检查目标表结构时出错: {e}")
        return False

# ----------------------------------------------------------------------
# 3. 查询各相关表数据（重命名"数据日期"为"日期"便于合并）
# ----------------------------------------------------------------------
def query_capital_flow(engine, codes):
    if not codes:
        return pd.DataFrame()
    try:
        query = f"""
            SELECT *
            FROM capital_flow
            WHERE 代码 IN ({','.join(["'" + code + "'" for code in codes])})
        """
        print(f"执行资金流查询...")
        df = pd.read_sql(query, engine)
        df.rename(columns={"数据日期": "日期"}, inplace=True)
        df.drop(columns=["序"], errors="ignore", inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        return df
    except Exception as e:
        print(f"查询资金流数据时出错: {e}")
        return pd.DataFrame()

def query_dde_analysis(engine, codes):
    if not codes:
        return pd.DataFrame()
    try:
        query = f"""
            SELECT *
            FROM dde_analysis
            WHERE 代码 IN ({','.join(["'" + code + "'" for code in codes])})
        """
        print(f"执行DDE分析查询...")
        df = pd.read_sql(query, engine)
        df.rename(columns={"数据日期": "日期"}, inplace=True)
        df.drop(columns=["序", "最新", "涨幅%"], errors="ignore", inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        return df
    except Exception as e:
        print(f"查询DDE分析数据时出错: {e}")
        return pd.DataFrame()

def query_position_analysis(engine, codes):
    if not codes:
        return pd.DataFrame()
    try:
        query = f"""
            SELECT *
            FROM position_analysis
            WHERE 代码 IN ({','.join(["'" + code + "'" for code in codes])})
        """
        print(f"执行持仓分析查询...")
        df = pd.read_sql(query, engine)
        df.rename(columns={"数据日期": "日期"}, inplace=True)
        df.drop(columns=["序", "最新", "涨幅%"], errors="ignore", inplace=True)
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        return df
    except Exception as e:
        print(f"查询持仓分析数据时出错: {e}")
        return pd.DataFrame()

def query_sector_trend(engine, names):
    if not names:
        return pd.DataFrame()
    try:
        # 打印要查询的板块名称
        print(f"尝试查询的板块名称: {names}")
        
        # 先尝试确切匹配
        formatted_names = [name.strip().upper() for name in names]
        exact_query = f"""
            SELECT *
            FROM sector_trend
            WHERE UPPER(TRIM(名称)) IN ({','.join(["'" + name + "'" for name in formatted_names])})
        """
        print("执行板块趋势精确匹配查询...")
        df = pd.read_sql(exact_query, engine)
        
        # 如果确切匹配没有结果，尝试模糊匹配
        if df.empty:
            print(f"警告: 未能在 sector_trend 表中找到任何精确匹配的板块名称")
            
            # 获取sector_trend表中的所有名称
            all_names_query = "SELECT DISTINCT 名称 FROM sector_trend"
            all_names_df = pd.read_sql(all_names_query, engine)
            all_names = all_names_df['名称'].tolist()
            print(f"sector_trend 表中共有 {len(all_names)} 个板块名称")
            
            # 显示前10个名称作为参考
            print(f"sector_trend 表中的名称样本: {all_names[:10]}")
            
            print("尝试使用模糊匹配...")
            # 构建模糊匹配的查询条件
            like_conditions = []
            for name in formatted_names:
                # 去除可能的概念、板块等后缀
                base_name = name.replace('概念', '').replace('板块', '').strip()
                like_conditions.append(f"UPPER(TRIM(名称)) LIKE '%{base_name}%'")
            
            if like_conditions:
                fuzzy_query = f"""
                    SELECT *
                    FROM sector_trend
                    WHERE {' OR '.join(like_conditions)}
                """
                print("执行板块趋势模糊匹配查询...")
                df = pd.read_sql(fuzzy_query, engine)
                print(f"模糊匹配找到 {len(df)} 条记录")
                if not df.empty:
                    # 打印匹配到的名称
                    matched_names = df['名称'].unique().tolist()
                    print(f"模糊匹配到的板块名称: {matched_names}")
        
        df.rename(columns={"数据日期": "日期", "名称": "名称_cir"}, inplace=True)
        df.drop(columns=["序"], errors="ignore", inplace=True)
        if "名称_cir" in df.columns:
            df["名称_cir"] = df["名称_cir"].astype(str).str.strip().str.upper()
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        return df
    except Exception as e:
        print(f"查询 sector_trend 表出错: {e}")
        return pd.DataFrame()

# ----------------------------------------------------------------------
# 4. 获取目标表中最新数据日期（目标表字段为"数据日期"）
# ----------------------------------------------------------------------
def get_latest_date(engine, table_name):
    try:
        query = f"SELECT MAX(`数据日期`) AS max_date FROM `{table_name}`"
        df = pd.read_sql(query, engine)
        if df.empty or pd.isnull(df.loc[0, "max_date"]):
            return None
        return pd.to_datetime(df.loc[0, "max_date"]).date()
    except Exception as e:
        print(f"获取最新日期时出错: {e}")
        return None

# ----------------------------------------------------------------------
# 5. 合并各表数据
#
#    - capital_flow、dde_analysis、position_analysis：基于 (代码, 日期) 合并；
#    - 利用重点股票映射补充名称（key_stocks 中名称统一为大写）；
#    - sector_trend：现在基于 (名称, 日期) 改为 (名称_cir, 日期) 合并。
# ----------------------------------------------------------------------
def merge_all_data(key_df, cf_df, dde_df, pa_df, st_df):
    # 从资金流表开始
    if cf_df.empty:
        print("警告: 资金流数据为空，无法开始合并")
        return pd.DataFrame()
        
    merged = cf_df.copy()
    
    # 依次合并其他表
    if not dde_df.empty:
        print(f"合并DDE分析数据 ({len(dde_df)}条记录)...")
        merged = pd.merge(merged, dde_df, on=["代码", "日期"], how="left", suffixes=("", "_dde"))
    else:
        print("DDE分析数据为空，跳过合并")
        
    if not pa_df.empty:
        print(f"合并持仓分析数据 ({len(pa_df)}条记录)...")
        merged = pd.merge(merged, pa_df, on=["代码", "日期"], how="left", suffixes=("", "_pa"))
    else:
        print("持仓分析数据为空，跳过合并")
    
    # 合并重点股票信息，补充名称
    print(f"补充股票名称信息...")
    merged = pd.merge(merged, key_df, on="代码", how="left", suffixes=("", "_key"))
    
    # 确保名称字段存在且处理大小写
    if "名称" in merged.columns:
        merged["名称"] = merged["名称"].astype(str).str.strip().str.upper()
        print(f"合并后数据中的板块名称: {merged['名称'].unique().tolist()}")
        
        # 添加名称_cir字段，复制名称字段的值
        merged["名称_cir"] = merged["名称"]
    
    # 合并板块趋势数据（使用名称_cir字段）
    if not st_df.empty:
        print(f"合并板块趋势数据 ({len(st_df)}条记录)...")
        # 确保st_df的名称_cir字段也是大写
        print(f"板块趋势数据中的名称_cir: {st_df['名称_cir'].unique().tolist()}")
        
        # 检查是否有匹配的名称_cir
        common_names = set(merged['名称_cir'].unique()) & set(st_df['名称_cir'].unique())
        print(f"合并数据与板块趋势数据中的共同名称_cir: {list(common_names)}")
        
        if common_names:
            merged = pd.merge(merged, st_df, on=["名称_cir", "日期"], how="left", suffixes=("", "_st"))
        else:
            print("警告: 没有匹配的板块名称_cir，跳过板块趋势数据合并")
            # 创建模拟的空列，防止后续处理出错
            for col in ["涨幅%_st", "3日涨幅%_st", "涨速%", "领涨股", "涨家数", "跌家数",
                       "涨跌比", "涨停家数", "换手%", "3日换手%", "成交量", "金额", "总市值",
                       "流通市值", "平均收益", "平均股本", "市盈率"]:
                if col not in merged.columns:
                    merged[col] = None
    else:
        print("板块趋势数据为空，跳过合并")
        # 创建模拟的空列，防止后续处理出错
        for col in ["涨幅%_st", "3日涨幅%_st", "涨速%", "领涨股", "涨家数", "跌家数",
                   "涨跌比", "涨停家数", "换手%", "3日换手%", "成交量", "金额", "总市值",
                   "流通市值", "平均收益", "平均股本", "市盈率"]:
            if col not in merged.columns:
                merged[col] = None
    
    merged.sort_values(by=["代码", "日期"], inplace=True)
    merged.reset_index(drop=True, inplace=True)
    
    # 在这里将"日期"列重命名为"数据日期"，以匹配目标表结构
    merged.rename(columns={"日期": "数据日期"}, inplace=True)
    
    return merged

# ----------------------------------------------------------------------
# 6. 过滤掉目标表中已有的记录（相同的日期、代码、名称）
# ----------------------------------------------------------------------
def filter_existing_data(engine, table_name, new_df):
    try:
        query = f"SELECT `数据日期`, `代码`, `名称`, `名称_cir` FROM `{table_name}`"
        print(f"查询目标表 {table_name} 中已有记录...")
        existing_df = pd.read_sql(query, engine)
        
        if existing_df.empty:
            print("目标表为空，不需要过滤")
            return new_df
            
        # 将目标表中字段"数据日期"转换为 date 类型
        existing_df['数据日期'] = pd.to_datetime(existing_df['数据日期']).dt.date
        
        # 统一名称格式
        if "名称" in existing_df.columns:
            existing_df["名称"] = existing_df["名称"].astype(str).str.strip().str.upper()
        
        # 统一名称_cir格式
        if "名称_cir" in existing_df.columns:
            existing_df["名称_cir"] = existing_df["名称_cir"].astype(str).str.strip().str.upper()
        
        # 确保新数据中的"数据日期"字段是正确的日期类型
        new_df['数据日期'] = pd.to_datetime(new_df['数据日期']).dt.date
        
        # 统一新数据名称格式
        if "名称" in new_df.columns:
            new_df["名称"] = new_df["名称"].astype(str).str.strip().str.upper()
        
        # 统一新数据名称_cir格式
        if "名称_cir" in new_df.columns:
            new_df["名称_cir"] = new_df["名称_cir"].astype(str).str.strip().str.upper()
        
        print(f"过滤前新数据记录数: {len(new_df)}")
        # 修改：同时使用名称和名称_cir进行过滤
        merged = pd.merge(new_df, existing_df, on=['数据日期', '代码', '名称', '名称_cir'], how='left', indicator=True)
        filtered_df = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
        print(f"过滤后新数据记录数: {len(filtered_df)}")
        return filtered_df
    except Exception as e:
        print(f"过滤已有数据时出错: {e}")
        # 如果出错，返回原始数据，避免数据丢失
        return new_df

# ----------------------------------------------------------------------
# 7. 规定合并后的数据字段顺序，与目标表结构严格对应
# ----------------------------------------------------------------------
def reindex_columns(merged_df):
    # 注意目标表字段顺序如下（必须与数据库中的表结构一致）
    target_columns = [
        "数据日期", "代码", "名称", "名称_cir", "最新", "涨幅%", "主力净流入", "集合竞价",
        "超大单流入", "超大单流出", "超大单净额", "超大单净占比%", "大单流入", "大单流出",
        "大单净额", "大单净占比%", "中单流入", "中单流出", "中单净额", "中单净占比%",
        "小单流入", "小单流出", "小单净额", "小单净占比%", "名称_dde", "DDX", "DDY",
        "DDZ", "5日DDX", "5日DDY", "10日DDX", "10日DDY", "连续", "5日内", "10日内",
        "特大买入%", "特大卖出%", "特大单净比%", "大单买入%", "大单卖出%", "大单净比%",
        "名称_pa", "今日增仓占比", "今日排名", "今日排名变化", "今日涨幅%", "3日增仓占比",
        "3日排名", "3日排名变化", "3日涨幅%", "5日增仓占比", "5日排名", "5日排名变化",
        "5日涨幅%", "10日增仓占比", "10日排名", "10日排名变化", "10日涨幅%",
        "涨幅%_st", "3日涨幅%_st", "涨速%", "领涨股", "涨家数", "跌家数",
        "涨跌比", "涨停家数", "换手%", "3日换手%", "成交量", "金额", "总市值",
        "流通市值", "平均收益", "平均股本", "市盈率"
    ]
    
    # 检查目标列中的列是否都存在于合并数据中
    missing_columns = [col for col in target_columns if col not in merged_df.columns]
    if missing_columns:
        print(f"警告: 合并数据中缺少以下列: {missing_columns}")
        # 为缺失的列添加空值
        for col in missing_columns:
            merged_df[col] = None
    
    # 重新排列列顺序
    merged_df = merged_df.reindex(columns=target_columns, fill_value=None)
    return merged_df

# ----------------------------------------------------------------------
# 8. 将新数据写入目标表 merged_data_specified
# ----------------------------------------------------------------------
def insert_new_data(engine, table_name, new_df):
    if new_df.empty:
        print("无新数据需要写入。")
        return
    try:
        # 处理数据类型，避免写入错误
        for col in new_df.columns:
            # 如果列名包含"%"但不是对象类型，转换为float
            if "%" in col and new_df[col].dtype != 'object':
                new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
            # 日期列确保是datetime
            elif col == "数据日期":
                new_df[col] = pd.to_datetime(new_df[col])
        
        print(f"开始写入 {len(new_df)} 条数据到 {table_name}...")
        new_df.to_sql(table_name, engine, if_exists='append', index=False)
        print(f"成功插入 {len(new_df)} 条新数据到 {table_name} 表中。")
    except Exception as e:
        print("写入数据库时出错：", e)
        # 尝试分批写入
        try:
            print("尝试分批写入数据...")
            batch_size = 100  # 每批写入的记录数
            for i in range(0, len(new_df), batch_size):
                batch = new_df.iloc[i:i+batch_size]
                batch.to_sql(table_name, engine, if_exists='append', index=False)
                print(f"已写入批次 {i//batch_size + 1}, 记录 {i} - {min(i+batch_size, len(new_df))}")
        except Exception as e2:
            print(f"分批写入也失败: {e2}")
            print("请检查数据类型是否与目标表结构匹配")

# ----------------------------------------------------------------------
# 9. 主函数：查询、合并、检测新数据并写入数据库
# ----------------------------------------------------------------------
def main():
    db_config = {
        "host": "rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com",
        "user": "hucongyanRoot",
        "password": "Hu123456",
        "database": "stock_analysis",
        "port": 3306
    }
    table_name = "merged_data_specified"
    engine = get_engine(db_config)
    
    # 检查目标表结构
    check_target_table(engine, table_name)
    
    # 1. 获取所有板块（从数据库动态获取）
    key_df, stock_dict = get_key_stocks(engine)
    codes = key_df["代码"].unique().tolist()
    names = key_df["名称"].unique().tolist()
    
    print(f"要更新的板块数量: {len(codes)}")
    print(f"板块代码示例: {codes[:5]} ..." if len(codes) > 5 else f"板块代码: {codes}")
    print(f"板块名称示例: {names[:5]} ..." if len(names) > 5 else f"板块名称: {names}")
    
    # 2. 获取目标表中最新数据日期（字段为 数据日期 ）
    latest_db_date = get_latest_date(engine, table_name)
    print("数据库中最新数据日期：", latest_db_date)
    
    # 3. 查询各相关表数据
    cf_df = query_capital_flow(engine, codes)
    print(f"资金流数据: {len(cf_df)} 条记录")
    
    dde_df = query_dde_analysis(engine, codes)
    print(f"DDE分析数据: {len(dde_df)} 条记录")
    
    pa_df = query_position_analysis(engine, codes)
    print(f"持仓分析数据: {len(pa_df)} 条记录")
    
    st_df = query_sector_trend(engine, names)
    print(f"板块趋势数据: {len(st_df)} 条记录")
    
    # 检查每个数据框的结构
    inspect_dataframe(cf_df, "资金流")
    inspect_dataframe(dde_df, "DDE分析") 
    inspect_dataframe(pa_df, "持仓分析")
    inspect_dataframe(st_df, "板块趋势")
    
    # 4. 如果目标表已有数据，则只取新日期数据（大于最新日期）
    if latest_db_date is not None:
        cf_df = cf_df[cf_df['日期'] > latest_db_date]
        dde_df = dde_df[dde_df['日期'] > latest_db_date]
        pa_df = pa_df[pa_df['日期'] > latest_db_date]
        st_df = st_df[st_df['日期'] > latest_db_date]
        
        print(f"过滤后资金流数据: {len(cf_df)} 条记录")
        print(f"过滤后DDE分析数据: {len(dde_df)} 条记录")
        print(f"过滤后持仓分析数据: {len(pa_df)} 条记录")
        print(f"过滤后板块趋势数据: {len(st_df)} 条记录")
    
    if cf_df.empty:
        print("没有检测到资金流新数据，目标表不更新。")
        return
    
    # 5. 合并各表数据（现在在merge_all_data函数内部将"日期"改为"数据日期"）
    merged_df = merge_all_data(key_df, cf_df, dde_df, pa_df, st_df)
    print(f"合并后数据: {len(merged_df)} 条记录")
    
    if merged_df.empty:
        print("合并后数据为空，目标表不更新。")
        return
        
    merged_df = merged_df.drop_duplicates(subset=["名称", "代码", "数据日期", "名称_cir"], keep="first")
    print(f"去重后数据: {len(merged_df)} 条记录")
    
    # 检查合并后的数据框
    inspect_dataframe(merged_df, "合并后数据")
    
    # 6. 过滤掉目标表中已存在的记录（按 数据日期, 代码, 名称, 名称_cir）
    new_df = filter_existing_data(engine, table_name, merged_df)
    print("最终待写入数据记录数：", len(new_df))
    
    if new_df.empty:
        print("没有新数据需要写入，目标表不更新。")
        return
    
    # 7. 重新排列字段顺序，确保与目标表对应
    new_df = reindex_columns(new_df)
    
    # 8. 写入新数据到目标表
    insert_new_data(engine, table_name, new_df)

if __name__ == "__main__":
    try:
        print("="*50)
        print("开始执行股票数据合并程序")
        print("="*50)
        main()
        print("="*50)
        print("程序执行完毕")
        print("="*50)
    except Exception as e:
        print("="*50)
        print(f"程序执行出错: {e}")
        print("="*50)