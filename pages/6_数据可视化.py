import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import traceback
from backend.db import db

# 页面配置
st.set_page_config(page_title="数据可视化", page_icon="📊", layout="wide")

# 页面标题
st.title("📊 数据可视化")

# 定义图表配置
CHART_CONFIGS = {
    '主力资金图': {
        'table': 'capital_flow',
        'default_fields': ['主力净流入'],
        'fields': [
            '主力净流入', '超大单净额', '大单净额', '中单净额', '小单净额', 
            '超大单流入', '超大单流出', '大单流入', '大单流出', 
            '中单流入', '中单流出', '小单流入', '小单流出',
            '超大单净占比%', '大单净占比%', '中单净占比%', '小单净占比%'
        ]
    },
    'DDE行为图': {
        'table': 'dde_analysis',
        'default_fields': ['DDX', 'DDY', 'DDZ'],
        'fields': [
            'DDX', 'DDY', 'DDZ', '5日DDX', '5日DDY', '10日DDX', '10日DDY',
            '连续', '5日内', '10日内', '特大买入%', '特大卖出%', '特大单净比%',
            '大单买入%', '大单卖出%', '大单净比%'
        ]
    },
    '增仓结构图': {
        'table': 'position_analysis',
        'default_fields': ['今日增仓占比'],
        'fields': [
            '今日增仓占比', '今日排名', '今日排名变化', '今日涨幅%',
            '3日增仓占比', '3日排名', '3日排名变化', '3日涨幅%',
            '5日增仓占比', '5日排名', '5日排名变化', '5日涨幅%',
            '10日增仓占比', '10日排名', '10日排名变化', '10日涨幅%'
        ]
    },
    '板块情绪图': {
        'table': 'sector_trend',
        'default_fields': ['涨停家数'],
        'fields': [
            '成交量', '涨停家数', '涨家数', '跌家数', '涨跌比', 
            '换手%', '3日换手%', '涨幅%', '涨速%', '金额', 
            '总市值', '流通市值', '平均收益', '平均股本', '市盈率'
        ]
    },
    '大盘监测图': {
        'table': 'market_trend',
        'default_fields': ['最新'],
        'fields': [
            '最新', '涨幅%', '开盘', '最高', '最低', '昨收', '成交量', '成交额'
        ]
    }
}

# 定义指标对应的颜色映射
INDICATOR_COLORS = {
    # 主力资金指标颜色
    '主力净流入': '#ff4d4f',
    '超大单净额': '#ff7a45',
    '大单净额': '#fa8c16',
    '中单净额': '#ffc53d',
    '小单净额': '#ffec3d',
    '超大单流入': '#ff7a45',
    '超大单流出': '#ff7a45',
    '大单流入': '#fa8c16',
    '大单流出': '#fa8c16',
    '中单流入': '#ffc53d',
    '中单流出': '#ffc53d',
    '小单流入': '#ffec3d',
    '小单流出': '#ffec3d',
    '超大单净占比%': '#ff7a45',
    '大单净占比%': '#fa8c16',
    '中单净占比%': '#ffc53d',
    '小单净占比%': '#ffec3d',
    
    # DDE指标颜色
    'DDX': '#722ed1',
    'DDY': '#2f54eb',
    'DDZ': '#1890ff',
    '5日DDX': '#722ed1',
    '5日DDY': '#2f54eb',
    '10日DDX': '#722ed1',
    '10日DDY': '#2f54eb',
    '连续': '#13c2c2',
    '5日内': '#13c2c2',
    '10日内': '#13c2c2',
    '特大买入%': '#ff4d4f',
    '特大卖出%': '#52c41a',
    '特大单净比%': '#1890ff',
    '大单买入%': '#ff4d4f',
    '大单卖出%': '#52c41a',
    '大单净比%': '#1890ff',
    
    # 增仓结构指标颜色
    '今日增仓占比': '#ff4d4f',
    '今日排名': '#ffec3d',
    '今日排名变化': '#52c41a',
    '今日涨幅%': '#1890ff',
    '3日增仓占比': '#ff7a45',
    '3日排名': '#ffc53d',
    '3日排名变化': '#52c41a',
    '3日涨幅%': '#1890ff',
    '5日增仓占比': '#fa8c16',
    '5日排名': '#ffc53d',
    '5日排名变化': '#52c41a',
    '5日涨幅%': '#1890ff',
    '10日增仓占比': '#fa541c',
    '10日排名': '#ffd666',
    '10日排名变化': '#52c41a',
    '10日涨幅%': '#1890ff',
    
    # 板块情绪指标颜色
    '成交量': '#1890ff',
    '涨停家数': '#ff4d4f',
    '涨家数': '#ff7a45',
    '跌家数': '#52c41a',
    '涨跌比': '#faad14',
    '换手%': '#1890ff',
    '3日换手%': '#1890ff',
    '涨幅%': '#ff4d4f',
    '涨速%': '#ff7a45',
    '金额': '#13c2c2',
    '总市值': '#722ed1',
    '流通市值': '#2f54eb',
    '平均收益': '#fa8c16',
    '平均股本': '#13c2c2',
    '市盈率': '#eb2f96',
    
    # 大盘监测指标颜色
    '最新': '#1890ff',
    '涨幅%': '#ff4d4f',
    '开盘': '#52c41a',
    '最高': '#ff7a45',
    '最低': '#52c41a',
    '昨收': '#ffc53d',
    '成交量': '#722ed1',
    '成交额': '#2f54eb'
}

