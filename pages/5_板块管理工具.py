import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import traceback
from backend.db import db
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

# 设置页面标题和布局
st.set_page_config(page_title="板块管理工具", layout="wide")
st.title("板块管理工具")

# 创建一个进度容器来显示操作进度
progress_container = st.empty()

# 获取当前跟踪的板块列表
def get_tracked_sectors():
    try:
        st.write("正在执行查询...")
        query = """
            SELECT DISTINCT 代码 as stock_code, 名称 as stock_name 
            FROM merged_data_specified 
            ORDER BY 代码
        """
        st.write(f"执行SQL查询: {query}")
        results_df = db.query_to_dataframe(query)
        st.write(f"查询结果: {len(results_df)} 条记录")
        
        return results_df
    except Exception as e:
        st.error(f"获取板块列表失败: {str(e)}")
        st.write(f"错误详情: {str(e)}")
        st.write(traceback.format_exc())
        return pd.DataFrame(columns=['stock_code', 'stock_name'])

# 将NumPy类型转换为Python标准类型
def convert_numpy_types(value):
    if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        if np.isnan(value):  # 明确处理NaN值
            return None
        return float(value)
    elif isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, np.datetime64):
        return pd.Timestamp(value).to_pydatetime()
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif pd.isna(value):
        return None
    elif isinstance(value, str) and value.strip() == '':  # 处理空字符串
        return None
    return value

# 安全地从DataFrame行中获取值
def safe_get_value(row, column):
    """安全地从DataFrame行中获取值，处理任何异常"""
    try:
        if column not in row.index:
            return None
        value = row[column]
        return convert_numpy_types(value)
    except Exception as e:
        # 发生任何错误，返回None而不是失败
        return None

