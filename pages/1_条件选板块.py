import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
from backend.db import db
from io import BytesIO

# 页面配置
st.set_page_config(page_title="条件选板块", page_icon="📈", layout="wide")

# 页面标题
st.title("📈 条件选板块")

# 定义可选择的数据表和对应的中文名称
TABLES = {
    'capital_flow': '资金流向',
    'dde_analysis': '主力行为',
    'position_analysis': '持仓分析',
    'sector_trend': '板块趋势',
    'market_trend': '大盘趋势',
    'bk_type_mapping': '板块类型映射'
}

# 定义每个表的可用字段和对应的中文名称
FIELDS = {
    'capital_flow': {
        '主力净流入': '主力净流入',
        '超大单净额': '超大单净额',
        '大单净额': '大单净额',
        '中单净额': '中单净额',
        '小单净额': '小单净额',
        '超大单流入': '超大单流入',
        '超大单流出': '超大单流出',
        '超大单净占比%': '超大单净占比%',
        '大单流入': '大单流入',
        '大单流出': '大单流出',
        '大单净占比%': '大单净占比%',
        '中单流入': '中单流入',
        '中单流出': '中单流出',
        '中单净占比%': '中单净占比%',
        '小单流入': '小单流入',
        '小单流出': '小单流出',
        '小单净占比%': '小单净占比%'
    },
    'dde_analysis': {
        'DDX': 'DDX指标',
        'DDY': 'DDY指标',
        'DDZ': 'DDZ指标',
        '5日DDX': '5日DDX',
        '5日DDY': '5日DDY',
        '10日DDX': '10日DDX',
        '10日DDY': '10日DDY',
        '连续': '连续',
        '5日内': '5日内',
        '10日内': '10日内',
        '特大买入%': '特大买入比例',
        '特大卖出%': '特大卖出比例',
        '特大单净比%': '特大单净比例',
        '大单买入%': '大单买入比例',
        '大单卖出%': '大单卖出比例',
        '大单净比%': '大单净比例'
    },
    'position_analysis': {
        '今日增仓占比': '1日增仓比例',
        '今日排名': '今日排名',
        '今日排名变化': '今日排名变化',
        '今日涨幅%': '今日涨幅',
        '3日增仓占比': '3日增仓比例',
        '3日排名': '3日排名',
        '3日排名变化': '3日排名变化',
        '3日涨幅%': '3日涨幅',
        '5日增仓占比': '5日增仓比例',
        '5日排名': '5日排名',
        '5日排名变化': '5日排名变化',
        '5日涨幅%': '5日涨幅',
        '10日增仓占比': '10日增仓比例',
        '10日排名': '10日排名',
        '10日排名变化': '10日排名变化',
        '10日涨幅%': '10日涨幅'
    },
    'sector_trend': {
        '涨幅%': '涨幅',
        '3日涨幅%': '3日涨幅',
        '涨速%': '涨速',
        '领涨股': '领涨股',
        '涨家数': '涨家数',
        '跌家数': '跌家数',
        '涨跌比': '涨跌比',
        '涨停家数': '涨停家数',
        '换手%': '换手率',
        '3日换手%': '3日换手率',
        '成交量': '成交量',
        '金额': '成交金额',
        '总市值': '总市值',
        '流通市值': '流通市值',
        '平均收益': '平均收益',
        '平均股本': '平均股本',
        '市盈率': '市盈率'
    },
    'market_trend': {
        'close_price': '收盘价',
        'change_ratio': '涨跌幅',
        'turnover': '成交额',
        'high_price': '最高价',
        'low_price': '最低价',
        'open_price': '开盘价',
        'pre_close': '昨收价'
    },
    'bk_type_mapping': {
        'board_type': '板块类型'
    }
}

# 定义条件运算符
OPERATORS = {
    '>': '大于',
    '>=': '大于等于',
    '<': '小于',
    '<=': '小于等于',
    '=': '等于',
    'continuous_>': '连续n天大于',
    'continuous_>=': '连续n天大于等于',
    'avg_>=': '大于等于n日均值',
    'avg_ratio_>=': '大于等于n日均值的m倍'
}