# 获取跟踪的板块列表
@st.cache_data(ttl=300)
def get_tracked_sectors():
    try:
        query = """
            SELECT DISTINCT 代码 as stock_code, 名称 as stock_name 
            FROM merged_data_specified 
            ORDER BY 代码
        """
        results_df = db.query_to_dataframe(query)
        return results_df
    except Exception as e:
        st.error(f"获取板块列表失败: {str(e)}")
        return pd.DataFrame(columns=['stock_code', 'stock_name'])

# 清理数据，处理缺失值
def clean_data_for_visualization(df):
    """清理数据，为可视化做准备
    
    1. 将日期转换为datetime类型
    2. 将空字符串转为NaN
    3. 确保数值类型字段为数值
    """
    if df.empty:
        return df
        
    # 确保日期格式正确
    if '数据日期' in df.columns:
        df['数据日期'] = pd.to_datetime(df['数据日期'])
    
    # 将空字符串转为NaN
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].replace('', np.nan)
    
    # 尝试将能转换为数值的列转为数值类型
    for col in df.columns:
        if col not in ['代码', '名称', '数据日期']:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    
    return df

# 获取标的历史数据
@st.cache_data(ttl=300)
def get_historical_data(table_name, sector_code, date_range=30):
    try:
        # 对于大盘监测图，使用不同的处理方式
        if table_name == 'market_trend':
            query = f"""
                SELECT * FROM market_trend
                ORDER BY 数据日期 DESC
                LIMIT {date_range}
            """
        else:
            # 构建查询语句，获取最近N天的数据
            query = f"""
                SELECT * FROM {table_name}
                WHERE 代码 = '{sector_code}'
                ORDER BY 数据日期 DESC
                LIMIT {date_range}
            """
        
        # 执行查询
        df = db.query_to_dataframe(query)
        
        # 清理数据
        df = clean_data_for_visualization(df)
        
        return df
    except Exception as e:
        st.error(f"获取历史数据失败: {str(e)}")
        st.write(traceback.format_exc())
        return pd.DataFrame()

# 获取合并表的历史数据
@st.cache_data(ttl=60)  # 降低缓存时间以便调试
def get_merged_historical_data(sector_code, date_range=30):
    try:
        # 调试信息
        st.session_state['debug_info'] = f"尝试获取{sector_code}最近{date_range}天的数据"
        
        # 使用日期子查询确保我们能获取到最近N天的不同日期数据
        query = f"""
            SELECT m.* FROM merged_data_specified m
            JOIN (
                SELECT DISTINCT 数据日期
                FROM merged_data_specified
                WHERE 代码 = '{sector_code}'
                ORDER BY 数据日期 DESC
                LIMIT {date_range}
            ) d ON m.数据日期 = d.数据日期
            WHERE m.代码 = '{sector_code}'
            ORDER BY m.数据日期
        """
        
        # 记录SQL查询供调试
        st.session_state['debug_sql'] = query
        
        # 执行查询
        df = db.query_to_dataframe(query)
        
        # 显示调试信息
        st.session_state['debug_info'] += f"，查询返回{len(df)}行"
        
        # 清理数据
        df = clean_data_for_visualization(df)
        
        return df
    except Exception as e:
        error_msg = f"获取合并历史数据失败: {str(e)}"
        st.session_state['debug_info'] = error_msg
        st.error(error_msg)
        st.write(traceback.format_exc())
        return pd.DataFrame()

