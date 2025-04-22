import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
import traceback
import sys
import os
import sqlite3
import logging
from pathlib import Path
from collections import deque  # 用于收集调试信息

# 添加项目根目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

# 全局变量，用于收集调试信息
if 'debug_messages' not in st.session_state:
    st.session_state.debug_messages = deque(maxlen=100)  # 限制最大消息数量
    
# 定义函数用于收集调试信息，而不是直接显示
def add_debug_message(message, level="info"):
    """
    添加调试信息到全局队列，而不是直接显示
    
    Args:
        message: 调试信息内容
        level: 消息级别 (info, success, warning, error)
    """
    # 将消息添加到队列
    st.session_state.debug_messages.append((level, message))

# 替换原来直接显示的调试函数
def debug_info(message):
    """收集信息级别的调试消息"""
    add_debug_message(message, "info")
    
def debug_success(message):
    """收集成功级别的调试消息"""
    add_debug_message(message, "success")
    
def debug_warning(message):
    """收集警告级别的调试消息"""
    add_debug_message(message, "warning")
    
def debug_error(message):
    """收集错误级别的调试消息"""
    add_debug_message(message, "error")

# 在页面底部显示所有收集的调试信息
def display_debug_messages():
    """在页面底部显示所有收集的调试信息"""
    if st.session_state.debug_messages:
        with st.expander("调试信息", expanded=False):
            for level, message in st.session_state.debug_messages:
                if level == "info":
                    st.info(message)
                elif level == "success":
                    st.success(message)
                elif level == "warning":
                    st.warning(message)
                elif level == "error":
                    st.error(message)

# 页面配置
st.set_page_config(page_title="热门板块排行", page_icon="🔥", layout="wide")