def format_condition_summary(condition):
    """格式化单个条件为人类可读的文本"""
    table_name = TABLES[condition['table']]
    field_name = FIELDS[condition['table']][condition['field']]
    operator = OPERATORS[condition['operator']]
    
    if 'continuous_' in condition['operator']:
        return f"{table_name}的{field_name}连续{condition['days']}天{operator.replace('连续n天','')} {condition['value']}"
    elif 'avg_ratio_' in condition['operator']:
        return f"{table_name}的{field_name}{operator.replace('n日均值的m倍','')} {condition['days']}日均值的{condition['value']}倍"
    elif 'avg_' in condition['operator']:
        return f"{table_name}的{field_name}{operator.replace('n日均值','')} {condition['days']}日均值"
    else:
        return f"{table_name}的{field_name} {operator} {condition['value']}"

def create_filter_area(area_name):
    """创建独立的筛选区域"""
    with st.expander(f"📊 筛选区 {area_name}", expanded=True):
        num_conditions = st.number_input(
            "条件数量",
            min_value=1,
            max_value=10,
            value=1,
            key=f"num_conditions_{area_name}"
        )
        
        conditions = []
        for i in range(num_conditions):
            st.markdown(f"##### 条件{i+1}")
            
            cols = st.columns([2, 2, 1.5, 1, 1])
            
            with cols[0]:
                table = st.selectbox(
                    f"选择数据表 #{i+1}",
                    options=list(TABLES.keys()),
                    format_func=lambda x: TABLES[x],
                    key=f'table_{area_name}_{i}'
                )
            
            with cols[1]:
                field = st.selectbox(
                    f"选择字段 #{i+1}",
                    options=list(FIELDS.get(table, {}).keys()),
                    format_func=lambda x: FIELDS[table][x],
                    key=f'field_{area_name}_{i}'
                )
            
            with cols[2]:
                operator = st.selectbox(
                    f"条件 #{i+1}",
                    options=list(OPERATORS.keys()),
                    format_func=lambda x: OPERATORS[x],
                    key=f'operator_{area_name}_{i}',
                    index=0 if i > 0 else list(OPERATORS.keys()).index('continuous_>')
                )
            
            with cols[3]:
                if 'continuous_' in operator or 'avg_' in operator:
                    days = st.number_input(
                        "天数",
                        min_value=1,
                        value=3 if i == 0 else 1,
                        key=f'days_{area_name}_{i}'
                    )
                else:
                    days = 0
            
            with cols[4]:
                if 'avg_ratio_' in operator:
                    value = st.number_input(
                        "倍数",
                        value=1.5,
                        step=0.1,
                        format='%f',
                        key=f'value_{area_name}_{i}'
                    )
                else:
                    value = st.number_input(
                        "数值",
                        value=0.0,
                        step=1.0,
                        format='%f',
                        key=f'value_{area_name}_{i}'
                    )
            
            conditions.append({
                'table': table,
                'field': field,
                'operator': operator,
                'days': days,
                'value': value
            })
        
        # 存储条件到session state
        if 'filter_conditions' not in st.session_state:
            st.session_state.filter_conditions = {}
        st.session_state.filter_conditions[area_name] = conditions
        
        # 显示条件摘要
        if conditions:
            st.markdown("**筛选条件摘要:**")
            for i, condition in enumerate(conditions):
                st.markdown(f"- {format_condition_summary(condition)}")

