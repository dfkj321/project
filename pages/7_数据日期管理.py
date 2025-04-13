import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
from backend.db import db
import traceback
import os
import sys
import time
import random

# 页面配置
st.set_page_config(page_title="数据日期管理", page_icon="🗓️", layout="wide")

# 页面标题
st.title("🗓️ 数据日期管理")

# 定义数据表列表
TABLES = [
    "capital_flow",      # 资金流
    "dde_analysis",      # DDE分析
    "position_analysis", # 持仓分析
    "sector_trend",      # 板块趋势
    "market_trend",      # 大盘趋势
    "merged_data_specified"  # 合并数据
]

def get_table_latest_date(table_name):
    """
    获取指定表的最新数据日期
    
    Args:
        table_name: 表名
        
    Returns:
        最新日期（如果没有数据则返回None）
    """
    try:
        query = f"SELECT MAX(数据日期) as latest_date FROM {table_name}"
        df = db.query_to_dataframe(query)
        if df.empty or pd.isnull(df.iloc[0]['latest_date']):
            return None
        return pd.to_datetime(df.iloc[0]['latest_date']).date()
    except Exception as e:
        st.error(f"获取{table_name}最新日期时出错: {str(e)}")
        return None

def get_table_earliest_date(table_name):
    """
    获取指定表的最早数据日期
    
    Args:
        table_name: 表名
        
    Returns:
        最早日期（如果没有数据则返回None）
    """
    try:
        query = f"SELECT MIN(数据日期) as earliest_date FROM {table_name}"
        df = db.query_to_dataframe(query)
        if df.empty or pd.isnull(df.iloc[0]['earliest_date']):
            return None
        return pd.to_datetime(df.iloc[0]['earliest_date']).date()
    except Exception as e:
        st.error(f"获取{table_name}最早日期时出错: {str(e)}")
        return None

def get_table_date_range(table_name):
    """
    获取指定表的数据日期范围
    
    Args:
        table_name: 表名
        
    Returns:
        (最早日期, 最新日期)的元组（如果没有数据则返回(None, None)）
    """
    earliest_date = get_table_earliest_date(table_name)
    latest_date = get_table_latest_date(table_name)
    
    # 获取表中数据的总日期数
    try:
        query = f"SELECT COUNT(DISTINCT 数据日期) as date_count FROM {table_name}"
        df = db.query_to_dataframe(query)
        date_count = df.iloc[0]['date_count'] if not df.empty else 0
    except Exception:
        date_count = 0
        
    return (earliest_date, latest_date, date_count)

def get_table_date_count(table_name, date_str):
    """
    获取指定表指定日期的数据记录数
    
    Args:
        table_name: 表名
        date_str: 日期字符串
        
    Returns:
        记录数量
    """
    try:
        query = f"SELECT COUNT(*) as count FROM {table_name} WHERE 数据日期 = '{date_str}'"
        df = db.query_to_dataframe(query)
        return df.iloc[0]['count'] if not df.empty else 0
    except Exception as e:
        st.error(f"获取{table_name}记录数时出错: {str(e)}")
        return 0

def delete_table_date_data(table_name, date_str):
    """
    删除指定表指定日期的数据
    
    Args:
        table_name: 表名
        date_str: 日期字符串
        
    Returns:
        删除的记录数
    """
    try:
        # 先获取要删除的记录数
        count = get_table_date_count(table_name, date_str)
        if count == 0:
            return 0
            
        # 执行删除
        query = f"DELETE FROM {table_name} WHERE 数据日期 = '{date_str}'"
        db.execute_update(query)
        
        return count
    except Exception as e:
        st.error(f"删除{table_name}数据时出错: {str(e)}")
        with st.expander("🔍 查看错误详情", expanded=True):
            st.exception(e)
            st.code(traceback.format_exc())
        return 0

