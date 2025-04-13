import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
from backend.db import db
from io import BytesIO
import traceback
import subprocess
import sys
import os

# 页面配置
st.set_page_config(page_title="重点板块跟踪", page_icon="📌", layout="wide")

# 页面标题
st.title("📌 重点板块跟踪")

def get_stock_pool():
    """
    从merged_data_specified表获取当前股票池数据
    """
    try:
        # 尝试简化的查询，不使用特殊字符
        test_query = "SELECT COUNT(*) as count FROM merged_data_specified"
        test_df = db.query_to_dataframe(test_query)
        st.write(f"数据库连接测试成功，表中有 {test_df.iloc[0]['count']} 条记录")
        
        # 查询最新日期 - 不使用特殊字符
        latest_date_query = "SELECT MAX(数据日期) as latest_date FROM merged_data_specified"
        latest_date_df = db.query_to_dataframe(latest_date_query)
        
        if latest_date_df.empty or pd.isnull(latest_date_df.iloc[0]['latest_date']):
            st.error("无法获取最新数据日期")
            return pd.DataFrame()
        
        latest_date = latest_date_df.iloc[0]['latest_date']
        latest_date_str = pd.to_datetime(latest_date).strftime('%Y-%m-%d')
        
        # 创建一个简单的查询，避免所有特殊字符
        # 使用列别名来重命名含有特殊字符的字段
        query = f"""
        SELECT 
            代码 as stock_code, 
            名称 as stock_name, 
            数据日期 as data_date, 
            主力净流入 as main_net_inflow,
            最新 as latest_price,
            超大单净额 as huge_order_net,
            大单净额 as big_order_net,
            中单净额 as medium_order_net,
            小单净额 as small_order_net
        FROM merged_data_specified 
        WHERE 数据日期 = '{latest_date_str}'
        ORDER BY 主力净流入 DESC
        """
        
        # 显示查询语句
        with st.expander("查询SQL", expanded=False):
            st.code(query, language="sql")
            
        # 执行查询
        results_df = db.query_to_dataframe(query)
        
        # 如果需要涨幅%字段，可以在查询成功后再单独查询添加
        if not results_df.empty:
            try:
                # 获取所有股票代码作为条件
                stock_codes = "', '".join(results_df['stock_code'].tolist())
                
                # 首先尝试查询一条记录，看看有哪些字段
                fields_query = f"""
                SELECT * 
                FROM merged_data_specified 
                WHERE 数据日期 = '{latest_date_str}' 
                LIMIT 1
                """
                
                try:
                    # 查询所有字段来了解表结构
                    fields_df = db.query_to_dataframe(fields_query)
                    if not fields_df.empty:
                        # 显示所有字段名
                        with st.expander("表字段信息", expanded=False):
                            st.write("表中的所有字段:")
                            st.write(fields_df.columns.tolist())
                            
                        # 检查是否存在任何包含"涨幅"的字段
                        percent_fields = [col for col in fields_df.columns if '涨幅' in col]
                        if percent_fields:
                            # 在调试模式下才显示字段信息
                            debug_mode = False  # 设置为True打开调试信息
                            if debug_mode:
                                st.success(f"找到以下含有'涨幅'的字段: {percent_fields}")
                            
                            # 使用最简单的方法：查询所有字段，然后在Python中处理
                            try:
                                # 查询所有股票的所有数据
                                all_fields_query = f"""
                                SELECT * FROM merged_data_specified
                                WHERE 数据日期 = '{latest_date_str}'
                                AND 代码 IN ('{stock_codes}')
                                """
                                
                                # 执行查询获取所有字段
                                all_data_df = db.query_to_dataframe(all_fields_query)
                                
                                if not all_data_df.empty:
                                    # 在Python中提取需要的字段
                                    if '涨幅%' in all_data_df.columns:
                                        # 创建一个新的DataFrame只包含代码和涨幅%
                                        pct_df = pd.DataFrame({
                                            'stock_code': all_data_df['代码'],
                                            'change_pct': all_data_df['涨幅%']
                                        })
                                        
                                        # 合并数据
                                        results_df = pd.merge(results_df, pct_df, on='stock_code', how='left')
                                        if debug_mode:
                                            st.success("成功获取涨幅数据")
                                    else:
                                        if debug_mode:
                                            st.warning("查询结果中没有涨幅%字段")
                                else:
                                    if debug_mode:
                                        st.warning("未能查询到股票的完整数据")
                                    
                            except Exception as q_err:
                                if debug_mode:
                                    st.warning(f"查询所有字段失败: {str(q_err)}")
                                # 放弃查询涨幅，使用现有数据
                                st.info("将只显示基本数据，不包含涨幅信息")
                        else:
                            if debug_mode:
                                st.warning("表中没有找到包含'涨幅'的字段")
                except Exception as field_err:
                    st.warning(f"查询表字段出错: {str(field_err)}")
                
            except Exception as pct_err:
                st.warning(f"获取涨幅数据失败: {str(pct_err)}")
        
        if results_df.empty:
            st.warning(f"未找到{latest_date_str}的股票池数据")
        else:
            st.success(f"已加载{latest_date_str}的股票池数据，共{len(results_df)}只股票")
            
        return results_df
    
    except Exception as e:
        st.error(f"查询股票池数据时出错: {str(e)}")
        with st.expander("🔍 查看错误详情", expanded=True):
            st.exception(e)
            st.code(traceback.format_exc())
        return pd.DataFrame()