# 添加新板块到跟踪池
def add_sector_to_pool(sector_code, sector_name):
    progress_text = st.empty()
    progress_bar = st.progress(0, "处理中")
    
    try:
        progress_text.write("步骤1/7: 开始添加板块流程...")
        progress_bar.progress(10, text="开始处理")
        
        # 获取资金流向历史数据
        progress_text.write("步骤2/7: 正在查询资金流向历史数据...")
        progress_bar.progress(20, text="查询资金流向数据")
        
        capital_flow_query = f"""
            SELECT *
            FROM capital_flow
            WHERE 代码 = '{sector_code}'
            ORDER BY 数据日期 DESC
        """
        st.code(capital_flow_query, language="sql")
        
        try:
            capital_flow_data = db.query_to_dataframe(capital_flow_query)
            st.write(f"资金流向数据查询完成，获取到 {len(capital_flow_data)} 条记录")
            if not capital_flow_data.empty:
                st.write("资金流向数据样例:")
                st.write(capital_flow_data.head(1))
            else:
                st.warning("未找到资金流向数据")
        except Exception as query_error:
            error_message = str(query_error).lower()
            
            # 判断错误类型，提供更具体的错误信息
            if "timeout" in error_message or "connection" in error_message or "connect" in error_message:
                st.error(f"📶 数据库连接超时或网络问题: {str(query_error)}")
                st.info("💡 建议: 请等待几秒钟后再次尝试添加，或者检查数据库服务是否正常运行")
            elif "access denied" in error_message or "permission" in error_message:
                st.error(f"🔒 数据库访问权限问题: {str(query_error)}")
            elif "table" in error_message and ("not exist" in error_message or "doesn't exist" in error_message):
                st.error(f"📋 数据表不存在: {str(query_error)}")
                st.info("💡 建议: 请确认数据库中是否存在capital_flow表")
            else:
                st.error(f"❌ 查询资金流向数据时出错: {str(query_error)}")
            
            st.write(traceback.format_exc())
            progress_text.write("添加板块失败: 查询资金流向数据错误")
            progress_bar.progress(100, text="操作失败")
            return
        
        if capital_flow_data.empty:
            # 提供更明确的数据不存在提示
            progress_text.write("添加板块失败: 找不到资金流向数据")
            progress_bar.progress(100, text="操作失败")
            
            # 检查资金流表中是否存在任何记录，来判断是否是表结构问题
            try:
                check_table_query = "SELECT COUNT(*) as count FROM capital_flow LIMIT 1"
                table_check = db.query_to_dataframe(check_table_query)
                total_records = table_check.iloc[0]['count'] if not table_check.empty else 0
                
                if total_records == 0:
                    st.error(f"❗ 资金流向表为空: capital_flow表中没有任何记录")
                    st.info("💡 建议: 请先导入资金流向数据")
                else:
                    # 检查其他板块是否有数据，判断是否是特定板块的问题
                    other_records_query = "SELECT DISTINCT 代码 FROM capital_flow LIMIT 5"
                    other_records = db.query_to_dataframe(other_records_query)
                    
                    if not other_records.empty:
                        available_sectors = ", ".join(other_records['代码'].tolist())
                        st.error(f"❌ 板块 {sector_code} '{sector_name}' 在资金流向表中没有数据")
                        st.info(f"💡 建议: 请确认板块代码是否正确。资金流向表中现有的板块代码示例: {available_sectors}")
                    else:
                        st.error(f"❓ 资金流向表结构可能有问题")
            except Exception as check_error:
                st.error(f"🔍 无法检查资金流向表状态: {str(check_error)}")
            
            return
        
        # 获取已有数据的日期列表，用于后续过滤
        progress_text.write("步骤3/7: 获取已存在的数据日期...")
        progress_bar.progress(30, text="检查已有数据")
        
        existing_dates_query = f"""
            SELECT 数据日期
            FROM merged_data_specified
            WHERE 代码 = '{sector_code}'
        """
        
        try:
            existing_dates_df = db.query_to_dataframe(existing_dates_query)
            existing_dates = set()
            if not existing_dates_df.empty:
                existing_dates = set(pd.to_datetime(existing_dates_df['数据日期']).dt.strftime('%Y-%m-%d'))
            
            st.write(f"已有 {len(existing_dates)} 个日期的数据")
        except Exception as check_error:
            error_message = str(check_error).lower()
            
            # 判断错误类型
            if "timeout" in error_message or "connection" in error_message:
                st.error(f"📶 数据库连接超时或网络问题: {str(check_error)}")
            elif "access denied" in error_message or "permission" in error_message:
                st.error(f"🔒 数据库访问权限问题: {str(check_error)}")
            elif "table" in error_message and ("not exist" in error_message or "doesn't exist" in error_message):
                st.error(f"📋 merged_data_specified表不存在: {str(check_error)}")
                st.info("💡 表可能尚未创建，将正常继续处理")
            else:
                st.error(f"❌ 检查已有数据时出错: {str(check_error)}")
            
            st.write(traceback.format_exc())
            existing_dates = set()  # 如果查询失败，假设没有现有数据
        
        # 准备查询其他表的数据
        progress_text.write("步骤4/7: 准备处理所有日期数据...")
        progress_bar.progress(40, text="准备批量处理")
        
        # 获取所有要处理的日期
        all_dates = pd.to_datetime(capital_flow_data['数据日期']).dt.strftime('%Y-%m-%d').unique()
        dates_to_process = [d for d in all_dates if d not in existing_dates]
        
        st.write(f"找到 {len(all_dates)} 个日期的数据，需要处理 {len(dates_to_process)} 个新日期")
        
        if not dates_to_process:
            progress_text.write("添加板块完成: 没有新的数据需要添加")
            progress_bar.progress(100, text="无需操作")
            st.success(f"板块 {sector_code} {sector_name} 的所有数据已经存在，无需添加")
            return
        
        # 收集所有日期的DDE分析、持仓分析和板块趋势数据
        progress_text.write("步骤5/7: 收集其他表的数据...")
        progress_bar.progress(50, text="收集关联数据")
        
        # 获取DDE分析数据
        try:
            st.write("正在查询DDE分析数据...")
            dde_query = f"""
                SELECT *
                FROM dde_analysis
                WHERE 代码 = '{sector_code}'
            """
            dde_data = db.query_to_dataframe(dde_query)
            dde_data['数据日期'] = pd.to_datetime(dde_data['数据日期']).dt.strftime('%Y-%m-%d')
            dde_data_dict = {row['数据日期']: row for _, row in dde_data.iterrows()}
            st.write(f"DDE分析数据获取: {'成功，获取 ' + str(len(dde_data)) + ' 条记录' if not dde_data.empty else '无数据'}")
        except Exception as dde_error:
            error_message = str(dde_error).lower()
            
            if "timeout" in error_message or "connection" in error_message:
                st.warning(f"📶 DDE分析数据查询超时或网络问题: {str(dde_error)}")
                st.info("将继续处理，但可能缺少DDE分析数据")
            elif "table" in error_message and ("not exist" in error_message or "doesn't exist" in error_message):
                st.warning(f"📋 DDE分析数据表不存在: {str(dde_error)}")
                st.info("将继续处理，但没有DDE分析数据")
            else:
                st.warning(f"⚠️ 查询DDE分析数据时出错: {str(dde_error)}")
            
            # 记录详细错误，但不中断处理
            with st.expander("查看DDE分析数据错误详情"):
                st.code(traceback.format_exc())
                
            dde_data_dict = {}
        
        # 获取持仓分析数据
        try:
            st.write("正在查询持仓分析数据...")
            position_query = f"""
                SELECT *
                FROM position_analysis
                WHERE 代码 = '{sector_code}'
            """
            position_data = db.query_to_dataframe(position_query)
            position_data['数据日期'] = pd.to_datetime(position_data['数据日期']).dt.strftime('%Y-%m-%d')
            position_data_dict = {row['数据日期']: row for _, row in position_data.iterrows()}
            st.write(f"持仓分析数据获取: {'成功，获取 ' + str(len(position_data)) + ' 条记录' if not position_data.empty else '无数据'}")
        except Exception as position_error:
            error_message = str(position_error).lower()
            
            if "timeout" in error_message or "connection" in error_message:
                st.warning(f"📶 持仓分析数据查询超时或网络问题: {str(position_error)}")
                st.info("将继续处理，但可能缺少持仓分析数据")
            elif "table" in error_message and ("not exist" in error_message or "doesn't exist" in error_message):
                st.warning(f"📋 持仓分析数据表不存在: {str(position_error)}")
                st.info("将继续处理，但没有持仓分析数据")
            else:
                st.warning(f"⚠️ 查询持仓分析数据时出错: {str(position_error)}")
            
            # 记录详细错误，但不中断处理
            with st.expander("查看持仓分析数据错误详情"):
                st.code(traceback.format_exc())
                
            position_data_dict = {}
        
        # 获取板块趋势数据
        try:
            st.write("正在查询板块趋势数据...")
            # 统一清洗名称：去除空格并转换为大写
            sector_name_upper = sector_name.strip().upper()
            
            st.write(f"处理后的板块名称: '{sector_name_upper}'")
            
            # 先尝试确切匹配，使用参数化查询避免SQL注入和转义问题
            exact_query = "SELECT * FROM sector_trend WHERE UPPER(TRIM(名称)) = %s"
            st.code(f"执行精确匹配查询: {exact_query} [参数: {sector_name_upper}]", language="sql")
            
            try:
                # 使用参数化查询而不是字符串拼接
                trend_data = db.query_to_dataframe(exact_query, params=[sector_name_upper])
                st.write(f"精确查询结果: {len(trend_data)} 条记录")
            except Exception as exact_query_error:
                st.warning(f"精确匹配查询出错: {str(exact_query_error)}")
                # 如果参数化查询失败，尝试直接执行SQL
                fallback_exact_query = f"""
                    SELECT * 
                    FROM sector_trend 
                    WHERE UPPER(TRIM(名称)) = '{sector_name_upper.replace("'", "''")}'
                """
                st.code(f"尝试备用查询: {fallback_exact_query}", language="sql")
                trend_data = db.query_to_dataframe(fallback_exact_query)
                st.write(f"备用精确查询结果: {len(trend_data)} 条记录")
            
            # 如果确切匹配没有结果，尝试模糊匹配
            if trend_data.empty:
                st.write(f"警告: 未能在 sector_trend 表中找到任何精确匹配的板块名称")
                
                # 获取表中所有板块名称作为参考
                try:
                    all_sectors_query = "SELECT DISTINCT 名称 FROM sector_trend LIMIT 100"
                    all_sectors = db.query_to_dataframe(all_sectors_query)
                    st.write(f"数据库中的板块名称示例: {all_sectors['名称'].tolist()[:10]}")
                except Exception as list_error:
                    st.warning(f"获取板块列表出错: {str(list_error)}")
                
                # 获取可能的名称匹配部分
                base_name = sector_name_upper.replace('概念', '').replace('板块', '').strip()
                st.write(f"用于模糊匹配的基础名称: '{base_name}'")
                
                try:
                    # 尝试参数化模糊匹配
                    fuzzy_query = "SELECT * FROM sector_trend WHERE UPPER(TRIM(名称)) LIKE %s"
                    fuzzy_param = f"%{base_name}%"
                    st.code(f"执行模糊匹配查询: {fuzzy_query} [参数: {fuzzy_param}]", language="sql")
                    trend_data = db.query_to_dataframe(fuzzy_query, params=[fuzzy_param])
                    st.write(f"模糊匹配找到 {len(trend_data)} 条记录")
                except Exception as fuzzy_query_error:
                    st.warning(f"模糊匹配查询出错: {str(fuzzy_query_error)}")
                    # 如果参数化查询失败，尝试直接执行SQL
                    fallback_fuzzy_query = f"""
                        SELECT * 
                        FROM sector_trend 
                        WHERE UPPER(TRIM(名称)) LIKE '%{base_name.replace("'", "''")}%'
                    """
                    st.code(f"尝试备用模糊查询: {fallback_fuzzy_query}", language="sql")
                    trend_data = db.query_to_dataframe(fallback_fuzzy_query)
                    st.write(f"备用模糊查询结果: {len(trend_data)} 条记录")
                
                if not trend_data.empty:
                    # 打印匹配到的名称
                    matched_names = trend_data['名称'].unique().tolist()
                    st.write(f"模糊匹配到的板块名称: {matched_names}")
            
            # 处理查询结果
            if not trend_data.empty:
                # 如果找到多个匹配记录，按日期分组
                trend_data['数据日期'] = pd.to_datetime(trend_data['数据日期']).dt.strftime('%Y-%m-%d')
                # 按日期分组，每个日期保留最佳匹配的记录
                trend_data_dict = {}
                for date, group in trend_data.groupby('数据日期'):
                    # 优先精确匹配，其次是包含匹配
                    exact_match = group[group['名称'].str.upper() == sector_name_upper]
                    if not exact_match.empty:
                        trend_data_dict[date] = exact_match.iloc[0]
                    else:
                        trend_data_dict[date] = group.iloc[0]  # 取第一个匹配
                
                st.write(f"板块趋势数据获取: 成功，找到 {len(trend_data_dict)} 个日期的数据")
            else:
                st.warning(f"未找到与 '{sector_name}' 匹配的板块趋势数据")
                # 添加一个名称_cir的空值，确保后续处理时不会出错
                st.write("创建空的板块趋势数据字典")
                trend_data_dict = {}
        except Exception as trend_error:
            error_message = str(trend_error).lower()
            
            if "timeout" in error_message or "connection" in error_message:
                st.warning(f"📶 板块趋势数据查询超时或网络问题: {str(trend_error)}")
                st.info("将继续处理，但可能缺少板块趋势数据")
            elif "table" in error_message and ("not exist" in error_message or "doesn't exist" in error_message):
                st.warning(f"📋 板块趋势数据表不存在: {str(trend_error)}")
                st.info("将继续处理，但没有板块趋势数据")
            else:
                st.warning(f"⚠️ 查询板块趋势数据时出错: {str(trend_error)}")
            
            # 记录详细错误，但不中断处理
            with st.expander("查看板块趋势数据错误详情"):
                st.code(traceback.format_exc())
                
            trend_data_dict = {}
        
        # 准备批量插入数据
        progress_text.write("步骤6/7: 准备批量插入数据...")
        progress_bar.progress(70, text="准备插入数据")
        
        # 遍历每个需要处理的日期
        records_to_insert = []
        
        for date_str in dates_to_process:
            # 获取该日期的资金流向数据
            cf_rows = capital_flow_data[pd.to_datetime(capital_flow_data['数据日期']).dt.strftime('%Y-%m-%d') == date_str]
            
            if cf_rows.empty:
                st.warning(f"日期 {date_str} 没有资金流向数据，跳过")
                continue
                
            cf_row = cf_rows.iloc[0]
            
            # 创建基础记录
            insert_data = {
                '代码': sector_code,
                '名称': sector_name,
                '数据日期': date_str
            }
            
            # 添加资金流向数据
            for col in cf_row.index:
                if col not in ['代码', '名称', '数据日期', '序']:
                    insert_data[col] = safe_get_value(cf_row, col)
            
            # 添加DDE分析数据
            if date_str in dde_data_dict:
                dde_row = dde_data_dict[date_str]
                for col in dde_row.index:
                    if col not in ['代码', '名称', '数据日期', '序', '最新', '涨幅%'] and col not in insert_data:
                        insert_data[col] = safe_get_value(dde_row, col)
            
            # 添加持仓分析数据
            if date_str in position_data_dict:
                position_row = position_data_dict[date_str]
                for col in position_row.index:
                    if col not in ['代码', '名称', '数据日期', '序', '最新', '涨幅%'] and col not in insert_data:
                        insert_data[col] = safe_get_value(position_row, col)
            
            # 添加板块趋势数据
            if date_str in trend_data_dict:
                trend_row = trend_data_dict[date_str]
                
                # 调试输出，查看板块趋势数据的原始列名
                if date_str == dates_to_process[0]:  # 只对第一个日期进行输出以减少日志
                    st.write(f"板块趋势数据原始字段: {list(trend_row.index)}")
                
                # 特殊处理涨幅字段 - 需要添加"_st"后缀以区分来源
                if "涨幅%" in trend_row.index:
                    insert_data["涨幅%_st"] = safe_get_value(trend_row, "涨幅%")
                
                if "3日涨幅%" in trend_row.index:
                    insert_data["3日涨幅%_st"] = safe_get_value(trend_row, "3日涨幅%")
                
                # 处理其他字段
                for col in trend_row.index:
                    # 跳过已经特殊处理的字段
                    if col in ["涨幅%", "3日涨幅%", "代码", "名称", "数据日期", "序"]:
                        continue
                    
                    # 对所有其他字段，如果插入数据中不存在则添加
                    if col not in insert_data:
                        insert_data[col] = safe_get_value(trend_row, col)
                
                # 确保存储原始板块名称
                if '名称_cir' not in insert_data and '名称' in trend_row.index:
                    insert_data['名称_cir'] = safe_get_value(trend_row, '名称')
            
            # 将NumPy类型转换为标准Python类型
            converted_data = {}
            for key, value in insert_data.items():
                converted_data[key] = convert_numpy_types(value)
            
            records_to_insert.append(converted_data)
        
        if not records_to_insert:
            progress_text.write("添加板块完成: 没有新的有效数据需要添加")
            progress_bar.progress(100, text="无数据添加")
            st.warning(f"板块 {sector_code} {sector_name} 没有新的有效数据可添加")
            return
        
        st.write(f"准备插入 {len(records_to_insert)} 条记录")
        
        # 预览部分数据
        preview_count = min(3, len(records_to_insert))
        st.write(f"数据预览 (前 {preview_count} 条):")
        preview_df = pd.DataFrame(records_to_insert[:preview_count])
        st.write(preview_df)
        
        # 执行批量插入
        progress_text.write(f"步骤7/7: 执行数据插入 ({len(records_to_insert)} 条记录)...")
        progress_bar.progress(90, text="插入数据")
        
        success_count = 0
        error_count = 0
        error_details = []
        
        for i, record in enumerate(records_to_insert):
            try:
                # 过滤掉值为None的键值对
                filtered_record = {k: v for k, v in record.items() if v is not None}
                
                if len(filtered_record) < 3:  # 至少需要代码、名称和日期字段
                    raise ValueError("有效字段太少，无法插入")
                
                columns = list(filtered_record.keys())
                values = list(filtered_record.values())
                
                # 检查并记录值的情况
                if i == 0 or i == len(records_to_insert) - 1:  # 仅记录第一条和最后一条以减少日志量
                    st.write(f"记录 #{i+1} ({filtered_record.get('数据日期', 'N/A')}) 字段数: {len(filtered_record)}")
                
                placeholders = ", ".join(["%s"] * len(columns))
                column_names = ", ".join([f"`{col}`" for col in columns])
                
                insert_query = f"""
                    INSERT INTO merged_data_specified ({column_names})
                    VALUES ({placeholders})
                """
                
                db.execute_update(insert_query, values)
                success_count += 1
                
                # 更新进度
                current_progress = 90 + (i / len(records_to_insert)) * 10
                progress_bar.progress(min(int(current_progress), 99), text=f"已插入 {i+1}/{len(records_to_insert)}")
                
            except Exception as insert_error:
                error_count += 1
                error_msg = f"插入日期 {record.get('数据日期', '未知')} 的数据时出错: {str(insert_error)}"
                st.error(error_msg)
                error_details.append(error_msg)
                # 继续处理其他记录而不是中断
        
        # 完成
        progress_text.write(f"板块添加完成! 成功: {success_count}, 失败: {error_count}")
        progress_bar.progress(100, text="操作完成")
        
        if success_count > 0:
            st.success(f"成功添加板块 {sector_code} {sector_name} 的 {success_count} 条历史数据到跟踪池")
        
        if error_count > 0:
            with st.expander(f"查看 {error_count} 条失败记录的详情"):
                for i, error in enumerate(error_details):
                    st.write(f"{i+1}. {error}")
            st.warning(f"有 {error_count} 条记录插入失败，点击上方查看详情")
            
    except Exception as e:
        progress_text.write("添加板块失败: 发生未知错误")
        progress_bar.progress(100, text="操作失败")
        
        error_message = str(e).lower()
        if "timeout" in error_message or "connection" in error_message:
            st.error(f"📶 数据库连接超时或网络问题: {str(e)}")
            st.info("💡 建议: 请等待几秒钟后再次尝试添加")
        elif "duplicate" in error_message or "already exists" in error_message:
            st.error(f"📋 数据重复: {str(e)}")
            st.info("💡 建议: 部分数据可能已经存在，请检查是否已添加该板块")
        else:
            st.error(f"❌ 添加板块失败: {str(e)}")
        
        with st.expander("查看详细错误信息"):
            st.code(traceback.format_exc())