# 获取多个板块的合并历史数据
@st.cache_data(ttl=60)
def get_multiple_sectors_data(sector_codes, date_range=30):
    """
    获取多个板块的历史数据，并为每个DataFrame添加板块标识
    
    Args:
        sector_codes: 板块代码列表
        date_range: 日期范围，默认30天
    
    Returns:
        包含多个板块数据的字典，键为板块代码
    """
    result = {}
    
    if not sector_codes:
        return result
    
    # 记录调试信息
    st.session_state['debug_info'] = f"尝试获取{len(sector_codes)}个板块最近{date_range}天的数据"
    
    try:
        for sector in sector_codes:
            # 获取单个板块数据
            df = get_merged_historical_data(sector, date_range)
            if not df.empty:
                result[sector] = df
                
        return result
    except Exception as e:
        error_msg = f"获取多板块历史数据失败: {str(e)}"
        st.session_state['debug_info'] = error_msg
        st.error(error_msg)
        st.write(traceback.format_exc())
        return {}

# 创建图表
def create_chart(chart_title, df, value_columns, chart_style='line'):
    """
    创建交互式折线图显示多个字段随时间的变化
    
    Args:
        chart_title: 图表标题
        df: 包含数据的DataFrame
        value_columns: 要显示的数值列名列表
        chart_style: 图表样式（'line'或'bar'）
    """
    date_col = '数据日期'  # 使用固定的日期列名
    
    if not df.empty and date_col in df.columns:
        # 尝试将日期列转换为字符串以简化格式
        try:
            # 提取日期部分，转为简短格式 (MM-DD)
            date_values = []
            for d in df[date_col]:
                if isinstance(d, (datetime, pd.Timestamp)):
                    date_values.append(d.strftime('%m-%d'))
                elif pd.notna(d):
                    # 如果是字符串，先尝试转换为datetime
                    try:
                        date_obj = pd.to_datetime(d)
                        date_values.append(date_obj.strftime('%m-%d'))
                    except:
                        # 如果转换失败但是字符串，尝试直接提取日期部分
                        date_str = str(d)
                        if len(date_str) > 10:  # 如果包含时间部分
                            date_parts = date_str[:10].split('-')  # 只保留日期部分
                            if len(date_parts) == 3:
                                # 格式化为MM-DD，确保月份和日期是两位数
                                month = date_parts[1].zfill(2)
                                day = date_parts[2].zfill(2)
                                date_values.append(f"{month}-{day}")
                            else:
                                date_values.append(date_str[:10])
                        else:
                            date_values.append(date_str)
                else:
                    date_values.append('')
        except Exception as e:
            st.error(f"日期格式转换错误: {e}")
            # 如果转换失败，使用原始值的字符串表示
            date_values = [str(d) for d in df[date_col]]
        
        # 创建图表
        fig = go.Figure()
        
        # 默认颜色列表（用于没有在颜色映射中定义的指标）
        default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # 添加每个字段的数据
        for i, column in enumerate(value_columns):
            if column in df.columns:  # 确保列在DataFrame中存在
                valid_mask = ~pd.isna(df[column])
                if date_values and sum(valid_mask) > 0:
                    # 获取指标对应的颜色，如果没有预定义则使用默认颜色
                    color = INDICATOR_COLORS.get(column, default_colors[i % len(default_colors)])
                    
                    if chart_style == 'line':
                        fig.add_trace(go.Scatter(
                            x=[date_values[j] for j in range(len(date_values)) if valid_mask.iloc[j]],
                            y=df.loc[valid_mask, column],
                            mode='lines+markers',
                            name=column,
                            line=dict(color=color, width=2),
                            marker=dict(size=6)
                        ))
                    else:  # bar chart
                        # 获取有效的值
                        valid_x = [date_values[j] for j in range(len(date_values)) if valid_mask.iloc[j]]
                        valid_y = df.loc[valid_mask, column].values
                        
                        # 如果是柱状图且不是使用多列数据，则根据数值设置颜色
                        if len(value_columns) == 1:
                            # 创建颜色数组，上涨为红色(#ff4d4f)，下跌为绿色(#52c41a)
                            color_array = ['#ff4d4f' if y >= 0 else '#52c41a' for y in valid_y]
                        else:
                            # 多列数据时，为每列使用统一的颜色
                            color_array = color
                        
                        fig.add_trace(go.Bar(
                            x=valid_x,
                            y=valid_y,
                            name=column,
                            marker_color=color_array
                        ))
        
        # 设置图表布局
        fig.update_layout(
            title=chart_title,
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(family="Arial", size=12)
            ),
            xaxis=dict(
                title='日期',
                tickangle=45,  # 增加角度使标签不重叠
                tickfont=dict(family="Arial", size=10),
                gridcolor='lightgray',
                showgrid=True,
                type='category',  # 使用类别类型而不是时间类型
                tickmode='auto',  # 自动确定最合适的刻度数量
                nticks=10  # 限制最大刻度数，避免过度拥挤
            ),
            yaxis=dict(
                title=value_columns[0] if len(value_columns) == 1 else '数值',
                tickfont=dict(family="Arial", size=10),
                gridcolor='lightgray',
                showgrid=True
            ),
            font=dict(family="Arial")
        )
        
        return fig
    else:
        st.warning(f"没有足够的数据来创建图表。日期列: 数据日期, 数据列: {value_columns}")
        return None