def get_stock_history(stock_codes, days=30):
    """
    获取指定股票的历史数据
    
    Args:
        stock_codes: 股票代码列表
        days: 获取的天数
    
    Returns:
        历史数据DataFrame
    """
    try:
        # 将股票代码列表转成SQL条件字符串
        codes_str = "', '".join(stock_codes)
        
        # 构建查询语句，获取最近N天的数据
        query = f"""
        SELECT * FROM (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY 代码 ORDER BY 数据日期 DESC) as rn
            FROM merged_data_specified
            WHERE 代码 IN ('{codes_str}')
        ) ranked
        WHERE rn <= {days}
        ORDER BY 代码, 数据日期 DESC
        """
        
        # 执行查询
        history_df = db.query_to_dataframe(query)
        
        # 删除辅助列
        if 'rn' in history_df.columns:
            history_df = history_df.drop('rn', axis=1)
        
        return history_df
    
    except Exception as e:
        st.error(f"获取历史数据时出错: {str(e)}")
        with st.expander("🔍 查看错误详情", expanded=False):
            st.exception(e)
            st.code(traceback.format_exc())
        return pd.DataFrame()

def display_stock_pool(df):
    """
    显示股票池数据
    """
    if df.empty:
        st.info("股票池为空，请添加股票")
        return
    
    # 添加勾选列
    if 'selected' not in st.session_state:
        st.session_state.selected = {}
        
    # 创建当前会话的临时状态保存
    if 'temp_selected' not in st.session_state:
        st.session_state.temp_selected = {}
    
    # 格式化数值列
    display_df = df.copy()
    
    # 修改列名为中文
    column_map = {
        'stock_code': '股票代码',
        'stock_name': '股票名称',
        'data_date': '日期',
        'change_pct': '涨幅(%)',
        'main_net_inflow': '主力净流入',
        'latest_price': '最新价',
        'huge_order_net': '超大单净额',
        'big_order_net': '大单净额',
        'medium_order_net': '中单净额',
        'small_order_net': '小单净额'
    }
    
    # 只重命名存在的列
    rename_cols = {col: column_map[col] for col in column_map if col in display_df.columns}
    display_df = display_df.rename(columns=rename_cols)
    
    # 设置数字格式
    numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
    format_dict = {}
    for col in numeric_cols:
        if '净流入' in col or '净额' in col:
            format_dict[col] = '{:,.2f}'  # 资金流相关列显示千分位
        elif '涨幅' in col:
            format_dict[col] = '{:.2f}%'  # 百分比列
        elif '最新价' in col:
            format_dict[col] = '{:.2f}'   # 价格列
    
    # 调整列的显示顺序
    if set(['股票代码', '股票名称', '日期', '涨幅(%)', '主力净流入', '最新价']).issubset(display_df.columns):
        # 优先显示重要列
        first_cols = ['股票代码', '股票名称', '日期', '涨幅(%)', '主力净流入', '最新价']
        other_cols = [col for col in display_df.columns if col not in first_cols]
        display_df = display_df[first_cols + other_cols]
    
    # 先显示股票池数据
    st.write("### 股票池数据:")
    
    # 计算适合的表格高度，避免显示太多空行
    row_height = 35  # 每行大约35像素
    header_height = 38  # 表头高度
    min_table_height = 150  # 最小表格高度
    calculated_height = min(len(display_df) * row_height + header_height, 400)
    table_height = max(calculated_height, min_table_height)
    
    # 显示表格 - 使用更兼容的方法处理索引
    # 重置索引，不显示原来的索引列
    display_df_reset = display_df.reset_index(drop=True)
    
    # 显示表格
    st.dataframe(
        display_df_reset.style.format(format_dict), 
        use_container_width=True,
        height=table_height
    )
    
    # 勾选区域
    st.write("### 选择股票导出:")
    selected_stocks = {}
    
    # 创建多列布局显示勾选框
    cols = st.columns(5)  # 5列布局
    
    # 按代码排序显示勾选框
    sorted_stocks = sorted(zip(display_df['股票代码'], display_df['股票名称']), key=lambda x: x[0])
    
    # 初始化临时状态
    for stock_code, _ in sorted_stocks:
        if stock_code not in st.session_state.temp_selected:
            st.session_state.temp_selected[stock_code] = st.session_state.selected.get(stock_code, False)
    
    # 检查是否需要切换状态
    if 'toggle_stock' in st.session_state and st.session_state.toggle_stock:
        stock_to_toggle = st.session_state.toggle_stock
        st.session_state.temp_selected[stock_to_toggle] = not st.session_state.temp_selected[stock_to_toggle]
        st.session_state.selected[stock_to_toggle] = st.session_state.temp_selected[stock_to_toggle]
        st.session_state.toggle_stock = None  # 重置切换标志
    
    # 为每个股票创建勾选框
    for i, (stock_code, stock_name) in enumerate(sorted_stocks):
        col_idx = i % 5
        
        # 创建勾选框，使用唯一key和当前临时状态
        with cols[col_idx]:
            # 创建按钮形式的勾选框，点击一次即可切换状态
            is_selected = st.session_state.temp_selected[stock_code]
            button_icon = "✅" if is_selected else "⬜"
            button_text = f"{button_icon} {stock_name} ({stock_code})"
            
            # 为按钮创建回调函数
            def on_click(code=stock_code):
                st.session_state.toggle_stock = code
            
            # 显示按钮
            st.button(button_text, key=f"btn_{stock_code}", on_click=on_click, use_container_width=True)
            
            # 如果已选中，添加到选中股票字典
            if st.session_state.selected.get(stock_code, False):
                selected_stocks[stock_code] = stock_name
    
    # 保存选中的股票信息
    st.session_state.selected_stocks = selected_stocks
    
    # 显示当前选中的股票数量和名称
    if selected_stocks:
        st.success(f"已选择 {len(selected_stocks)} 只股票: {', '.join([f'{name}({code})' for code, name in selected_stocks.items()])}")
    
    # 导出功能区域 - 优化布局
    st.write("### 导出数据:")
    
    # 选择导出时间范围
    export_option = st.selectbox(
        "选择导出范围",
        ["最新数据", "近30日数据", "近60日数据", "近90日数据", "全部数据"],
        index=0
    )
    
    # 导出按钮 - 放在单独一行，左右排列
    btn_cols = st.columns(2)
    
    with btn_cols[0]:
        if st.button("📤 导出所有股票数据", use_container_width=True, type="primary"):
            all_stocks = display_df['股票代码'].tolist()
            export_stock_data(all_stocks, export_option)
    
    with btn_cols[1]:
        if len(selected_stocks) > 0:
            if st.button(f"📤 导出已选{len(selected_stocks)}只股票", use_container_width=True, type="primary"):
                export_stock_data(list(selected_stocks.keys()), export_option)
        else:
            st.button("❗ 请先选择要导出的股票", disabled=True, use_container_width=True)