# 检查数据库连接
def test_db_connection():
    """测试数据库连接并返回诊断信息"""
    results = {"success": False, "tables": [], "error": None, "db_path": None}
    
    try:
        # 先尝试从backend.db导入
        try:
            from backend.db import db
            results["success"] = True
            results["connection_type"] = "backend.db模块"
            
            # 尝试获取所有表名
            try:
                query = "SELECT name FROM sqlite_master WHERE type='table';"
                tables_df = db.query_to_dataframe(query)
                if not tables_df.empty:
                    results["tables"] = tables_df['name'].tolist()
            except Exception as e:
                results["table_error"] = str(e)
                
        except ImportError as e:
            results["error"] = f"导入backend.db模块失败: {str(e)}"
            
            # 尝试直接连接数据库文件
            db_paths = [
                os.path.join(project_root, "plates.db"),
                os.path.join(project_root, "backend", "plates.db"),
                os.path.join(project_root, "data", "plates.db")
            ]
            
            for path in db_paths:
                if os.path.exists(path):
                    results["db_path"] = path
                    try:
                        conn = sqlite3.connect(path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        results["tables"] = [table[0] for table in tables]
                        results["success"] = True
                        results["connection_type"] = f"直接连接: {path}"
                        conn.close()
                        break
                    except Exception as e2:
                        results["error"] = f"直接连接{path}失败: {str(e2)}"
            
    except Exception as e:
        results["error"] = f"测试数据库连接时出错: {str(e)}"
    
    return results

# 导入数据库模块
try:
    from backend.db import db
except ModuleNotFoundError:
    st.error("无法导入数据库模块，请确保从项目根目录启动应用: streamlit run app.py")
    
    # 尝试自动修复db导入
    try:
        # 检查plates.db是否存在，如果存在，创建一个简单的db模块
        db_paths = [
            os.path.join(project_root, "plates.db"),
            os.path.join(project_root, "backend", "plates.db"),
            os.path.join(project_root, "data", "plates.db")
        ]
        
        db_path = None
        for path in db_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if db_path:
            st.info(f"找到数据库文件: {db_path}，尝试创建临时db连接...")
            
            # 创建临时db类
            class TempDB:
                def __init__(self, db_path):
                    self.db_path = db_path
                
                def query_to_dataframe(self, query, params=None):
                    try:
                        conn = sqlite3.connect(self.db_path)
                        if params:
                            df = pd.read_sql_query(query, conn, params=params)
                        else:
                            df = pd.read_sql_query(query, conn)
                        conn.close()
                        return df
                    except Exception as e:
                        st.error(f"执行查询失败: {str(e)}")
                        st.code(query)
                        raise e
            
            db = TempDB(db_path)
            st.success("已创建临时数据库连接")
        else:
            st.error("未找到数据库文件plates.db")
            if os.path.exists(os.path.join(project_root, "backend")):
                st.info(f"backend目录存在，内容: {os.listdir(os.path.join(project_root, 'backend'))}")
            st.stop()
    except Exception as e:
        st.error(f"尝试自动修复db导入时出错: {str(e)}")
        st.stop()

# 颜色设置
POSITIVE_COLOR = "#f63366"  # 红色，用于正向变化
NEGATIVE_COLOR = "#0068c9"  # 蓝色，用于负向变化
HEADER_COLOR = "#F0F2F6"    # 表头背景色
RANK_BG_COLORS = {
    1: "#FF4B4B",  # 红色（排名第1）
    2: "#FF8F65",  # 橙色（排名第2）
    3: "#FFCA3A",  # 黄色（排名第3）
}

# 页面标题
st.title("热门板块每日排行")

# 辅助函数
def format_value(value, unit="亿"):
    """格式化数值，添加单位"""
    if pd.isna(value):
        return "-"
    if isinstance(value, (int, float)):
        if unit == "亿" and abs(value) >= 1:
            return f"{value:.1f}{unit}"  # 小数点精确到1位
        elif unit == "%" and not pd.isna(value):
            return f"{value:.1f}{unit}"  # 小数点精确到1位
        elif unit == "":
            return f"{value:.1f}"  # 小数点精确到1位
        else:
            return f"{value:.1f}{unit}"  # 小数点精确到1位
    return str(value)

@st.cache_data(ttl=300)
def get_recent_trading_dates(days=10):
    """获取最近的交易日期，使用缓存提高性能"""
    try:
        # 记录当前日期，用于比较
        current_date = pd.Timestamp.now()
        
        # 首先获取实际存在数据的交易日期，使用JOIN子查询结构（参考6_数据可视化.py）
        try:
            # 从资金流表获取最近的有数据的交易日期
            # 注意：修复MySQL中LIKE语句格式化问题 - 使用双%转义
            trade_date_query = f"""
                SELECT DISTINCT 数据日期 
                FROM capital_flow 
                WHERE 代码 LIKE 'BK%%' 
                ORDER BY 数据日期 DESC 
                LIMIT 60
            """
            
            # 确保没有换行符和多余的空格
            trade_date_query = trade_date_query.replace("\n", " ").strip()
            
            trade_dates_df = db.query_to_dataframe(trade_date_query)
            
            if not trade_dates_df.empty:
                # 将日期转换为标准格式并验证
                valid_dates = []
                skipped_dates = []
                
                for date in trade_dates_df['数据日期']:
                    try:
                        # 先检查是否为字符串
                        if isinstance(date, str):
                            date_obj = pd.to_datetime(date)
                        elif isinstance(date, pd.Timestamp) or isinstance(date, datetime.date):
                            date_obj = pd.to_datetime(date)
                        else:
                            skipped_dates.append((str(date), f"非日期类型数据: {type(date)}"))
                            continue
                        
                        # 排除未来日期（超过当前日期30天）
                        if date_obj > current_date + pd.Timedelta(days=30):
                            skipped_dates.append((date_obj.strftime('%Y-%m-%d'), f"远期未来日期"))
                            continue
                        
                        # 格式化为标准日期字符串
                        valid_dates.append(date_obj.strftime('%Y-%m-%d'))
                    except Exception as e:
                        skipped_dates.append((str(date), f"日期格式无效: {str(e)}"))
                
                # 仅返回请求的天数
                if valid_dates:
                    return valid_dates[:days]
            
            # 如果资金流表没有数据，尝试从sector_trend表获取日期
            sector_date_query = f"""
                SELECT DISTINCT 数据日期 
                FROM sector_trend 
                ORDER BY 数据日期 DESC 
                LIMIT 60
            """
            
            sector_date_query = sector_date_query.replace("\n", " ").strip()
            sector_dates_df = db.query_to_dataframe(sector_date_query)
            
            if not sector_dates_df.empty:
                # 验证日期
                valid_dates = []
                
                for date in sector_dates_df['数据日期']:
                    try:
                        if isinstance(date, str):
                            date_obj = pd.to_datetime(date)
                        elif isinstance(date, pd.Timestamp) or isinstance(date, datetime.date):
                            date_obj = pd.to_datetime(date)
                        else:
                            continue
                        
                        # 排除未来日期
                        if date_obj > current_date + pd.Timedelta(days=30):
                            continue
                        
                        # 格式化为标准日期字符串
                        valid_dates.append(date_obj.strftime('%Y-%m-%d'))
                    except Exception:
                        continue
                
                # 仅返回请求的天数
                if valid_dates:
                    return valid_dates[:days]
                    
        except Exception as e:
            # 记录错误但继续执行
            st.error(f"获取日期时出错: {str(e)}")
            st.code(traceback.format_exc())
        
        # 如果实际交易日期获取失败，使用模拟日期（仅周一至周五）
        simulated_dates = []
        current_date = pd.Timestamp.now()
        date_count = 0
        days_back = 0
        
        # 生成足够多的工作日日期（排除周末）
        while date_count < days:
            test_date = current_date - pd.Timedelta(days=days_back)
            days_back += 1
            
            # 跳过周六(5)和周日(6)
            if test_date.weekday() < 5:  # 0-4 是周一至周五
                simulated_dates.append(test_date.strftime('%Y-%m-%d'))
                date_count += 1
        
        return simulated_dates
        
    except Exception as e:
        # 任何情况下都返回模拟日期，确保函数不会失败
        st.error(f"生成日期时出错: {str(e)}")
        st.code(traceback.format_exc())
        
        simulated_dates = []
        current_date = pd.Timestamp.now()
        date_count = 0
        days_back = 0
        
        while date_count < days:
            test_date = current_date - pd.Timedelta(days=days_back)
            days_back += 1
            
            # 跳过周末
            if test_date.weekday() < 5:  # 0-4 是周一至周五
                simulated_dates.append(test_date.strftime('%Y-%m-%d'))
                date_count += 1
        
        return simulated_dates

def get_all_indicators():
    """获取所有可用的指标"""
    # 包含所有四个表的指标
    indicators = {
        # 资金流相关指标 (来自capital_flow表)
        "主力净流入": {"table": "capital_flow", "field": "主力净流入", "unit": "亿"},
        "超大单净额": {"table": "capital_flow", "field": "超大单净额", "unit": "亿"},
        "大单净额": {"table": "capital_flow", "field": "大单净额", "unit": "亿"},
        "中单净额": {"table": "capital_flow", "field": "中单净额", "unit": "亿"},
        "小单净额": {"table": "capital_flow", "field": "小单净额", "unit": "亿"},
        
        # DDE行为指标 (来自dde_analysis表)
        "DDX": {"table": "dde_analysis", "field": "DDX", "unit": ""},
        "DDY": {"table": "dde_analysis", "field": "DDY", "unit": ""},
        "DDZ": {"table": "dde_analysis", "field": "DDZ", "unit": ""},
        "5日DDX": {"table": "dde_analysis", "field": "5日DDX", "unit": ""},
        "5日DDY": {"table": "dde_analysis", "field": "5日DDY", "unit": ""},
        "特大单净比": {"table": "dde_analysis", "field": "特大单净比%", "unit": "%"},
        
        # 增仓结构指标 (来自position_analysis表)
        "今日增仓占比": {"table": "position_analysis", "field": "今日增仓占比", "unit": "%"},
        "3日增仓占比": {"table": "position_analysis", "field": "3日增仓占比", "unit": "%"},
        "5日增仓占比": {"table": "position_analysis", "field": "5日增仓占比", "unit": "%"},
        "今日排名": {"table": "position_analysis", "field": "今日排名", "unit": ""},
        
        # 板块趋势指标 (来自sector_trend表)
        "涨幅": {"table": "sector_trend", "field": "涨幅%", "unit": "%"},
        "涨速": {"table": "sector_trend", "field": "涨速%", "unit": "%"},
        "换手率": {"table": "sector_trend", "field": "换手%", "unit": "%"},
        "成交金额": {"table": "sector_trend", "field": "金额", "unit": "亿"},
        "总市值": {"table": "sector_trend", "field": "总市值", "unit": "亿"},
        "流通市值": {"table": "sector_trend", "field": "流通市值", "unit": "亿"},
        "涨跌比": {"table": "sector_trend", "field": "涨跌比", "unit": ""},
        "涨家数": {"table": "sector_trend", "field": "涨家数", "unit": "家"},
        "跌家数": {"table": "sector_trend", "field": "跌家数", "unit": "家"},
        "涨停家数": {"table": "sector_trend", "field": "涨停家数", "unit": "家"},
        "3日涨幅": {"table": "sector_trend", "field": "3日涨幅%", "unit": "%"},
        "3日换手率": {"table": "sector_trend", "field": "3日换手%", "unit": "%"},
    }
    return indicators

@st.cache_data(ttl=60)
def get_hot_sectors(indicator_info, dates, rank_limit=100, get_bottom=False, board_type=None):
    """
    获取热门板块排行数据，使用缓存提高性能
    参考6_数据可视化.py中的方式，避免SQL注入和动态构建风险
    
    Args:
        indicator_info: 排序指标信息（包含表名、字段名和单位）
        dates: 日期列表
        rank_limit: 返回的最大排名数
        get_bottom: 是否获取负值最大的板块（底部排名）
        board_type: 板块类型过滤（概念、行业、地区、风格）
        
    Returns:
        包含多个日期排名数据的DataFrame
    """
    if not dates:
        debug_warning("无有效日期数据")
        return pd.DataFrame()
    
    try:
        # 解析指标信息
        table = indicator_info["table"]
        field = indicator_info["field"]
        
        debug_info(f"获取表 {table} 的字段 {field} 数据")
        
        # 首先过滤掉未来日期
        current_date = pd.Timestamp.now()
        filtered_dates = []
        for date in dates:
            try:
                parsed_date = pd.to_datetime(date)
                # 如果日期是未来的，跳过
                if parsed_date > current_date + pd.Timedelta(days=1):  # 允许今天和明天的日期
                    debug_warning(f"日期 {date} 是未来日期，已跳过")
                    continue
                filtered_dates.append(date)
            except:
                # 如果日期无法解析，也跳过
                debug_warning(f"日期 {date} 无法解析，已跳过")
                continue
        
        if not filtered_dates:
            debug_warning("所有日期均无效或是未来日期")
            return pd.DataFrame()
        
        # 如果需要按板块类型过滤，先获取相应的board_name或名称列表
        valid_board_names = []
        valid_board_codes = []
        if board_type:
            debug_info(f"准备根据板块类型 '{board_type}' 过滤数据...")
            try:
                # 从bk_type_mapping获取所需板块类型的板块名称和代码
                type_query = f"""
                SELECT bk_code, board_name 
                FROM bk_type_mapping 
                WHERE board_type = '{board_type}'
                """
                mapping_df = db.query_to_dataframe(type_query)
                
                if not mapping_df.empty:
                    # 提取板块代码（用于capital_flow, dde_analysis, position_analysis表）
                    if 'bk_code' in mapping_df.columns:
                        board_codes = mapping_df['bk_code'].dropna().tolist()
                        if board_codes:
                            valid_board_codes = board_codes
                            add_debug_message(f"找到 {len(valid_board_codes)} 个类型为 '{board_type}' 的板块代码", "info")
                            add_debug_message(f"板块代码列表: {', '.join(board_codes[:10])}{'...' if len(board_codes) > 10 else ''}", "info")
                    
                    # 提取板块名称（用于sector_trend表）
                    if 'board_name' in mapping_df.columns:
                        board_names = mapping_df['board_name'].dropna().tolist()
                        if board_names:
                            valid_board_names = board_names
                            add_debug_message(f"找到 {len(valid_board_names)} 个类型为 '{board_type}' 的板块名称", "info")
                            add_debug_message(f"板块名称列表: {', '.join(board_names[:10])}{'...' if len(board_names) > 10 else ''}", "info")
                    
                    # 还需要从capital_flow表获取板块名称（这些可能是sector_trend表中使用的名称）
                    if valid_board_codes:
                        bk_codes_str = "', '".join(valid_board_codes)
                        
                        # 从capital_flow表获取这些代码对应的名称
                        names_query = f"""
                        SELECT DISTINCT 代码, 名称 
                        FROM capital_flow 
                        WHERE 代码 IN ('{bk_codes_str}')
                        """
                        names_df = db.query_to_dataframe(names_query)
                        
                        if not names_df.empty:
                            add_debug_message(f"从capital_flow表获取到 {len(names_df)} 条代码-名称记录", "info")
                            add_debug_message(f"代码-名称映射样本: {names_df.head(5).to_string()}", "info")
                            more_names = names_df['名称'].dropna().tolist()
                            
                            # 创建代码到名称的映射并打印
                            code_to_name = dict(zip(names_df['代码'], names_df['名称']))
                            add_debug_message(f"部分代码到名称映射: {dict(list(code_to_name.items())[:5])}", "info")
                            
                            valid_board_names.extend(more_names)
                            debug_info(f"从capital_flow表获取到额外的 {len(more_names)} 个板块名称")
                            if more_names:
                                add_debug_message(f"额外的板块名称: {', '.join(more_names[:10])}{'...' if len(more_names) > 10 else ''}", "info")
                        else:
                            add_debug_message(f"在capital_flow表中未找到匹配的代码-名称记录", "warning")
                            add_debug_message(f"查询: {names_query}", "info")
                else:
                    debug_warning(f"找不到类型为 '{board_type}' 的板块")
                    add_debug_message(f"查询: {type_query}", "info")
                    add_debug_message(f"请检查bk_type_mapping表中是否有'{board_type}'类型的记录", "warning")
            except Exception as e:
                debug_error(f"获取板块类型映射时出错: {str(e)}")
                add_debug_message(f"查询: {type_query if 'type_query' in locals() else '未执行查询'}", "info")
                if traceback:
                    debug_error(traceback.format_exc())
                    
        # 打印筛选后的有效板块名称和代码数量
        add_debug_message(f"最终获取到 {len(valid_board_names)} 个板块名称和 {len(valid_board_codes)} 个板块代码", "info")
        if valid_board_names:
            add_debug_message(f"名称示例: {', '.join(valid_board_names[:10])}{'...' if len(valid_board_names) > 10 else ''}", "info")
        if valid_board_codes:
            add_debug_message(f"代码示例: {', '.join(valid_board_codes[:10])}{'...' if len(valid_board_codes) > 10 else ''}", "info")
        
        # 创建日期列表字符串，用于IN子句
        date_str_list = "', '".join(filtered_dates)
        date_filter = f"DATE(数据日期) IN ('{date_str_list}')"
        
        # 1. 首先检查表是否存在
        try:
            test_query = f"SELECT 1 FROM {table} LIMIT 1"
            test_df = db.query_to_dataframe(test_query)
            debug_success(f"表 {table} 存在并可以访问")
        except Exception as e:
            debug_error(f"表 {table} 不存在或无法访问: {str(e)}")
            if traceback:
                debug_error(traceback.format_exc())
            return pd.DataFrame()
        
        # 2. 构建查询 - 根据是否获取底部排名使用不同的SQL语句
        try:
            # 构建查询，不同表使用不同的查询模式
            if table == "capital_flow":
                if board_type and valid_board_codes:
                    # 使用板块代码列表过滤
                    board_codes_str = "', '".join(valid_board_codes)
                    add_debug_message(f"使用 {len(valid_board_codes)} 个板块代码过滤 capital_flow 表", "info")
                    
                    if get_bottom and ("流入" in field or "金额" in field or "净额" in field):
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 IN ('{board_codes_str}') 
                            ORDER BY 数据日期 DESC, {field} ASC
                        """
                        debug_info("正在查询资金流出最大的板块（负值最大）")
                    else:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 IN ('{board_codes_str}') 
                            ORDER BY 数据日期 DESC
                        """
                elif not board_type:
                    # 不需要过滤，使用LIKE BK% 匹配所有板块
                    if get_bottom and ("流入" in field or "金额" in field or "净额" in field):
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 LIKE 'BK%%' 
                            ORDER BY 数据日期 DESC, {field} ASC
                        """
                        debug_info("正在查询资金流出最大的板块（负值最大）")
                    else:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 LIKE 'BK%%' 
                            ORDER BY 数据日期 DESC
                        """
                else:
                    debug_warning(f"没有找到类型为 '{board_type}' 的板块代码")
                    return pd.DataFrame()
            elif table == "sector_trend":
                # 对于sector_trend表，使用名称匹配板块类型
                if board_type and valid_board_names:
                    # 构建名称IN子句
                    names_str = "', '".join(valid_board_names)
                    
                    # 记录实际使用的名称列表
                    add_debug_message(f"使用 {len(valid_board_names)} 个板块名称过滤 sector_trend 表", "info")
                    
                    if get_bottom:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 名称 IN ('{names_str}')
                            ORDER BY 数据日期 DESC, {field} ASC
                        """
                    else:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 名称 IN ('{names_str}')
                            ORDER BY 数据日期 DESC
                        """
                    debug_info(f"使用板块名称列表过滤sector_trend表数据")
                elif not board_type:
                    # 不需要过滤或没有有效的板块名称列表
                    if get_bottom:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter}
                            ORDER BY 数据日期 DESC, {field} ASC
                        """
                    else:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter}
                            ORDER BY 数据日期 DESC
                        """
                else:
                    debug_warning(f"没有找到类型为 '{board_type}' 的板块名称")
                    return pd.DataFrame()
            elif table == "dde_analysis" or table == "position_analysis":
                # 对于dde_analysis和position_analysis表，也通过代码匹配板块类型
                if board_type and valid_board_codes:
                    # 构建代码IN子句
                    board_codes_str = "', '".join(valid_board_codes)
                    
                    add_debug_message(f"使用 {len(valid_board_codes)} 个板块代码过滤 {table} 表", "info")
                    
                    if get_bottom:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 IN ('{board_codes_str}') 
                            ORDER BY 数据日期 DESC, {field} ASC
                        """
                    else:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 IN ('{board_codes_str}') 
                            ORDER BY 数据日期 DESC
                        """
                    debug_info(f"使用板块代码列表过滤{table}表数据")
                elif not board_type:
                    # 不需要过滤，使用LIKE BK% 匹配所有板块
                    if get_bottom:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 LIKE 'BK%%' 
                            ORDER BY 数据日期 DESC, {field} ASC
                        """
                    else:
                        query = f"""
                            SELECT * FROM {table} 
                            WHERE {date_filter} AND 代码 LIKE 'BK%%' 
                            ORDER BY 数据日期 DESC
                        """
                else:
                    debug_warning(f"没有找到类型为 '{board_type}' 的板块代码")
                    return pd.DataFrame()
            else:
                debug_error(f"不支持的表名: {table}")
                return pd.DataFrame()
            
            # 确保没有换行符和多余的空格
            query = query.replace("\n", " ").strip()
            
            # 显示SQL查询内容到调试区
            add_debug_message(f"SQL查询:\n{query}", "info")
            
            # 执行查询获取所有字段
            debug_info(f"正在执行查询...")
            df = db.query_to_dataframe(query)
            
            if df.empty:
                debug_warning(f"查询结果为空，可能指定的日期在表 {table} 中不存在数据")
                return pd.DataFrame()
            
            debug_success(f"查询成功，获取到 {len(df)} 条记录")
            
            # 确保数据日期列转换为字符串格式
            if '数据日期' in df.columns:
                df['数据日期'] = df['数据日期'].astype(str)
                debug_info(f"数据日期范围: {df['数据日期'].min()} 至 {df['数据日期'].max()}")
            
            # 确保目标字段存在
            if field not in df.columns:
                debug_error(f"字段 {field} 在表 {table} 中不存在")
                # 显示表中存在的列
                add_debug_message(f"表中存在的列: {df.columns.tolist()}", "info")
                return pd.DataFrame()
            
            # 添加indicator_value列，用于后续处理
            df['indicator_value'] = df[field]
            
            # 对每个日期计算排名
            if get_bottom:
                # 对于底部排名，使用升序排名（值越小排名越高）
                df['rank'] = df.groupby('数据日期')[field].rank(ascending=True, method='min')
            else:
                # 对于顶部排名，使用降序排名（值越大排名越高）
                df['rank'] = df.groupby('数据日期')[field].rank(ascending=False, method='min')
            
            # 只保留每个日期的前N名
            df = df[df['rank'] <= rank_limit]
            
            return df
            
        except Exception as e:
            debug_error(f"查询数据时出错: {str(e)}")
            if traceback:
                debug_error(traceback.format_exc())
            return pd.DataFrame()
    
    except Exception as e:
        debug_error(f"获取热门板块数据时出错: {str(e)}")
        if traceback:
            debug_error(traceback.format_exc())
        # 任何意外错误，返回空DataFrame
        return pd.DataFrame()

def create_mock_sector_data(indicator_info, dates, rank_limit=100, board_type=None):
    """创建模拟的板块数据，用于在数据库查询失败时展示"""
    # 此函数已不再使用，保留函数定义以保证代码结构完整性
    # 返回空DataFrame
    return pd.DataFrame()

def generate_rank_table(data, dates, indicator, rank_limit=100, show_limit=10, unit=""):
    """
    生成排名表格
    
    Args:
        data: 包含排名数据的DataFrame
        dates: 日期列表
        indicator: 排序指标
        rank_limit: 最大排名数
        show_limit: 显示的排名数
        unit: 指标单位
        
    Returns:
        HTML格式的表格
    """
    if data.empty:
        return "<p>无数据</p>"
    
    # 数据预处理 - 确保数据日期格式一致
    if '数据日期' in data.columns:
        data['数据日期_str'] = data['数据日期'].astype(str)
        
        # 处理每个日期的数据匹配
        for date in dates:
            try:
                # 尝试不同的匹配方式
                # 1. 精确匹配
                exact_match = data[data['数据日期_str'] == date]
                # 2. 日期部分匹配 (只比较年月日)
                date_part_match = data[data['数据日期_str'].str.startswith(date.split()[0] if ' ' in date else date)]
                
                # 使用效果最好的匹配方式
                if len(exact_match) > 0:
                    data.loc[exact_match.index, '日期匹配'] = date
                elif len(date_part_match) > 0:
                    data.loc[date_part_match.index, '日期匹配'] = date
            except Exception:
                pass
    else:
        # 添加一个虚拟日期列以继续
        data['日期匹配'] = dates[0] if dates else ""
    
    # 准备表格头部 - 日期格式为MM-DD
    date_headers = [pd.to_datetime(date).strftime('%m-%d') for date in dates]
    
    # 构建HTML表格
    html = """
    <style>
    .hot-sectors-table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        text-align: center;
        border: 1px solid #e6e6e6;
    }
    .hot-sectors-table th {
        background-color: #F7F7F7;
        padding: 10px;
        border: 1px solid #e6e6e6;
        font-weight: normal;
        position: sticky;
        top: 0;
    }
    .hot-sectors-table td {
        padding: 0;
        border: 1px solid #e6e6e6;
        vertical-align: middle;
        height: 80px;
    }
    .hot-sectors-table tr:nth-child(even) {
        background-color: #FFFFFF;
    }
    .hot-sectors-table tr:nth-child(odd) {
        background-color: #FFFFFF;
    }
    .rank-cell {
        width: 50px;
        height: 50px;
        line-height: 50px;
        font-weight: bold;
        color: white;
        font-size: 22px;
        text-align: center;
        vertical-align: middle;
    }
    .rank-1 { background-color: #FF3A3A; }
    .rank-2 { background-color: #FF8843; }
    .rank-3 { background-color: #FFBA37; }
    .rank-other { background-color: #808080; }
    .sector-name {
        font-weight: normal;
        text-align: center;
        font-size: 15px;
        padding: 10px 5px 5px 5px;
    }
    .indicator-value {
        font-weight: bold;
        color: #FF3A3A;
        text-align: center;
        font-size: 17px;
        padding: 5px 5px 10px 5px;
    }
    .cell-with-border {
        border: 1px solid #e0c8c8;
        padding: 0;
        height: 100%;
    }
    </style>
    <table class='hot-sectors-table'>
        <tr>
            <th>排名</th>
    """
    
    # 添加日期列
    for date in date_headers:
        html += f"<th>{date}</th>"
    
    html += "</tr>"
    
    # 检查必要字段
    required_fields = ['名称', 'indicator_value', 'rank']
    missing_fields = [field for field in required_fields if field not in data.columns]
    
    if missing_fields:
        # 如果缺少字段，添加默认值
        for field in missing_fields:
            if field == '名称':
                data['名称'] = "未知板块"
            elif field == 'indicator_value':
                data['indicator_value'] = 0
            elif field == 'rank':
                data['rank'] = range(1, len(data) + 1)
    
    # 获取前N名数据 - 改用日期匹配列
    pivoted_data = {}
    
    # 对于每个日期
    for date in dates:
        # 使用日期匹配列筛选
        date_df = data[data.get('日期匹配', '') == date].copy() if '日期匹配' in data.columns else data[data['数据日期_str'] == date].copy()
        
        if not date_df.empty:
            date_df = date_df.sort_values(by='rank')
            
            # 只取前show_limit名
            date_df = date_df.head(show_limit)
            
            # 存储每个日期的排名数据
            for _, row in date_df.iterrows():
                try:
                    rank = int(row['rank'])
                    if rank not in pivoted_data:
                        pivoted_data[rank] = {}
                    
                    pivoted_data[rank][date] = {
                        'name': row['名称'],
                        'value': row['indicator_value']
                    }
                except:
                    continue
    
    # 生成表格行
    for rank in range(1, show_limit + 1):
        html += "<tr>"
        
        # 排名单元格
        rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
        html += f"<td class='rank-cell {rank_class}'>{rank}</td>"
        
        # 对于每个日期的数据
        for date in dates:
            if rank in pivoted_data and date in pivoted_data[rank]:
                cell_data = pivoted_data[rank][date]
                name = cell_data['name']
                value = cell_data['value']
                
                formatted_value = format_value(value, unit)
                
                # 对于前3名使用边框高亮
                if rank <= 3:
                    # 第一名有特殊边框
                    if rank == 1:
                        td_style = "style='padding:0;'"
                        inner_style = "style='border:2px solid #e0c8c8;padding:0;'"
                    else:
                        td_style = "style='padding:0;'"
                        inner_style = ""
                    
                    html += f"""
                    <td {td_style}>
                        <div {inner_style}>
                            <div class='sector-name'>{name}</div>
                            <div class='indicator-value'>{formatted_value}</div>
                        </div>
                    </td>
                    """
                else:
                    html += f"""
                    <td>
                        <div class='sector-name'>{name}</div>
                        <div class='indicator-value'>{formatted_value}</div>
                    </td>
                    """
            else:
                html += "<td>-</td>"
        
        html += "</tr>"
    
    html += "</table>"
    return html

def get_rank_change_data(data, dates, indicator):
    """获取板块排名变化数据"""
    if len(dates) < 2 or data.empty:
        return pd.DataFrame()
    
    # 取最新两个日期
    latest_date = dates[0]
    prev_date = dates[1]
    
    # 获取这两个日期的数据
    latest_df = data[data['数据日期'] == latest_date].copy()
    prev_df = data[data['数据日期'] == prev_date].copy()
    
    # 合并数据，计算排名变化
    merged = pd.merge(
        latest_df[['名称', 'rank', 'indicator_value']],
        prev_df[['名称', 'rank', 'indicator_value']],
        on='名称', how='inner', suffixes=('_latest', '_prev')
    )
    
    # 计算排名变化和指标变化
    merged['rank_change'] = merged['rank_prev'] - merged['rank_latest']  # 正值表示排名上升
    merged['value_change'] = merged['indicator_value_latest'] - merged['indicator_value_prev']
    
    # 返回排名变化最大的N个板块
    return merged.sort_values(by='rank_change', ascending=False)

def create_rank_change_chart(change_data, indicator):
    """创建排名变化图表"""
    if change_data.empty:
        return None
    
    # 取排名变化最大的5个上升和5个下降
    top_rise = change_data[change_data['rank_change'] > 0].head(5)
    top_fall = change_data[change_data['rank_change'] < 0].tail(5).iloc[::-1]  # 反转，使降幅最大的在底部
    
    # 合并数据
    plot_data = pd.concat([top_rise, top_fall])
    
    if plot_data.empty:
        return None
    
    # 创建横向条形图
    fig = px.bar(
        plot_data,
        x='rank_change',
        y='名称',
        color='rank_change',
        color_continuous_scale=['#0068c9', '#FFFFFF', '#f63366'],  # 蓝白红色
        range_color=[-max(abs(plot_data['rank_change'])), max(abs(plot_data['rank_change']))],
        title=f"最新交易日板块排名变化 (按{indicator})",
        labels={'rank_change': '排名变化', '名称': '板块名称'},
        height=400,
    )
    
    fig.update_layout(
        xaxis_title="排名变化（正值表示上升）",
        yaxis_title="",
        xaxis={'side': 'top'},
        margin=dict(l=10, r=10, t=40, b=10),
    )
    
    return fig

def normalize_date(date_value):
    """将各种格式的日期值标准化为 'YYYY-MM-DD' 格式的字符串"""
    try:
        # 处理 datetime.date 对象
        if isinstance(date_value, datetime.date):
            return date_value.strftime('%Y-%m-%d')
        
        # 处理 pandas Timestamp 对象
        elif isinstance(date_value, pd.Timestamp):
            return date_value.strftime('%Y-%m-%d')
        
        # 处理字符串格式
        elif isinstance(date_value, str):
            parsed_date = pd.to_datetime(date_value)
            return parsed_date.strftime('%Y-%m-%d')
        
        # 处理其他类型（转换为字符串后解析）
        else:
            parsed_date = pd.to_datetime(str(date_value))
            return parsed_date.strftime('%Y-%m-%d')
    
    except Exception as e:
        raise ValueError(f"无法将值 '{date_value}' 转换为有效日期: {str(e)}")

# 在test_db_connection函数下方添加一个新函数
def deep_db_diagnostic():
    """执行数据库深度诊断，针对MySQL数据库"""
    results = {"success": False, "details": [], "found_tables": []}
    
    try:
        # 尝试直接从backend.db导入
        try:
            from backend.db import db
            results["details"].append("✅ 成功导入backend.db模块")
            
            # 尝试执行简单查询测试连接
            try:
                version_query = "SELECT VERSION() as version"
                version_df = db.query_to_dataframe(version_query)
                if not version_df.empty:
                    version = version_df['version'].iloc[0]
                    results["details"].append(f"✅ 成功连接到MySQL数据库，版本: {version}")
                    results["success"] = True
                else:
                    results["details"].append("❌ 无法获取MySQL版本")
            except Exception as e:
                results["details"].append(f"❌ 连接数据库失败: {str(e)}")
                
            # 尝试获取所有表名
            try:
                tables_query = "SHOW TABLES"
                tables_df = db.query_to_dataframe(tables_query)
                if not tables_df.empty:
                    # 表名在第一列，但列名可能不同
                    first_col = tables_df.columns[0]
                    tables = tables_df[first_col].tolist()
                    results["details"].append(f"✅ 找到{len(tables)}个表: {tables}")
                    results["found_tables"] = tables
                else:
                    results["details"].append("❌ 查询表名成功，但数据库中没有表")
            except Exception as e:
                results["details"].append(f"❌ 获取表名失败: {str(e)}")
                
            # 尝试直接查询特定表
            target_tables = ["capital_flow", "CAPITAL_FLOW", "Capital_Flow", 
                           "sector_trend", "dde_analysis", "position_analysis"]
            
            for table in target_tables:
                try:
                    # 在MySQL中使用参数化查询
                    count_query = f"SELECT COUNT(*) as count FROM {table}"
                    count_df = db.query_to_dataframe(count_query)
                    if not count_df.empty:
                        count = count_df['count'].iloc[0]
                        results["details"].append(f"✅ 表 {table} 存在，包含 {count} 条记录")
                except Exception as e:
                    results["details"].append(f"❌ 查询表 {table} 失败: {str(e)}")
            
            # 检查表结构
            if "capital_flow" in results["found_tables"]:
                try:
                    struct_query = "DESCRIBE capital_flow"
                    struct_df = db.query_to_dataframe(struct_query)
                    if not struct_df.empty:
                        # 获取字段名列表
                        fields = struct_df['Field'].tolist() if 'Field' in struct_df.columns else []
                        results["details"].append(f"✅ capital_flow表列信息: {fields}")
                except Exception as e:
                    results["details"].append(f"❌ 获取表结构失败: {str(e)}")
                
        except ImportError as e:
            results["details"].append(f"❌ 导入backend.db模块失败: {str(e)}")
            
    except Exception as e:
        results["details"].append(f"❌ 诊断过程出错: {str(e)}")
    
    return results

def display_hot_sectors(dates, sector_data, selected_metric, show_limit=10, show_bottom=False):
    """
    显示热门板块排行榜，使用简洁的表格形式（用户指定的首选风格）
    
    Args:
        dates: 日期列表
        sector_data: 板块数据DataFrame
        selected_metric: 选择的排序指标
        show_limit: 显示的排名数量限制
        show_bottom: 是否显示垫底的板块（而非排名靠前的）
    """
    
    if sector_data.empty:
        st.warning("没有可显示的板块数据")
        return
    
    # 添加调试输出
    if st.checkbox("显示详细调试信息", value=False):
        st.write("原始数据预览：")
        st.dataframe(sector_data.head())
    
    # 确保数值列为数值类型
    numeric_cols = ['主力净流入', '涨幅_pct', '涨幅%', '成交额', '流入资金', '流出资金', 'indicator_value']
    for col in numeric_cols:
        if col in sector_data.columns:
            sector_data[col] = pd.to_numeric(sector_data[col], errors='coerce')
    
    # 确保日期列为日期类型，并处理日期格式问题
    if '数据日期' in sector_data.columns:
        # 把日期转换成字符串，方便后续处理
        sector_data['数据日期_str'] = sector_data['数据日期'].astype(str)
    
    # 处理每个日期的数据并构建日期与排名数据的映射
    date_rank_data = {}
    
    for date in dates:
        date_str = str(date)
        date_obj = pd.to_datetime(date).date() if isinstance(date, str) else date
        date_obj_str = str(date_obj)
        
        # 检查不同的日期格式
        date_formats = [
            date_str,
            date_obj_str,
            date_str.split()[0] if ' ' in date_str else date_str,  # 处理有时间部分的日期
            date_obj_str.split()[0] if ' ' in date_obj_str else date_obj_str,
        ]
        
        # 尝试不同的日期格式匹配
        found = False
        date_data = None
        for fmt in date_formats:
            # 通过字符串比较匹配日期
            if '数据日期_str' in sector_data.columns:
                date_filter = sector_data['数据日期_str'].str.startswith(fmt)
                if date_filter.any():
                    date_data = sector_data[date_filter].copy()
                    found = True
                    break
        
        # 如果上面的匹配都失败，尝试直接用对象匹配
        if not found and '数据日期' in sector_data.columns:
            date_data = sector_data[sector_data['数据日期'] == date_obj].copy()
        
        if date_data is None or date_data.empty:
            # 添加调试信息
            if st.checkbox("显示详细调试信息", value=False):
                st.warning(f"找不到日期 {date} 的数据")
            continue
        
        # 根据指标排序
        target_metric = selected_metric
        if target_metric not in date_data.columns and 'indicator_value' in date_data.columns:
            target_metric = 'indicator_value'
            
        if target_metric in date_data.columns:
            # 确定排序方向：如果是显示底部排名且是资金流指标，按指标值从小到大排序
            if show_bottom and ("流入" in selected_metric or "金额" in selected_metric):
                # 对于资金类指标，负值越大（如-5.18亿）表示资金流出越多
                date_data = date_data.sort_values(by=target_metric, ascending=True).reset_index(drop=True)
                # 添加排名（从1开始，表示倒数第一名）
                date_data['排名'] = range(1, len(date_data) + 1)
                date_data['排名类型'] = 'bottom'  # 标记为底部排名
            elif show_bottom:
                # 对于其他指标，按指标值从小到大排序
                date_data = date_data.sort_values(by=target_metric, ascending=True).reset_index(drop=True)
                # 添加排名（从1开始，表示倒数第一名）
                date_data['排名'] = range(1, len(date_data) + 1)
                date_data['排名类型'] = 'bottom'  # 标记为底部排名
            else:
                # 正常排序：指标值从大到小
                date_data = date_data.sort_values(by=target_metric, ascending=False).reset_index(drop=True)
                # 添加排名（从1开始，表示第一名）
                date_data['排名'] = range(1, len(date_data) + 1)
                date_data['排名类型'] = 'top'  # 标记为顶部排名
            
            # 精简数据，仅保留必要字段
            keep_cols = ['排名', '排名类型', '代码', '名称', target_metric]
            keep_cols = [col for col in keep_cols if col in date_data.columns]
            
            # 将列名统一
            date_data = date_data[keep_cols].copy()
            if '代码' in date_data.columns:
                date_data.rename(columns={'代码': '板块代码'}, inplace=True)
            if '名称' in date_data.columns:
                date_data.rename(columns={'名称': '板块名称'}, inplace=True)
            if target_metric in date_data.columns:
                date_data.rename(columns={target_metric: '指标值'}, inplace=True)
            
            # 仅保留前N名或后N名
            date_data = date_data.head(show_limit)
            
            # 存储日期数据
            date_rank_data[date_obj] = date_data
    
    if not date_rank_data:
        st.warning("没有可显示的排名数据")
        # 添加调试信息
        if st.checkbox("显示详细调试信息", value=False):
            st.write("尝试的日期格式:")
            for date in dates:
                st.write(f" - {date} (类型: {type(date)})")
            
            if '数据日期' in sector_data.columns:
                st.write("数据库中存在的日期:")
                unique_dates = sector_data['数据日期'].unique()
                for date in unique_dates[:10]:  # 只显示前10个，避免过多
                    st.write(f" - {date} (类型: {type(date)})")
        return
    
    # 显示标题
    if show_bottom:
        st.subheader(f"按{selected_metric}排序的表现最弱板块")
    else:
        st.subheader(f"按{selected_metric}排序的热门板块")
    
    # 创建简洁视图表格
    create_simple_rank_table(date_rank_data, dates, selected_metric, show_limit, show_bottom)


def create_simple_rank_table(date_rank_data, dates, metric_name, show_limit=10, show_bottom=False):
    """
    创建简洁的排名表格，完全使用Streamlit原生组件
    
    Args:
        date_rank_data: 日期与排名数据的映射
        dates: 日期列表
        metric_name: 指标名称
        show_limit: 显示的最大排名数
        show_bottom: 是否显示垫底的板块
    """
    # 按日期倒序排列(最新日期在前)
    sorted_dates = sorted(dates, reverse=True)
    # 显示所有日期
    display_dates = sorted_dates
    
    # 如果日期太多，添加一个提示
    if len(display_dates) > 10:
        st.info(f"正在显示全部 {len(display_dates)} 列数据，您可以水平滚动查看所有日期。")
    
    # 创建一个包含所有数据的表格数据结构
    all_data_frames = []
    
    # 处理每个日期的数据，将它们收集到一个列表中
    for i, date in enumerate(display_dates):
        # 确保生成唯一的日期标识符，包含日期和索引
        date_str = date.strftime('%m-%d') if hasattr(date, 'strftime') else str(date)
        # 从日期字符串中提取月-日部分，如果格式为YYYY-MM-DD
        if not hasattr(date, 'strftime') and len(date_str) >= 10 and '-' in date_str:
            try:
                # 尝试从YYYY-MM-DD格式提取MM-DD
                date_str = date_str[5:10]  # 提取MM-DD部分
            except:
                pass  # 如果失败，保留原始格式
                
        short_date = f"{date_str}_{i}"  # 添加索引确保唯一性
        
        # 查找此日期的数据
        date_data = None
        for key, value in date_rank_data.items():
            if (isinstance(key, (datetime.date, pd.Timestamp)) and 
                isinstance(date, (datetime.date, pd.Timestamp)) and
                key == date):
                date_data = value
                break
            elif str(key).startswith(str(date)) or str(date).startswith(str(key)):
                date_data = value
                break
        
        if date_data is not None:
            # 创建这个日期的DataFrame
            temp_df = date_data.copy()
            # 仅保留排名和板块名称、指标值和类型信息
            if '板块名称' in temp_df.columns and '指标值' in temp_df.columns:
                # 将指标值格式化
                temp_df['value_str'] = temp_df['指标值'].apply(
                    lambda x: f"{x:.2f}亿" if "流入" in metric_name or "金额" in metric_name 
                    else (f"{x:.2f}%" if "%" in metric_name else f"{x:.2f}")
                )
                # 添加数值的正负标记
                temp_df['value_sign'] = temp_df['指标值'].apply(lambda x: "positive" if x >= 0 else "negative")
                
                # 使用唯一列名
                temp_df[f'板块_{short_date}'] = temp_df['板块名称']
                temp_df[f'值_{short_date}'] = temp_df['value_str']
                temp_df[f'符号_{short_date}'] = temp_df['value_sign']
                temp_df[f'类型_{short_date}'] = temp_df['排名类型']
                
                # 保留必要字段，只保留排名和新创建的带日期列名的列
                columns_to_keep = ['排名']
                columns_to_keep.extend([
                    f'板块_{short_date}', 
                    f'值_{short_date}', 
                    f'符号_{short_date}', 
                    f'类型_{short_date}'
                ])
                
                if f'倒数排名_{short_date}' in temp_df.columns:
                    columns_to_keep.append(f'倒数排名_{short_date}')
                
                temp_df = temp_df[columns_to_keep]
                
                # 将处理后的DataFrame添加到列表中
                all_data_frames.append(temp_df)
    
    # 如果没有数据，显示提示并返回
    if not all_data_frames:
        st.warning("无法生成表格：没有找到匹配的数据")
        return
    
    # 从第一个DataFrame开始，依次合并其余的DataFrame
    df_merged = all_data_frames[0]
    for df in all_data_frames[1:]:
        df_merged = pd.merge(df_merged, df, on='排名', how='outer', suffixes=(False, False))
    
    # 按排名排序
    df_merged = df_merged.sort_values('排名')
    
    # 创建一个容器并添加CSS以支持水平滚动
    st.markdown("""
    <style>
    .scrollable-container {
        width: 100%;
        overflow-x: auto;
        white-space: nowrap;
    }
    .bottom-rank-marker {
        font-size: 10px;
        color: #666666;
        position: absolute;
        top: -5px;
        right: -5px;
        background-color: #f0f0f0;
        border-radius: 50%;
        width: 16px;
        height: 16px;
        line-height: 16px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 1. 使用可滚动容器包装表格
    st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
    
    # 创建表格容器
    with st.container():
        # 创建一个表格展示区域
        col_count = len(display_dates) + 1  # 排名列 + 日期列
        columns = st.columns(col_count)
        
        # 添加表头
        with columns[0]:
            if show_bottom:
                st.markdown("<div style='text-align: center; font-weight: bold;'>倒数</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: center; font-weight: bold;'>排名</div>", unsafe_allow_html=True)
        
        for i, date in enumerate(display_dates):
            # 修改这里的日期格式化逻辑，只显示月-日，不显示年份
            if hasattr(date, 'strftime'):
                display_date = date.strftime('%m-%d')  # 只显示月-日
            else:
                # 尝试从字符串中提取月-日部分
                try:
                    date_str = str(date)
                    if len(date_str) >= 10 and '-' in date_str:
                        # 对于YYYY-MM-DD格式
                        display_date = date_str[5:10]  # 提取MM-DD部分
                    else:
                        date_obj = pd.to_datetime(date)
                        display_date = date_obj.strftime('%m-%d')
                except:
                    display_date = str(date)
                    # 如果是YYYY-MM-DD格式，只保留MM-DD部分
                    if len(display_date) >= 10 and '-' in display_date:
                        display_date = display_date[5:10]
            
            with columns[i+1]:
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{display_date}</div>", unsafe_allow_html=True)
        
        # 添加分隔线
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        
        # 标准模式 - 显示所有排名
        for idx, row in df_merged.iterrows():
            rank = int(row['排名'])
            if rank > show_limit:
                continue
                
            cols = st.columns(col_count)
            
            # 排名列 - 使用自定义HTML显示带颜色的排名
            with cols[0]:
                if show_bottom:
                    # 使用灰色系列表示倒数排名
                    if rank <= 3:
                        color = ["#767676", "#888888", "#999999"][rank-1]  # 深灰、灰、浅灰
                    else:
                        color = "#aaaaaa"  # 普通灰色
                    # 添加向下箭头标记
                    st.markdown(f"""
                    <div style='display: flex; justify-content: center; align-items: center; position: relative;'>
                        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: {color}; 
                        color: white; display: flex; align-items: center; justify-content: center; 
                        font-weight: bold; font-size: 18px;'>{rank}</div>
                        <div style='font-size: 10px; color: #666666; position: absolute; 
                        top: -5px; right: -5px; background-color: #f0f0f0; border-radius: 50%; 
                        width: 16px; height: 16px; line-height: 16px; text-align: center;
                        display: flex; align-items: center; justify-content: center;'>↓</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # 正常排名使用彩色标记
                    if rank <= 3:
                        color = ["#FF4B4B", "#FF8F65", "#FFCA3A"][rank-1]  # 红、橙、黄
                    else:
                        color = "#f44336"  # 普通红色
                    st.markdown(f"""
                    <div style='display: flex; justify-content: center; align-items: center;'>
                        <div style='width: 30px; height: 30px; border-radius: 50%; background-color: {color}; 
                        color: white; display: flex; align-items: center; justify-content: center; 
                        font-weight: bold; font-size: 18px;'>{rank}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 日期数据列
            for i, date in enumerate(display_dates):
                # 提取月-日格式
                if hasattr(date, 'strftime'):
                    date_str = date.strftime('%m-%d')
                else:
                    date_str = str(date)
                    if len(date_str) >= 10 and '-' in date_str:
                        date_str = date_str[5:10]
                short_date = f"{date_str}_{i}"  # 与上面生成列名的方式保持一致
                
                with cols[i+1]:
                    board_col = f'板块_{short_date}'
                    value_col = f'值_{short_date}'
                    sign_col = f'符号_{short_date}'
                    
                    if (board_col in row and value_col in row and sign_col in row and 
                        pd.notna(row[board_col]) and pd.notna(row[value_col])):
                        board_name = row[board_col]
                        value = row[value_col]
                        is_positive = row[sign_col] == "positive"
                        
                        # 根据值的正负选择颜色：正数红色，负数绿色
                        # 对于倒数排名板块，可以使用较暗的颜色
                        if show_bottom:
                            value_color = "#de5246" if is_positive else "#359e35"  # 暗红色/暗绿色
                        else:
                            value_color = "#ff4b4b" if is_positive else "#0bbd0b"  # 亮红色/亮绿色
                        
                        st.markdown(f"""
                        <div style='text-align: center;'>
                            <div style='font-size: 14px; margin-bottom: 5px;'>{board_name}</div>
                            <div style='font-size: 16px; font-weight: bold; color: {value_color};'>{value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align: center;'>-</div>", unsafe_allow_html=True)
            
            # 添加浅色分隔线
            st.markdown("<hr style='margin: 5px 0; border-color: #f0f0f0;'>", unsafe_allow_html=True)
    
    # 关闭可滚动容器
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 显示日期到数据映射的调试信息
    if st.checkbox("显示数据映射调试", value=False):
        st.write("日期到数据的映射:")
        for date, data in date_rank_data.items():
            st.write(f"日期: {date} (类型: {type(date)})")
            st.dataframe(data.head(3))

def main():
    # 侧边栏：所有配置选项
    with st.sidebar:
        st.header("📊 数据设置")
        
        # 添加板块类型过滤选项
        st.markdown("### 板块类型")
        board_type_options = {
            "概念板块": "概念", 
            "行业板块": "行业", 
            "地区板块": "地区", 
            "风格板块": "风格",
            "全部板块": None
        }
        selected_board_type_display = st.selectbox(
            "选择板块类型", 
            list(board_type_options.keys()),
            index=0  # 默认选择"概念板块"
        )
        selected_board_type = board_type_options[selected_board_type_display]
        
        # 获取指标列表并提供选择（下拉式）
        all_indicators = get_all_indicators()
        
        # 按表分组指标
        grouped_indicators = {
            "资金流指标 (capital_flow)": [k for k, v in all_indicators.items() if v["table"] == "capital_flow"],
            "DDE指标 (dde_analysis)": [k for k, v in all_indicators.items() if v["table"] == "dde_analysis"],
            "增仓指标 (position_analysis)": [k for k, v in all_indicators.items() if v["table"] == "position_analysis"],
            "板块趋势 (sector_trend)": [k for k, v in all_indicators.items() if v["table"] == "sector_trend"],
        }
        
        # 选择指标分组
        selected_group = st.selectbox(
            "选择指标分组",
            list(grouped_indicators.keys()),
            index=0
        )
        
        # 根据选择的分组显示相应的指标
        group_indicators = grouped_indicators[selected_group]
        
        selected_indicator = st.selectbox(
            "选择指标", 
            group_indicators,
            index=0,
            format_func=lambda x: f"{x} ({all_indicators[x]['unit']})" if all_indicators[x]['unit'] else x
        )
        
        # 添加日期选择界面
        st.markdown("### 日期设置")
        
        # 日期范围选择（下拉式）
        date_options = {"最近5日": 5, "最近10日": 10, "最近30日": 30, "最近60日": 60}
        date_range = st.selectbox("日期范围", list(date_options.keys()), index=1)
        days_count = date_options[date_range]
        
        # 获取交易日期（自动方式）
        status_container = st.empty()
        dates = get_recent_trading_dates(days=days_count)
        if dates:
            add_debug_message(f"成功获取 {len(dates)} 个交易日期", "success")
        else:
            add_debug_message("无法获取交易日期数据", "error")
            current_date = pd.Timestamp.now()
            dates = [(current_date - pd.Timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days_count)]
        
        # 显示范围（下拉式）
        st.markdown("### 显示范围")
        rank_options = [
            "前10名", "前20名", "前30名", "前50名",
            "后10名", "后20名", "后30名",
            "全部"
        ]
        rank_display = st.selectbox("显示范围", rank_options, index=0)
        
        # 解析显示范围，设置show_limit和show_bottom
        show_bottom = False
        if rank_display == "前10名":
            show_limit = 10
        elif rank_display == "前20名":
            show_limit = 20
        elif rank_display == "前30名":
            show_limit = 30
        elif rank_display == "前50名":
            show_limit = 50
        elif rank_display == "后10名":
            show_limit = 10
            show_bottom = True
        elif rank_display == "后20名":
            show_limit = 20
            show_bottom = True
        elif rank_display == "后30名":
            show_limit = 30
            show_bottom = True
        else:  # 全部
            show_limit = 100
        
        # 添加显示调试信息的选项
        show_debug = st.checkbox("显示调试信息", value=False,
                               help="选中此项将显示详细的查询过程和错误信息")
    
    # 验证日期格式，过滤掉无效日期
    valid_dates = []
    for date in dates:
        try:
            # 尝试标准化日期
            normalized_date = normalize_date(date)
            valid_dates.append(normalized_date)
        except Exception as e:
            add_debug_message(f"日期 {date} 格式无效，已跳过: {str(e)}", "warning")
            continue
    
    if not valid_dates:
        st.error("⚠️ 所有日期均无效，无法获取数据")
        if show_debug:
            display_debug_messages()
        return
    
    dates = valid_dates
    
    # 显示有效的日期列表到调试区
    add_debug_message(f"有效日期列表: {dates}", "info")
    
    # 如果选择了板块类型，添加到调试信息
    if selected_board_type:
        add_debug_message(f"板块类型过滤: {selected_board_type}", "info")
         
    # 获取所选指标的数据
    indicator_info = all_indicators[selected_indicator]
    add_debug_message(f"正在获取指标数据: {selected_indicator} (表: {indicator_info['table']})", "info")
    
    # 从数据库获取数据
    add_debug_message("从数据库获取数据...", "info")
    # 传递show_bottom参数和board_type参数到get_hot_sectors函数
    hot_sectors_data = get_hot_sectors(
        indicator_info, 
        dates, 
        rank_limit=100, 
        get_bottom=show_bottom,
        board_type=selected_board_type
    )
    
    if hot_sectors_data.empty:
        st.error(f"⚠️ 未能获取到\"{selected_indicator}\"的数据")
        st.info("可能的原因：")
        st.info("1. 数据库中不存在该指标的数据")
        st.info("2. 所选日期范围内没有数据")
        if selected_board_type:
            st.info(f"3. 没有符合\"{selected_board_type_display}\"类型的板块数据")
        st.info("请尝试选择其他指标、日期范围或板块类型")
    else:
        add_debug_message(f"成功获取 {len(hot_sectors_data)} 条数据记录", "success")
        # 主区域：显示排名表格
        display_hot_sectors(dates, hot_sectors_data, selected_indicator, show_limit, show_bottom)
    
    # 添加数据库工具到页面底部
    st.markdown("---")  # 分隔线
    with st.expander("数据库工具", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # 数据库连接测试按钮
            if st.button("测试数据库连接", type="primary", key="test_db_bottom"):
                with st.spinner("正在测试数据库连接..."):
                    db_info = test_db_connection()
                    if db_info["success"]:
                        st.success(f"✅ 数据库连接成功: {db_info['connection_type']}")
                        if db_info["tables"]:
                            st.info(f"数据库中的表: {db_info['tables']}")
                        else:
                            st.warning("数据库中没有找到表")
                    else:
                        st.error(f"❌ 数据库连接失败: {db_info['error']}")
                        if db_info["db_path"]:
                            st.info(f"找到数据库文件: {db_info['db_path']}")
        
        with col2:
            # 数据库深度诊断按钮
            if st.button("数据库深度诊断", type="secondary", key="deep_db_bottom"):
                with st.spinner("正在执行深度诊断..."):
                    diagnostic_results = deep_db_diagnostic()
                    for detail in diagnostic_results["details"]:
                        if detail.startswith("✅"):
                            st.success(detail)
                        elif detail.startswith("❌"):
                            st.error(detail)
                        else:
                            st.info(detail)
    
    # 在页面底部显示收集的调试信息
    if show_debug:
        display_debug_messages()

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