# 创建多板块比较图表
def create_multi_sector_chart(chart_title, sectors_data, sector_names, value_column, chart_style='line'):
    """
    创建多板块比较图表
    
    Args:
        chart_title: 图表标题
        sectors_data: 包含多个板块数据的字典，键为板块代码
        sector_names: 板块代码到名称的映射字典
        value_column: 要显示的数值列名
        chart_style: 图表样式（'line'或'bar'）
    """
    if not sectors_data:
        st.warning(f"没有数据来创建多板块比较图表")
        return None
    
    date_col = '数据日期'
    fig = go.Figure()
    
    # 默认颜色列表
    default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # 为每个板块添加一条线/一组柱状图
    for i, (sector_code, df) in enumerate(sectors_data.items()):
        if df.empty or date_col not in df.columns or value_column not in df.columns:
            continue
            
        # 获取板块名称
        sector_label = f"{sector_code} - {sector_names.get(sector_code, '未知')}"
        
        # 处理日期格式
        try:
            date_values = [d.strftime('%m-%d') if isinstance(d, (datetime, pd.Timestamp)) 
                          else pd.to_datetime(d).strftime('%m-%d') 
                          for d in df[date_col] if pd.notna(d)]
        except Exception:
            date_values = [str(d) for d in df[date_col] if pd.notna(d)]
        
        # 获取有效的值掩码
        valid_mask = ~pd.isna(df[value_column])
        
        # 如果有有效数据
        if date_values and sum(valid_mask) > 0:
            # 使用颜色列表中的颜色
            color = default_colors[i % len(default_colors)]
            
            if chart_style == 'line':
                fig.add_trace(go.Scatter(
                    x=[date_values[j] for j in range(len(date_values)) if valid_mask.iloc[j]],
                    y=df.loc[valid_mask, value_column],
                    mode='lines+markers',
                    name=sector_label,
                    line=dict(color=color, width=2),
                    marker=dict(size=6)
                ))
            else:  # bar chart - 使用分组柱状图
                fig.add_trace(go.Bar(
                    x=[date_values[j] for j in range(len(date_values)) if valid_mask.iloc[j]],
                    y=df.loc[valid_mask, value_column],
                    name=sector_label,
                    marker_color=color
                ))
    
    # 设置图表布局
    fig.update_layout(
        title=f"{chart_title} - {value_column}",
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(family="Arial", size=12)
        ),
        xaxis=dict(
            title='日期',
            tickangle=45,
            tickfont=dict(family="Arial", size=10),
            gridcolor='lightgray',
            showgrid=True,
            type='category',
            tickmode='auto',
            nticks=10
        ),
        yaxis=dict(
            title=value_column,
            tickfont=dict(family="Arial", size=10),
            gridcolor='lightgray',
            showgrid=True
        ),
        font=dict(family="Arial"),
        barmode='group' if chart_style == 'bar' else None  # 分组柱状图
    )
    
    return fig