def export_stock_data(stock_codes, export_option):
    """
    导出股票数据
    
    Args:
        stock_codes: 股票代码列表
        export_option: 导出选项（"最新数据", "近30日数据", "近60日数据", "近90日数据", "全部数据"）
    """
    if not stock_codes:
        st.warning("没有选择要导出的股票")
        return
    
    # 根据选项确定要导出的天数
    days = 1
    if export_option == "近30日数据":
        days = 30
    elif export_option == "近60日数据":
        days = 60
    elif export_option == "近90日数据":
        days = 90
    elif export_option == "全部数据":
        days = 9999  # 一个足够大的数，表示全部数据
    
    # 获取股票历史数据
    with st.spinner(f"正在获取{export_option}，请稍候..."):
        history_df = get_stock_history(stock_codes, days)
    
    if history_df.empty:
        st.error(f"获取历史数据失败")
        return
    
    # 导出为Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        history_df.to_excel(writer, sheet_name=f"{export_option}", index=False)
    
    excel_data = output.getvalue()
    
    # 展示下载按钮
    today = pd.Timestamp.now().strftime('%Y%m%d')
    file_name = f"重点股票池_{len(stock_codes)}只_{export_option}_{today}.xlsx"
    
    st.download_button(
        label=f"下载 {export_option} Excel文件",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.ms-excel"
    )
    
    # 显示导出数据预览
    st.success(f"已准备好 {len(history_df)} 条记录的导出数据")
    with st.expander("预览导出数据", expanded=False):
        # 使用更兼容的方法处理索引
        history_df_reset = history_df.reset_index(drop=True)
        preview_height = min(len(history_df_reset) * 35 + 38, 400)
        st.dataframe(history_df_reset.style.format(), use_container_width=True, height=preview_height)