# 从跟踪池中删除板块
def delete_sector_from_pool(sector_code):
    try:
        st.write("正在执行删除操作...")
        delete_query = f"""
            DELETE FROM merged_data_specified 
            WHERE 代码 = '{sector_code}'
        """
        st.code(delete_query, language="sql")
        db.execute_update(delete_query)
        st.success(f"成功从跟踪池中删除板块 {sector_code}")
    except Exception as e:
        st.error(f"删除板块失败: {str(e)}")
        st.write(f"错误详情: {str(e)}")
        st.write(traceback.format_exc())

# 主界面
st.header("板块管理")

# 显示当前跟踪的板块列表
st.subheader("当前跟踪的板块")
tracked_sectors = get_tracked_sectors()
if not tracked_sectors.empty:
    st.dataframe(tracked_sectors)
else:
    st.info("当前没有跟踪的板块")

# 添加新板块
st.subheader("添加新板块")
col1, col2 = st.columns(2)
with col1:
    sector_code = st.text_input("板块代码", placeholder="例如: BK0732")
with col2:
    sector_name = st.text_input("板块名称", placeholder="例如: 贵金属")

add_button = st.button("添加板块")
if add_button:
    # 验证输入是否有效
    is_valid = True
    if not sector_code or sector_code.strip() == "":
        st.error("请输入有效的板块代码！")
        is_valid = False
    if not sector_name or sector_name.strip() == "":
        st.error("请输入有效的板块名称！")
        is_valid = False
    
    if is_valid:
        st.write(f"开始添加板块: {sector_code} - {sector_name}")
        with st.spinner(f"正在添加板块 {sector_code} - {sector_name}..."):
            add_sector_to_pool(sector_code, sector_name)
        st.write("处理完成，点击下方按钮刷新页面")
        if st.button("刷新页面"):
            st.rerun()
    else:
        st.warning("请检查并修正上面的错误，然后重试")

# 删除板块
st.subheader("删除板块")
if not tracked_sectors.empty:
    sector_to_delete = st.selectbox(
        "选择要删除的板块",
        options=tracked_sectors['stock_code'].tolist(),
        format_func=lambda x: f"{x} - {tracked_sectors[tracked_sectors['stock_code'] == x]['stock_name'].iloc[0]}"
    )
    
    if st.button("删除选中板块"):
        with st.spinner(f"正在删除板块 {sector_to_delete}..."):
            delete_sector_from_pool(sector_to_delete)
        st.write("处理完成，点击下方按钮刷新页面")
        if st.button("刷新页面", key="refresh_after_delete"):
            st.rerun()
else:
    st.info("没有可删除的板块") 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
