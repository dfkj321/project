import streamlit as st
from pathlib import Path
import os
import sys

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置页面配置
st.set_page_config(
    page_title="板块数据分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置页面样式
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .stSelectbox {
        margin-bottom: 1rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 显示系统标题和欢迎信息
st.title("📊 板块数据分析系统")

st.markdown("### 👋 欢迎使用板块数据分析系统")

st.markdown("本系统提供以下核心功能：")

st.markdown("""
- 📈 条件选板块 - 基于涨幅、资金流向、成交量等多维指标筛选板块
- 📌 重点板块跟踪 - 实时监控板块涨跌、资金流向、龙头股表现
- 🔍 板块股票分析 - 深入分析板块内个股表现，发现优质标的
- 📊 数据可视化 - 丰富的图表展示，支持多维度数据分析
  - 板块资金流向：主力资金、散户资金、净流入分析
  - 龙头股分析：板块内个股涨跌、成交量、换手率分析
  - 多维对比：支持板块间、个股间多指标对比
- 🔄 数据同步管理 
  - 自动同步：定时更新板块、个股最新数据
  - 数据校验：确保数据准确性和完整性
- 💾 数据导出 - 支持Excel格式导出，便于深入研究
- 🛠️ 辅助工具集
  - 板块管理：支持自定义板块分组和标记
  - 数据日期管理：灵富的数据管理和维护功能
""")

# 版本信息
with st.expander("版本信息", expanded=False):
    st.write("当前版本: 1.5.0")
    st.write("更新日志:")
    st.markdown("""
    - 新增全局板块选择功能
    - 新增常用板块收藏功能
    - 优化板块对比模式，支持多维度分析
    - 增加数据日期管理工具
    - 修复已知问题，提升系统稳定性
    """)

# 显示系统状态
with st.sidebar:
    st.markdown("### 系统状态")
    
    # 兼容从不同目录启动应用的情况
    current_dir_config = Path("config/.env")
    parent_dir_config = Path("../project/config/.env")
    script_dir_config = Path(__file__).parent / "config" / ".env"
    
    if current_dir_config.exists() or parent_dir_config.exists() or script_dir_config.exists():
        st.success("✅ 数据库配置已就绪")
    else:
        st.warning("⚠️ 未检测到数据库配置") 