def build_stock_query(conditions, board_type=None):
    """构建股票筛选SQL查询"""
    sub_queries = []
    detail_columns = []  # 用于存储需要显示的详细列
    detail_joins = []    # 用于存储需要JOIN的子查询
    has_sector_trend = False  # 标记是否使用了sector_trend表
    
    for i, condition in enumerate(conditions):
        table = condition['table']
        field = condition['field']
        operator = condition['operator']
        value = float(condition['value'])
        days = condition['days']
        
        # 为sector_trend表使用特殊处理
        if table == "sector_trend":
            has_sector_trend = True
            
        # 连续N天条件
        if 'continuous_' in operator:
            op = operator.replace('continuous_', '')
            
            # 添加连续天数的数据到展示列
            for day in range(1, days + 1):
                detail_columns.append(f"day{i}_{day}.`{field}` AS `{field}_day{day}`")
            
            # 为每一天创建JOIN，特殊处理sector_trend表
            for day in range(1, days + 1):
                if table == "sector_trend":
                    detail_joins.append(f"""
                    LEFT JOIN (
                        SELECT 
                            `名称` as code_match, 
                            `{field}`
                        FROM (
                            SELECT 
                                `名称`, 
                                `{field}`,
                                ROW_NUMBER() OVER(PARTITION BY `名称` ORDER BY `数据日期` DESC) as row_num
                            FROM `{table}`
                        ) ranked
                        WHERE row_num = {day}
                    ) day{i}_{day} ON cf.`名称` = day{i}_{day}.code_match
                    """)
                else:
                    detail_joins.append(f"""
                    LEFT JOIN (
                        SELECT 
                            `代码` as code_match, 
                            `{field}`
                        FROM (
                            SELECT 
                                `代码`, 
                                `{field}`,
                                ROW_NUMBER() OVER(PARTITION BY `代码` ORDER BY `数据日期` DESC) as row_num
                            FROM `{table}`
                        ) ranked
                        WHERE row_num = {day}
                    ) day{i}_{day} ON cf.`代码` = day{i}_{day}.code_match
                    """)
            
            # 使用窗口函数找出连续满足条件的记录
            if table == "sector_trend":
                sub_query = f"""
                SELECT t1.`名称` as matching_code
                FROM (
                    SELECT 
                        `名称`,
                        `数据日期`,
                        `{field}`,
                        ROW_NUMBER() OVER(PARTITION BY `名称` ORDER BY `数据日期` DESC) as date_rank
                    FROM `{table}`
                ) as t1
                WHERE t1.date_rank <= {days}
                AND t1.`{field}` {op} {value}
                GROUP BY t1.`名称`
                HAVING COUNT(t1.`名称`) = {days}
                """
            else:
                sub_query = f"""
                SELECT t1.`代码` as matching_code
                FROM (
                    SELECT 
                        `代码`,
                        `数据日期`,
                        `{field}`,
                        ROW_NUMBER() OVER(PARTITION BY `代码` ORDER BY `数据日期` DESC) as date_rank
                    FROM `{table}`
                ) as t1
                WHERE t1.date_rank <= {days}
                AND t1.`{field}` {op} {value}
                GROUP BY t1.`代码`
                HAVING COUNT(t1.`代码`) = {days}
                """
            sub_queries.append((sub_query, table))
            
        elif 'avg_' in operator:
            # 均值条件处理... (省略)
            pass
            
        else:
            # 普通条件 - 添加最新值到明细展示
            detail_columns.append(f"latest{i}.`{field}` AS `{field}_latest`")
            
            # 创建JOIN获取最新值，特殊处理sector_trend表
            if table == "sector_trend":
                detail_joins.append(f"""
                LEFT JOIN (
                    SELECT 
                        `名称` as code_match, 
                        `{field}`
                    FROM `{table}`
                    WHERE `数据日期` = (SELECT MAX(`数据日期`) FROM `{table}`)
                ) latest{i} ON cf.`名称` = latest{i}.code_match
                """)
                
                # 普通条件查询
                sub_query = f"""
                SELECT `名称` as matching_code
                FROM `{table}`
                WHERE `数据日期` = (SELECT MAX(`数据日期`) FROM `{table}`)
                AND `{field}` {operator} {value}
                """
            else:
                detail_joins.append(f"""
                LEFT JOIN (
                    SELECT 
                        `代码` as code_match, 
                        `{field}`
                    FROM `{table}`
                    WHERE `数据日期` = (SELECT MAX(`数据日期`) FROM `{table}`)
                ) latest{i} ON cf.`代码` = latest{i}.code_match
                """)
                
                # 普通条件查询
                sub_query = f"""
                SELECT `代码` as matching_code
                FROM `{table}`
                WHERE `数据日期` = (SELECT MAX(`数据日期`) FROM `{table}`)
                AND `{field}` {operator} {value}
                """
            sub_queries.append((sub_query, table))
    
    # 组合所有子查询（交集）
    if not sub_queries:
        return None, []
    
    # 预处理子查询，处理sector_trend表的特殊情况
    processed_queries = []
    
    for query, table in sub_queries:
        if table == "sector_trend":
            # 对于sector_trend表，需要使用名称进行匹配
            processed_query = f"""
            SELECT cf.`代码` as matching_code
            FROM `capital_flow` cf
            JOIN ({query}) st ON cf.`名称` = st.matching_code
            WHERE cf.`数据日期` = (SELECT MAX(`数据日期`) FROM `capital_flow`)
            """
            processed_queries.append(processed_query)
        else:
            processed_queries.append(query)
    
    # MySQL 5.x不支持INTERSECT，使用JOIN或WITH子句代替
    if len(processed_queries) == 1:
        combined_query = processed_queries[0]
    else:
        # 使用WITH子句实现交集
        combined_query = f"""
        WITH query1 AS ({processed_queries[0]})
        """
        for i, query in enumerate(processed_queries[1:], 1):
            combined_query += f"""
            , query{i+1} AS ({query})
            """
        
        combined_query += """
        SELECT q1.matching_code
        FROM query1 q1
        """
        
        for i in range(1, len(processed_queries)):
            combined_query += f"""
            JOIN query{i+1} q{i+1} ON q1.matching_code = q{i+1}.matching_code
            """
    
    # 构建最终查询 - 动态添加详细信息列
    detail_columns_str = ""
    if detail_columns:
        detail_columns_str = ", " + ", ".join(detail_columns)
    
    # 拼接JOIN语句
    detail_joins_str = " ".join(detail_joins)
    
    # 构建板块类型过滤条件
    board_type_filter = ""
    if board_type:
        board_type_filter = f" AND bkt.`board_type` = '{board_type}'"
    
    final_query = f"""
    SELECT 
        cf.`代码` as ts_code,
        cf.`名称` as name,
        COALESCE(bkt.`board_type`, '未知') as 板块类型,
        cf.`主力净流入`,
        cf.`超大单净额` as 超大单净流入,
        cf.`大单净额` as 大单净流入,
        cf.`中单净额` as 中单净流入,
        cf.`小单净额` as 小单净流入,
        dde.`DDX` as dde_value,
        pos.`今日增仓占比` as position_value,
        cf.`数据日期` as flow_date{detail_columns_str}
    FROM `capital_flow` cf
    LEFT JOIN `dde_analysis` dde ON cf.`代码` = dde.`代码` 
      AND dde.`数据日期` = (SELECT MAX(`数据日期`) FROM `dde_analysis`)
    LEFT JOIN `position_analysis` pos ON cf.`代码` = pos.`代码` 
      AND pos.`数据日期` = (SELECT MAX(`数据日期`) FROM `position_analysis`)
    LEFT JOIN `bk_type_mapping` bkt ON cf.`代码` = bkt.`bk_code`
    {detail_joins_str}
    WHERE cf.`数据日期` = (SELECT MAX(`数据日期`) FROM `capital_flow`)
    AND cf.`代码` IN ({combined_query}){board_type_filter}
    """
    
    return final_query, detail_columns