# 获取大盘指数列表
@st.cache_data(ttl=300)
def get_market_indices():
    try:
        query = """
            SELECT DISTINCT 代码 as index_code, 名称 as index_name 
            FROM market_trend 
            ORDER BY 代码
        """
        results_df = db.query_to_dataframe(query)
        return results_df
    except Exception as e:
        st.error(f"获取大盘指数列表失败: {str(e)}")
        return pd.DataFrame(columns=['index_code', 'index_name'])

# 获取大盘指数历史数据
@st.cache_data(ttl=60)
def get_market_historical_data(index_code, date_range=30):
    try:
        # 调试信息
        st.session_state['market_debug_info'] = f"尝试获取大盘指数{index_code}最近{date_range}天的数据"
        
        # 使用日期子查询确保我们能获取到最近N天的不同日期数据
        query = f"""
            SELECT m.* FROM market_trend m
            JOIN (
                SELECT DISTINCT 数据日期
                FROM market_trend
                WHERE 代码 = '{index_code}'
                ORDER BY 数据日期 DESC
                LIMIT {date_range}
            ) d ON m.数据日期 = d.数据日期
            WHERE m.代码 = '{index_code}'
            ORDER BY m.数据日期
        """
        
        # 记录SQL查询供调试
        st.session_state['market_debug_sql'] = query
        
        # 执行查询
        df = db.query_to_dataframe(query)
        
        # 显示调试信息
        st.session_state['market_debug_info'] += f"，查询返回{len(df)}行"
        
        # 清理数据
        df = clean_data_for_visualization(df)
        
        return df
    except Exception as e:
        error_msg = f"获取大盘指数历史数据失败: {str(e)}"
        st.session_state['market_debug_info'] = error_msg
        st.error(error_msg)
        st.write(traceback.format_exc())
        return pd.DataFrame()