def main():
    """主函数"""
    # 获取当前股票池数据
    st.markdown("### 当前股票池")
    
    # 创建按钮列
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 刷新股票池数据", type="primary"):
            st.session_state.stock_pool_df = get_stock_pool()
    
    with col2:
        if st.button("📥 更新数据", type="secondary"):
            with st.spinner("正在更新数据，请稍候..."):
                try:
                    # 使用subprocess运行key_stocks_tracker.py
                    process = subprocess.run(
                        ["python", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "key_stocks_tracker.py")],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # 检查执行结果
                    if process.returncode == 0:
                        st.success("数据更新完成！")
                        # 显示部分输出
                        with st.expander("查看更新详情", expanded=False):
                            # 显示最后10行输出
                            output_lines = process.stdout.strip().split("\n")
                            st.code("\n".join(output_lines[-10:]) if len(output_lines) > 10 else process.stdout)
                        # 更新后自动刷新显示
                        st.session_state.stock_pool_df = get_stock_pool()
                    else:
                        st.error("数据更新过程中出现错误")
                        with st.expander("查看错误详情", expanded=True):
                            st.code(process.stderr)
                except subprocess.CalledProcessError as e:
                    st.error(f"更新数据时出错: 进程返回代码 {e.returncode}")
                    with st.expander("🔍 查看错误详情", expanded=True):
                        st.code(e.stderr)
                except Exception as e:
                    st.error(f"更新数据时出错: {str(e)}")
                    with st.expander("🔍 查看错误详情", expanded=True):
                        st.exception(e)
                        st.code(traceback.format_exc())
    
    # 初始化或使用现有数据
    if 'stock_pool_df' not in st.session_state:
        st.session_state.stock_pool_df = get_stock_pool()
    
    # 显示股票池数据
    display_stock_pool(st.session_state.stock_pool_df)
    
    # 使用说明
    with st.expander("使用说明"):
        st.markdown("""
        ### 使用说明
        1. 此页面展示当前重点股票池数据
        2. 数据来源于合并多表数据的 merged_data_specified 表
        3. 默认按照主力净流入金额降序排列
        4. 点击股票名称前的勾选框可以选择要操作的股票
        5. 可以选择导出范围（最新数据、近30日、近60日、近90日或全部数据）
        6. 可以导出所有股票数据或仅导出已选择的股票数据
        7. 点击刷新按钮更新显示
        8. 点击更新数据按钮将自动从源表同步数据库中**所有板块**的最新数据
        9. 如需管理数据日期，请使用"数据日期管理"页面
        """)

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