def execute_query(query):
    """执行SQL查询"""
    if not query:
        st.error("没有有效的查询条件")
        return pd.DataFrame()
    
    try:
        # 将SQL查询放在可展开区域，默认隐藏
        with st.expander("🔍 查看执行的SQL查询", expanded=False):
            st.code(query, language="sql")
        
        # 执行完整查询
        results_df = db.query_to_dataframe(query)
        st.write(f"查询成功，获取到 {len(results_df)} 条记录")
        return results_df
        
    except Exception as e:
        st.error("查询执行出错")
        with st.expander("🔍 查看错误详情", expanded=True):
            st.exception(e)
            
            # 保留简化查询以便诊断问题
            try:
                st.subheader("尝试执行简化查询...")
                simple_query = """
                SELECT COUNT(*) as total 
                FROM `capital_flow` 
                WHERE `数据日期` = (SELECT MAX(`数据日期`) FROM `capital_flow`)
                """
                st.code(simple_query, language="sql")
                test_df = db.query_to_dataframe(simple_query)
                st.write(f"简化查询成功，共有 {test_df.iloc[0]['total']} 条记录")
                
                # 检查MySQL版本
                st.subheader("检查MySQL版本兼容性...")
                version_query = """
                SELECT VERSION() as mysql_version
                """
                version_df = db.query_to_dataframe(version_query)
                if not version_df.empty:
                    st.write(f"MySQL版本: {version_df.iloc[0]['mysql_version']}")
            except Exception as test_e:
                st.error(f"简化查询也失败: {str(test_e)}")
        
        return pd.DataFrame()