# 主应用
def main():
    # 清除缓存按钮
    if st.sidebar.button("清除缓存"):
        st.cache_data.clear()
        st.rerun()
        
    # 侧边栏配置
    st.sidebar.title("数据设置")
    
    # 获取跟踪的板块 - 提前获取以便在所有选项卡中使用
    tracked_sectors = get_tracked_sectors()
    if tracked_sectors.empty:
        st.warning("没有找到跟踪的板块数据。请先在'板块管理工具'中添加需要跟踪的板块。")
        return
        
    # 创建板块代码到名称的映射
    sector_name_map = dict(zip(tracked_sectors['stock_code'], tracked_sectors['stock_name']))
    
    # 添加全局板块选择器到侧边栏
    st.sidebar.markdown("### 全局板块选择")
    st.sidebar.markdown("_选择一个板块并应用到所有图表_")
    
    # 存储上一次选择的全局板块，以便检测变化
    if "last_global_sector" not in st.session_state:
        st.session_state.last_global_sector = None
        
    # 初始化常用板块
    if "favorite_sectors" not in st.session_state:
        st.session_state.favorite_sectors = []
        
    # 常用板块选择区域
    if st.session_state.favorite_sectors:
        st.sidebar.markdown("#### ⭐ 常用板块")
        # 分割常用板块为两列显示
        fav_cols = st.sidebar.columns(2)
        for i, sector_code in enumerate(st.session_state.favorite_sectors):
            col_idx = i % 2
            # 创建常用板块按钮
            if fav_cols[col_idx].button(f"{sector_code} {sector_name_map.get(sector_code, '')}",
                                       key=f"fav_btn_{sector_code}", use_container_width=True):
                # 选中该常用板块
                st.session_state.global_sector = sector_code
                st.rerun()
                
        # 添加清除常用板块的按钮
        if st.sidebar.button("🗑️ 清除常用板块", key="clear_favorites"):
            st.session_state.favorite_sectors = []
            st.rerun()
            
        st.sidebar.markdown("---")
    
    # 全局板块选择
    global_sector = st.sidebar.selectbox(
        "选择板块",
        options=tracked_sectors['stock_code'].tolist(),
        format_func=lambda x: f"{x} - {sector_name_map.get(x, '未知')}",
        key="global_sector"
    )
    
    # 添加到常用板块按钮
    if global_sector not in st.session_state.favorite_sectors:
        if st.sidebar.button("⭐ 添加到常用板块", key="add_favorite"):
            st.session_state.favorite_sectors.append(global_sector)
            st.rerun()
    
    # 创建除了大盘监测图以外的所有图表名称列表
    sector_chart_names = [k for k in CHART_CONFIGS.keys() if k != '大盘监测图']
    
    # 全局应用状态
    if "global_applied" not in st.session_state:
        st.session_state.global_applied = False
    
    # 是否应用到所有图表
    if st.sidebar.button("📊 应用到所有图表", type="primary", use_container_width=True):
        # 设置所有图表的板块选择为全局选择的板块
        for chart_name in sector_chart_names:
            sector_key = f"sectors_{chart_name}"
            st.session_state[sector_key] = [global_sector]
        
        # 记录全局设置状态
        st.session_state.global_applied = True
        st.session_state.last_global_sector = global_sector
        
        # 显示成功消息
        st.sidebar.success(f"✅ 已将所有图表设置为: {global_sector} - {sector_name_map.get(global_sector, '未知')}")
        
        # 刷新页面以应用更改
        st.rerun()
    
    # 如果有全局应用记录，显示状态
    if st.session_state.global_applied and st.session_state.last_global_sector:
        last_sector = st.session_state.last_global_sector
        if last_sector in sector_name_map:
            st.sidebar.info(f"ℹ️ 上次全局应用: {last_sector} - {sector_name_map.get(last_sector, '未知')}")
    
    # 添加信息提示
    st.sidebar.info("👆 全局设置不会影响各图表的独立板块选择功能")
    
    # 添加分隔线
    st.sidebar.markdown("---")
    
    # 创建选项卡以区分板块分析和大盘监测
    tab_sector, tab_market = st.tabs(["板块分析", "大盘监测"])
    
    with tab_sector:
        # 显示分析数据的图表
        st.markdown("## 板块数据分析")
        
        # 创建图表布局
        st.markdown("### 数据图表")
        
        # 创建除了大盘监测图以外的选项卡
        sector_chart_configs = {k: v for k, v in CHART_CONFIGS.items() if k != '大盘监测图'}
        tabs = st.tabs([config_name for config_name in sector_chart_configs.keys()])
        
        # 遍历所有图表配置
        for i, (chart_name, config) in enumerate(sector_chart_configs.items()):
            with tabs[i]:
                # 创建图表设置区域
                col1, col2 = st.columns([3, 1])
                
                with col2:
                    st.markdown("#### 图表设置")
                    
                    # 添加全局板块选择提示
                    if st.session_state.global_applied:
                        st.info("ℹ️ 提示：可以使用侧边栏的全局板块选择功能快速设置所有图表")
                    
                    # 添加板块选择控件 - 现在每个图表单独选择
                    sector_key = f"sectors_{chart_name}"
                    if sector_key not in st.session_state:
                        # 默认选择第一个板块
                        st.session_state[sector_key] = [tracked_sectors['stock_code'].iloc[0]] if not tracked_sectors.empty else []
                    
                    # 多选板块
                    selected_sectors = st.multiselect(
                        "选择板块",
                        options=tracked_sectors['stock_code'].tolist(),
                        default=st.session_state[sector_key],
                        format_func=lambda x: f"{x} - {sector_name_map.get(x, '未知')}",
                        key=sector_key
                    )
                    
                    # 确保至少选择一个板块
                    if not selected_sectors:
                        st.warning("请至少选择一个板块")
                        if not tracked_sectors.empty:
                            selected_sectors = [tracked_sectors['stock_code'].iloc[0]]
                            st.session_state[sector_key] = selected_sectors
                    
                    # 使用session_state来存储字段选择，确保页面刷新时不会丢失
                    field_key = f"fields_{chart_name}"
                    if field_key not in st.session_state:
                        st.session_state[field_key] = config['default_fields']
                    
                    # 字段选择
                    selected_fields = st.multiselect(
                        "选择指标",
                        options=config['fields'],
                        default=st.session_state[field_key],
                        key=field_key
                    )
                    
                    # 当用户清除所有选择时，显示警告并使用默认值
                    if not selected_fields:
                        st.warning("请至少选择一个指标")
                        selected_fields = [config['default_fields'][0]]  # 使用第一个默认值
                        # 更新session_state
                        st.session_state[field_key] = selected_fields
                    
                    # 每个图表单独的日期范围选择
                    date_range_key = f"date_range_{chart_name}"
                    if date_range_key not in st.session_state:
                        st.session_state[date_range_key] = 10  # 默认10天
                    
                    date_range = st.selectbox(
                        "日期范围",
                        options=[5, 10, 30, 60],
                        index=1,  # 默认选择10天
                        format_func=lambda x: f"最近{x}天",
                        key=date_range_key
                    )
                    
                    # 每个图表单独的图表样式选择
                    style_key = f"chart_style_{chart_name}"
                    if style_key not in st.session_state:
                        st.session_state[style_key] = "bar"  # 默认柱状图
                    
                    chart_style = st.radio(
                        "图表样式",
                        ["line", "bar"],
                        index=1,  # 默认选择柱状图
                        format_func=lambda x: "折线图" if x == "line" else "柱状图",
                        key=style_key
                    )
                    
                    # 是否启用板块对比模式
                    if len(selected_sectors) > 1:
                        # 添加分隔线和对比模式标题
                        st.markdown("---")
                        st.markdown("#### 📊 板块对比模式")
                        
                        comparison_key = f"comparison_mode_{chart_name}"
                        if comparison_key not in st.session_state:
                            st.session_state[comparison_key] = True
                        
                        # 选择对比模式的布局    
                        col_mode1, col_mode2 = st.columns(2)
                        
                        # 使用按钮切换对比模式
                        with col_mode1:
                            if st.button("✅ 启用对比模式", 
                                        key=f"enable_{chart_name}", 
                                        use_container_width=True,
                                        disabled=st.session_state[comparison_key],
                                        type="primary" if st.session_state[comparison_key] else "secondary"):
                                st.session_state[comparison_key] = True
                                st.rerun()
                                
                        with col_mode2:
                            if st.button("❌ 禁用对比模式", 
                                        key=f"disable_{chart_name}", 
                                        use_container_width=True,
                                        disabled=not st.session_state[comparison_key],
                                        type="primary" if not st.session_state[comparison_key] else "secondary"):
                                st.session_state[comparison_key] = False
                                st.rerun()
                        
                        # 获取当前对比模式状态
                        comparison_mode = st.session_state[comparison_key]
                        
                        # 添加对比模式说明
                        if comparison_mode:
                            st.success("✓ 对比模式已启用：在同一图表中比较不同板块的相同指标")
                        else:
                            st.info("✗ 对比模式已禁用：为每个板块单独创建图表")
                    else:
                        comparison_mode = False
                        if len(selected_sectors) == 1:
                            st.markdown("---")
                            st.info("💡 选择多个板块可以启用对比模式")
                
                with col1:
                    if len(selected_sectors) > 0:
                        # 检查是否启用板块对比模式
                        if comparison_mode and len(selected_sectors) > 1 and len(selected_fields) > 0:
                            # 获取多个板块数据
                            sectors_data = get_multiple_sectors_data(selected_sectors, date_range)
                            
                            # 为每个选择的指标创建对比图表
                            for field in selected_fields:
                                # 创建板块比较图表
                                st.subheader(f"{field} - 板块对比")
                                fig = create_multi_sector_chart(
                                    chart_name,
                                    sectors_data,
                                    sector_name_map,
                                    field,
                                    chart_style
                                )
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info(f"无法创建 {field} 的板块对比图表，可能是数据不足")
                        else:
                            # 单板块模式或非对比模式，为每个板块单独创建图表
                            for sector_code in selected_sectors:
                                sector_name = sector_name_map.get(sector_code, "未知板块")
                                
                                # 获取当前图表的历史数据
                                chart_data = get_merged_historical_data(sector_code, date_range)
                                
                                if chart_data.empty:
                                    st.warning(f"未找到板块 {sector_code} - {sector_name} 的历史数据")
                                    continue
                                
                                # 创建图表标题
                                if len(selected_sectors) > 1:
                                    st.subheader(f"{sector_code} - {sector_name}")
                                
                                # 创建图表
                                fig = create_chart(
                                    f"{chart_name} - {sector_code} {sector_name}", 
                                    chart_data, 
                                    selected_fields, 
                                    chart_style
                                )
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info(f"无法创建图表，可能是数据不足或选择的字段在数据中不存在")
                    else:
                        st.info("请在右侧选择至少一个板块")
        
        # 板块分析页面底部放置调试信息，默认收起
        st.markdown("---")
        with st.expander("调试信息", expanded=False):
            col_debug1, col_debug2 = st.columns(2)
            
            with col_debug1:
                # 显示当前选择的板块
                if 'selected_sectors' in locals() and selected_sectors:
                    st.success(f"已选择的板块: {', '.join([f'{code} - {sector_name_map.get(code, '未知')}' for code in selected_sectors])}")
                
                # 显示调试信息
                if 'debug_info' in st.session_state:
                    st.info(st.session_state['debug_info'])
            
            with col_debug2:
                # 显示SQL查询
                if 'debug_sql' in st.session_state:
                    st.subheader("SQL查询")
                    st.code(st.session_state['debug_sql'], language="sql")
    
    with tab_market:
        # 获取大盘指数列表
        market_indices = get_market_indices()
        if market_indices.empty:
            st.warning("没有找到大盘指数数据。")
            return
        
        # 显示大盘监测图
        st.markdown("## 大盘监测")
        
        # 创建图表设置区域
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.markdown("#### 图表设置")
            
            # 选择大盘指数
            selected_index = st.selectbox(
                "选择大盘指数",
                options=market_indices['index_code'].tolist(),
                format_func=lambda x: f"{x} - {market_indices[market_indices['index_code'] == x]['index_name'].iloc[0]}"
            )
            
            # 获取当前选择指数的信息
            selected_index_name = market_indices[market_indices['index_code'] == selected_index]['index_name'].iloc[0]
            
            # 获取大盘监测图配置
            market_config = CHART_CONFIGS['大盘监测图']
            
            # 使用session_state来存储字段选择
            field_key = "fields_market"
            if field_key not in st.session_state:
                st.session_state[field_key] = market_config['default_fields']
            
            # 字段选择
            selected_fields = st.multiselect(
                "选择指标",
                options=market_config['fields'],
                default=st.session_state[field_key],
                key=field_key
            )
            
            # 当用户清除所有选择时，显示警告并使用默认值
            if not selected_fields:
                st.warning("请至少选择一个指标")
                selected_fields = [market_config['default_fields'][0]]  # 使用第一个默认值
                # 更新session_state
                st.session_state[field_key] = selected_fields
            
            # 放置日期范围选择
            market_date_range = st.selectbox(
                "日期范围",
                options=[5, 10, 30, 60],
                index=1,
                format_func=lambda x: f"最近{x}天",
                key="market_date_range"
            )
            
            # 放置图表类型选择
            market_chart_style = st.radio(
                "图表样式",
                ["line", "bar"],
                index=0,  # 默认选择折线图
                format_func=lambda x: "折线图" if x == "line" else "柱状图",
                key="market_chart_style"
            )
        
        with col1:
            # 获取大盘历史数据
            market_data = get_market_historical_data(selected_index, market_date_range)
            
            if market_data.empty:
                st.warning(f"未找到大盘指数 {selected_index} - {selected_index_name} 的历史数据")
                return
            
            # 创建图表标题
            chart_title = f"{selected_index} - {selected_index_name}"
            
            # 创建图表
            fig = create_chart(
                chart_title, 
                market_data, 
                selected_fields, 
                market_chart_style
            )
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"无法创建图表，可能是数据不足或选择的字段在数据中不存在")
        
        # 页面底部放置调试信息，默认收起
        st.markdown("---")
        with st.expander("调试信息", expanded=False):
            col_debug1, col_debug2 = st.columns(2)
            
            with col_debug1:
                # 显示数据日期范围
                if not market_data.empty and '数据日期' in market_data.columns:
                    min_date = market_data['数据日期'].min()
                    max_date = market_data['数据日期'].max()
                    st.success(f"数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
                    st.info(f"共{len(market_data)}个数据点")
                
                # 显示调试信息
                if 'market_debug_info' in st.session_state:
                    st.info(st.session_state['market_debug_info'])
            
            with col_debug2:
                # 显示SQL查询
                if 'market_debug_sql' in st.session_state:
                    st.subheader("SQL查询")
                    st.code(st.session_state['market_debug_sql'], language="sql")

# 运行主应用
if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