def trash_animation():
    """显示垃圾桶动画"""
    # 创建一个容器来放置动画
    container = st.empty()
    
    # 垃圾桶动画帧
    trash_frames = [
        """
        🗑️
        """,
        """
          🗑️
         💾
        """,
        """
           🗑️
          💾
        """,
        """
            🗑️
           💾
        """,
        """
             🗑️
            💾
        """,
        """
              🗑️
             💾
        """,
        """
               🗑️
              💾
        """,
        """
                🗑️
               💾
        """,
        """
                 🗑️
                💾
        """,
        """
                  🗑️
                 💾
        """,
        """
                   🗑️
                  💾
        """,
        """
                    🗑️
                   💾
        """,
        """
                     🗑️
                    💾
        """,
        """
                      🗑️
                     💾
        """,
        """
                       🗑️
                      💾
        """,
        """
                        🗑️
                       💾
        """,
        """
                         🗑️
                        💾
        """,
        """
                          🗑️
                          💥
        """,
        """
                          🗑️
                          ✨
        """,
        """
                          🗑️
                          
        """,
        """
                          🗑️
                          ✓
        """
    ]
    
    # 显示动画
    for frame in trash_frames:
        container.markdown(f"<div style='font-size:24px; text-align:center;'>{frame}</div>", unsafe_allow_html=True)
        time.sleep(0.1)
    
    # 随机选择一个有趣的完成消息
    finish_messages = [
        "搞定了！数据已被扔进了数字黑洞 🕳️",
        "删除成功！这些数据现在正在数字天堂 👼",
        "删除完毕！数据已被分解成比特粒子 ⚛️",
        "成功！那些数据现在只存在于平行宇宙中 🌌",
        "搞定！数据已被送入回收站的无底洞 ♻️",
        "删除成功！数据已化为数字尘埃 ✨",
        "完成！数据已被数字粉碎机处理 🔨",
        "干得好！数据已被数字橡皮擦抹除 🧹"
    ]
    
    # 显示完成消息
    container.markdown(f"<div style='font-size:20px; text-align:center; color:#FF4B4B; background-color:#FFF0F0; padding:10px; border-radius:5px; margin:10px 0;'><b>{random.choice(finish_messages)}</b></div>", unsafe_allow_html=True)
    
    # 返回容器以便后续清除
    return container