def main():
    """主函数"""
    # 添加全局板块类型过滤
    with st.expander("🔍 全局板块类型过滤", expanded=True):
        board_type_options = {
            "全部板块": None,
            "概念板块": "概念", 
            "行业板块": "行业", 
            "地区板块": "地区", 
            "风格板块": "风格"
        }
        
        selected_board_type_display = st.selectbox(
            "选择要显示的板块类型", 
            list(board_type_options.keys()),
            index=0,  # 默认选择"全部板块"
            key="global_board_type_filter"  # 添加唯一的key
        )
        selected_board_type = board_type_options[selected_board_type_display]
        
        if selected_board_type:
            st.success(f"已设置全局过滤: 只显示{selected_board_type_display}结果")
        else:
            st.info("当前显示所有类型的板块")
    
    # 筛选区数量设置
    col1, col2 = st.columns([0.3, 0.7])
    with col1:
        st.write("📊 筛选区数量")
    with col2:
        num_areas = st.number_input(
            "",
            min_value=1,
            max_value=5,
            value=1,
            key="num_filter_areas",
            label_visibility="collapsed"
        )
    
    # 创建多个筛选区
    for area_idx in range(num_areas):
        area_name = chr(65 + area_idx)  # A, B, C...
        create_filter_area(area_name)
    
    # 统一执行按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        execute_button = st.button("执行全部筛选", type="primary", use_container_width=True)
    
    if execute_button:
        if 'filter_conditions' in st.session_state:
            # 清空之前的筛选结果
            if 'filter_results' not in st.session_state:
                st.session_state.filter_results = {}
            else:
                st.session_state.filter_results.clear()
            
            # 在按钮下方显示结果区域
            st.markdown("## 筛选结果")
            
            # 显示当前使用的过滤条件
            if selected_board_type:
                st.info(f"全局板块类型过滤: 只显示{selected_board_type_display}")
            
            # 创建进度条
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            # 获取当前显示的筛选区
            active_areas = [chr(65 + i) for i in range(num_areas)]
            total_areas = len([name for name in st.session_state.filter_conditions.keys() if name in active_areas])
            
            for i, area_name in enumerate([name for name in st.session_state.filter_conditions.keys() if name in active_areas]):
                # 更新进度
                progress = int((i / total_areas) * 100)
                progress_bar.progress(progress)
                progress_text.text(f"处理筛选区 {area_name} ({i+1}/{total_areas})...")
                
                # 创建结果容器
                result_container = st.container()
                with result_container:
                    st.markdown(f"### 筛选区 {area_name} 结果")
                    
                    conditions = st.session_state.filter_conditions[area_name]
                    # 没有条件时跳过
                    if not conditions:
                        st.warning("没有设置筛选条件")
                        continue
                    
                    try:
                        # 构建并执行查询
                        query, detail_columns = build_stock_query(conditions, selected_board_type)
                        results_df = execute_query(query)
                        
                        # 显示结果
                        if not results_df.empty:
                            # 使用列布局显示统计信息 - 简化为只显示股票数量
                            st.success(f"找到 {len(results_df)} 只符合条件的股票")
                            
                            # 显示板块类型统计信息
                            if '板块类型' in results_df.columns:
                                board_type_counts = results_df['板块类型'].value_counts()
                                if not board_type_counts.empty:
                                    with st.expander("板块类型分布", expanded=False):
                                        for btype, count in board_type_counts.items():
                                            st.write(f"{btype}: {count}只")
                            
                            # 保存结果以便稍后分析
                            st.session_state.filter_results[area_name] = results_df
                            
                            # 格式化数值列
                            display_df = results_df.copy()
                            
                            # 标识重要的展示列
                            special_columns = []
                            for condition in conditions:
                                field = condition['field']
                                operator = condition['operator']
                                days = condition['days']
                                
                                # 对于连续天数条件，标记相关列以突出显示
                                if 'continuous_' in operator:
                                    for day in range(1, days + 1):
                                        col_name = f"{field}_day{day}"
                                        if col_name in display_df.columns:
                                            special_columns.append(col_name)
                                # 对于普通条件，标记最新值列
                                else:
                                    col_name = f"{field}_latest"
                                    if col_name in display_df.columns:
                                        special_columns.append(col_name)
                            
                            # 设置数字格式
                            numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
                            format_dict = {}
                            for col in numeric_cols:
                                if '净流入' in col or '净额' in col or '_day' in col or '_latest' in col:
                                    format_dict[col] = '{:,.2f}'
                                elif '_ratio' in col:
                                    format_dict[col] = '{:.2f}'
                            
                            # 移除主表格，只保留详情表
                            if special_columns and len(special_columns) > 0:
                                # 创建只包含必要列的详情视图
                                detail_view = display_df[['ts_code', 'name', '板块类型'] + special_columns].copy()
                                # 直接显示详情视图作为主表格
                                st.dataframe(detail_view.style.format(format_dict), use_container_width=True)
                            else:
                                # 如果没有特殊列，则显示基本表格
                                basic_columns = ['ts_code', 'name', '板块类型', '主力净流入', 'flow_date']
                                basic_view = display_df[basic_columns].copy()
                                st.dataframe(basic_view.style.format(format_dict), use_container_width=True)
                        else:
                            st.warning("没有找到符合条件的股票")
                    except Exception as e:
                        st.error(f"查询出错: {str(e)}")
            
            # 完成所有查询
            progress_bar.progress(100)
            progress_text.text("所有筛选区处理完成!")
            
            # 查询完成后显示共同股票分析 - 保留此功能
            if len(st.session_state.filter_results) > 1:
                st.markdown("### 🔍 共同股票分析")
                
                # 获取所有筛选区的股票集合
                stock_sets = {name: set(df['ts_code']) for name, df in st.session_state.filter_results.items()}
                
                # 计算交集
                intersection = set.intersection(*stock_sets.values())
                if intersection:
                    # 创建共同股票的详细信息DataFrame
                    common_stocks = pd.DataFrame({
                        '股票代码': list(intersection),
                        '股票名称': [next(df[df['ts_code'] == code]['name'].iloc[0] 
                                    for df in st.session_state.filter_results.values() 
                                    if code in df['ts_code'].values) 
                                for code in intersection],
                        '板块类型': [next(df[df['ts_code'] == code]['板块类型'].iloc[0] 
                                   for df in st.session_state.filter_results.values() 
                                   if code in df['ts_code'].values) 
                               for code in intersection]
                    })
                    
                    # 显示结果统计 - 简化为只显示股票数量
                    st.success(f"发现 {len(intersection)} 只在所有筛选区中都出现的股票")
                    
                    # 显示共同股票表格
                    st.dataframe(common_stocks, use_container_width=True)
                    
                    # 保留导出功能
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        common_stocks.to_excel(writer, sheet_name="共同股票", index=False)
                        for name, df in st.session_state.filter_results.items():
                            df.to_excel(writer, sheet_name=f"筛选区{name}完整结果", index=False)
                    
                    excel_data = output.getvalue()
                    st.download_button(
                        label="导出分析结果",
                        data=excel_data,
                        file_name=f"选股分析结果_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                else:
                    st.info("没有在所有筛选区中都出现的股票")
    
    # 使用说明
    with st.expander("使用说明"):
        st.markdown("""
        ### 使用说明
        1. 选择需要的筛选区数量（1-5个）
        2. 在每个筛选区中设置筛选条件
        3. 点击底部的"执行全部筛选"按钮
        4. 查看各个筛选区的结果和共同股票分析
        
        #### 条件类型说明：
        - **普通条件**（如：大于、小于等）：比较最新交易日的数据
        - **连续n天条件**：从最新交易日起往前连续n天都满足条件
        - **均值条件**：将最新交易日的数据与n日均值进行比较
        
        #### 特别说明：
        - 所有条件都基于数据库最新交易日的数据进行计算和比较
        - 可以导出筛选结果和共同股票分析
        """)

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")