def main():
    # 显示各表数据日期范围信息
    st.write("## 各表数据日期范围")
    
    # 创建信息卡片
    cols = st.columns(3)
    
    # 获取并显示各表的日期范围
    latest_dates = {}
    earliest_dates = {}
    
    for i, table in enumerate(TABLES):
        # 获取日期范围
        earliest_date, latest_date, date_count = get_table_date_range(table)
        
        # 保存日期信息用于后续操作
        latest_dates[table] = latest_date
        earliest_dates[table] = earliest_date
        
        # 计算列索引（0-2循环）
        col_idx = i % 3
        
        # 根据表名显示中文名称
        table_name_map = {
            "capital_flow": "资金流",
            "dde_analysis": "DDE分析",
            "position_analysis": "持仓分析",
            "sector_trend": "板块趋势",
            "market_trend": "大盘趋势",
            "merged_data_specified": "合并数据"
        }
        table_display_name = table_name_map.get(table, table)
        
        # 显示日期信息卡片
        with cols[col_idx]:
            if earliest_date and latest_date:
                # 计算日期跨度
                date_span = (latest_date - earliest_date).days + 1
                # 显示信息卡
                st.info(f"""
                **{table_display_name}**表日期范围:
                - **开始日期**: {earliest_date}
                - **结束日期**: {latest_date}
                - **数据天数**: {date_count} 天
                - **日期跨度**: {date_span} 天
                """)
            else:
                st.info(f"**{table_display_name}**表: 无数据")
    
    # 表格记录删除功能
    st.write("## 删除指定日期数据")
    
    # 选择要操作的表
    selected_table = st.selectbox(
        "选择要操作的数据表", 
        options=TABLES,
        format_func=lambda x: f"{table_name_map.get(x, x)}表 ({x})"
    )
    
    if selected_table:
        # 显示该表的日期范围
        latest_date = latest_dates[selected_table]
        earliest_date = earliest_dates[selected_table]
        
        if latest_date:
            # 显示表的日期范围信息
            st.write(f"表 **{selected_table}** 的数据日期范围: **{earliest_date}** 至 **{latest_date}**")
            
            # 创建日期选择器
            with st.form(f"delete_form_{selected_table}"):
                st.write("### 选择要删除的日期")
                # 默认选择最新日期，但可以选择范围内的任意日期
                date_to_delete = st.date_input(
                    "选择日期", 
                    value=latest_date,
                    min_value=earliest_date,
                    max_value=latest_date
                )
                date_str = date_to_delete.strftime('%Y-%m-%d')
                
                # 查询该日期的记录数
                record_count = get_table_date_count(selected_table, date_str)
                
                if record_count > 0:
                    st.write(f"该日期在**{table_name_map.get(selected_table, selected_table)}**表中有 **{record_count}** 条记录")
                    
                    # 警告框和确认
                    st.warning(f"⚠️ 删除操作不可撤销！请确认要删除 {table_name_map.get(selected_table, selected_table)}表中 {date_str} 的全部 {record_count} 条记录。")
                    confirm = st.checkbox("**我已了解风险并确认删除**")
                    
                    # 提交按钮 - 移除disabled参数，让表单自己处理禁用逻辑
                    if st.form_submit_button("执行删除", type="primary"):
                        if confirm:
                            with st.spinner(f"正在删除 {selected_table} 表 {date_str} 的数据..."):
                                deleted_count = delete_table_date_data(selected_table, date_str)
                            
                            if deleted_count > 0:
                                # 创建一个更醒目的成功通知
                                
                                # 显示垃圾桶动画
                                animation_container = trash_animation()
                                
                                # 气球效果
                                st.balloons()
                                
                                # 添加操作摘要卡片
                                st.success(f"✅ 已成功从 {table_name_map.get(selected_table, selected_table)}表 删除 {date_str} 的 {deleted_count} 条记录")
                                
                                st.info(f"""
                                ### 操作摘要
                                - **表**: {table_name_map.get(selected_table, selected_table)} ({selected_table})
                                - **日期**: {date_str}
                                - **删除记录数**: {deleted_count}
                                - **操作时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
                                
                                删除操作已完成，请点击下方的"刷新页面数据"按钮查看最新数据状态。
                                """)
                                
                                # 添加一些有趣的效果
                                st.markdown(f"""
                                <style>
                                @keyframes celebrate {{
                                  0% {{ transform: scale(1); }}
                                  50% {{ transform: scale(1.1); }}
                                  100% {{ transform: scale(1); }}
                                }}
                                .celebrate {{
                                  animation: celebrate 1s ease-in-out infinite;
                                  display: inline-block;
                                }}
                                </style>
                                <div style="text-align:center; margin:20px 0;">
                                <span class="celebrate" style="font-size:40px;">🎉</span>
                                <span class="celebrate" style="font-size:40px; animation-delay: 0.2s;">🗑️</span>
                                <span class="celebrate" style="font-size:40px; animation-delay: 0.4s;">✨</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 设置一个会话状态变量，表示删除成功
                                st.session_state.delete_success = True
                                st.session_state.deleted_table = selected_table
                                st.session_state.deleted_date = date_str
                                st.session_state.deleted_count = deleted_count
                                
                                # 2秒后清除动画容器
                                time.sleep(2)
                                animation_container.empty()
                                
                                # 不再自动重新运行页面，让用户欣赏动画效果
                                # st.rerun()
                            else:
                                st.error("删除操作未执行或失败")
                                st.info("可能的原因：数据库连接问题、权限不足或数据已被其他进程修改")
                        else:
                            st.error("⚠️ 请先勾选确认框以确认删除操作")
                            st.info("为保护数据安全，必须先确认了解风险才能执行删除操作")
                else:
                    st.info(f"所选日期 {date_str} 在 {table_name_map.get(selected_table, selected_table)}表 中没有数据")
        else:
            st.warning(f"表 {selected_table} 中没有数据")
    
    # 在表单外部处理刷新操作
    if st.session_state.get('delete_success', False):
        # 显示删除成功提示（表单外部）
        st.markdown(f"""
        <div style="background-color:#E8F0FE; padding:15px; border-radius:10px; border-left:5px solid #1E88E5; margin:10px 0;">
            <h3 style="color:#1E88E5; margin-top:0;">✅ 删除操作成功</h3>
            <p>已从 <b>{table_name_map.get(st.session_state.deleted_table, st.session_state.deleted_table)}</b> 表中删除 <b>{st.session_state.deleted_date}</b> 日期的 <b>{st.session_state.deleted_count}</b> 条记录</p>
            <p style="margin-bottom:0;">查看下面的最新数据状态，或刷新页面继续操作。</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 表单外部添加刷新按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 刷新页面状态", type="primary", use_container_width=True):
                # 清除会话状态
                st.session_state.delete_success = False
                if 'deleted_table' in st.session_state:
                    del st.session_state.deleted_table
                if 'deleted_date' in st.session_state:
                    del st.session_state.deleted_date
                if 'deleted_count' in st.session_state:
                    del st.session_state.deleted_count
                st.rerun()
    
    # 添加页面使用说明
    with st.expander("使用说明", expanded=False):
        st.markdown("""
        ### 数据日期管理工具使用说明
        
        此工具用于管理各数据表的日期数据，主要功能包括：
        
        1. **查看各表最新日期**: 在页面顶部显示各表的最新数据日期，方便了解数据更新状态
        2. **删除指定日期数据**: 可以针对特定表删除指定日期的全部数据记录
        
        **使用流程**:
        1. 在下拉菜单中选择要操作的数据表
        2. 在日期选择器中选择要删除的具体日期
        3. 系统会显示该日期在所选表中的记录数量
        4. 确认删除风险，勾选确认框
        5. 点击"执行删除"按钮完成操作
        
        **注意事项**:
        - 删除操作不可撤销，请谨慎操作
        - 删除合并表(merged_data_specified)的数据不会影响源数据表
        - 同样，删除源数据表的数据也不会自动更新合并表
        - 建议在操作后检查相关表的数据一致性
        """)

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
