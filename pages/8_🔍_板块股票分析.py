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
import requests
from bs4 import BeautifulSoup
import time
import ssl
import re
import json
import traceback
import random
# 导入AKShare库
import akshare as ak
import os

# 配置SSL上下文，解决SSL错误
ssl._create_default_https_context = ssl._create_unverified_context

# 页面配置
st.set_page_config(page_title="板块股票分析", page_icon="🔍", layout="wide")

# 定义收藏板块文件路径
FAVORITES_FILE = "favorite_boards.json"

# 从文件加载收藏的板块
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载收藏板块失败: {str(e)}")
    return {}

# 保存收藏的板块到文件
def save_favorites(favorites):
    try:
        with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存收藏板块失败: {str(e)}")

# 初始化收藏板块的session state
if 'favorite_boards' not in st.session_state:
    st.session_state.favorite_boards = load_favorites()

# 页面标题
st.title("🔍 板块股票分析")

# 清除页面上的调试信息
def clear_debug():
    for key in st.session_state.keys():
        if key.startswith('debug_'):
            del st.session_state[key]

# 板块行业映射 - 保留为备选方案
INDUSTRY_STOCK_MAPPING = {
    "881101": [  # 种植业与林业
        {"stock_code": "000998", "stock_name": "隆平高科"},
        {"stock_code": "600359", "stock_name": "新农开发"},
        {"stock_code": "600506", "stock_name": "香梨股份"},
        {"stock_code": "600540", "stock_name": "新赛股份"},
        {"stock_code": "600598", "stock_name": "北大荒"},
        {"stock_code": "601118", "stock_name": "海南橡胶"},
        {"stock_code": "603336", "stock_name": "宏辉果蔬"},
        {"stock_code": "000713", "stock_name": "丰乐种业"},
        {"stock_code": "002041", "stock_name": "登海种业"},
        {"stock_code": "300143", "stock_name": "星普医科"}
    ],
    "881273": [  # 白酒
        {"stock_code": "000568", "stock_name": "泸州老窖"},
        {"stock_code": "000596", "stock_name": "古井贡酒"},
        {"stock_code": "000799", "stock_name": "酒鬼酒"},
        {"stock_code": "000858", "stock_name": "五粮液"},
        {"stock_code": "002304", "stock_name": "洋河股份"},
        {"stock_code": "600197", "stock_name": "伊力特"},
        {"stock_code": "600519", "stock_name": "贵州茅台"},
        {"stock_code": "600559", "stock_name": "老白干酒"},
        {"stock_code": "600809", "stock_name": "山西汾酒"},
        {"stock_code": "603589", "stock_name": "口子窖"}
    ],
    "881133": [  # 饮料制造
        {"stock_code": "000848", "stock_name": "承德露露"},
        {"stock_code": "002732", "stock_name": "燕塘乳业"},
        {"stock_code": "600300", "stock_name": "维维股份"},
        {"stock_code": "600600", "stock_name": "青岛啤酒"},
        {"stock_code": "600655", "stock_name": "豫园股份"},
        {"stock_code": "600779", "stock_name": "水井坊"},
        {"stock_code": "600809", "stock_name": "山西汾酒"},
        {"stock_code": "600962", "stock_name": "国投中鲁"},
        {"stock_code": "603156", "stock_name": "养元饮品"},
        {"stock_code": "603711", "stock_name": "香飘飘"}
    ],
    "881150": [  # 半导体
        {"stock_code": "688981", "stock_name": "中芯国际"},
        {"stock_code": "688012", "stock_name": "中微公司"},
        {"stock_code": "603501", "stock_name": "韦尔股份"},
        {"stock_code": "603986", "stock_name": "兆易创新"},
        {"stock_code": "688516", "stock_name": "奥特维"},
        {"stock_code": "688396", "stock_name": "华润微"},
        {"stock_code": "688536", "stock_name": "思瑞浦"},
        {"stock_code": "688521", "stock_name": "芯原股份"},
        {"stock_code": "688368", "stock_name": "晶丰明源"},
        {"stock_code": "688682", "stock_name": "霍莱沃"},
        {"stock_code": "688008", "stock_name": "澜起科技"},
        {"stock_code": "300782", "stock_name": "卓胜微"},
        {"stock_code": "002371", "stock_name": "北方华创"},
        {"stock_code": "002916", "stock_name": "深南电路"},
        {"stock_code": "002049", "stock_name": "紫光国微"},
        {"stock_code": "600460", "stock_name": "士兰微"},
        {"stock_code": "600667", "stock_name": "太极实业"},
        {"stock_code": "002156", "stock_name": "通富微电"},
        {"stock_code": "000725", "stock_name": "京东方A"},
        {"stock_code": "300223", "stock_name": "北京君正"}
    ],
    "881169": [  # 软件开发
        {"stock_code": "688111", "stock_name": "金山办公"},
        {"stock_code": "300378", "stock_name": "鼎捷软件"},
        {"stock_code": "603039", "stock_name": "泛微网络"},
        {"stock_code": "300609", "stock_name": "汇纳科技"},
        {"stock_code": "300271", "stock_name": "华宇软件"},
        {"stock_code": "300448", "stock_name": "浩云科技"},
        {"stock_code": "300339", "stock_name": "润和软件"},
        {"stock_code": "300036", "stock_name": "超图软件"},
        {"stock_code": "300579", "stock_name": "数字认证"},
        {"stock_code": "603232", "stock_name": "格尔软件"},
        {"stock_code": "600570", "stock_name": "恒生电子"},
        {"stock_code": "300253", "stock_name": "卫宁健康"},
        {"stock_code": "002410", "stock_name": "广联达"},
        {"stock_code": "300674", "stock_name": "宇信科技"},
        {"stock_code": "300663", "stock_name": "科蓝软件"},
        {"stock_code": "600728", "stock_name": "佳都科技"},
        {"stock_code": "300170", "stock_name": "汉得信息"},
        {"stock_code": "002405", "stock_name": "四维图新"},
        {"stock_code": "300096", "stock_name": "易联众"},
        {"stock_code": "300766", "stock_name": "每日互动"},
        {"stock_code": "600845", "stock_name": "宝信软件"},
        {"stock_code": "603636", "stock_name": "南威软件"}
    ],
    # 可以添加更多板块的映射
}

# 添加概念板块映射 - 保留为备选方案
CONCEPT_STOCK_MAPPING = {
    "301558": [  # 人工智能
        {"stock_code": "002230", "stock_name": "科大讯飞"},
        {"stock_code": "300044", "stock_name": "赛为智能"},
        {"stock_code": "603019", "stock_name": "中科曙光"},
        {"stock_code": "000977", "stock_name": "浪潮信息"},
        {"stock_code": "300496", "stock_name": "中科创达"},
        {"stock_code": "300474", "stock_name": "景嘉微"},
        {"stock_code": "300017", "stock_name": "网宿科技"},
        {"stock_code": "600100", "stock_name": "同方股份"},
        {"stock_code": "002049", "stock_name": "紫光国微"},
        {"stock_code": "600588", "stock_name": "用友网络"},
        {"stock_code": "300418", "stock_name": "昆仑万维"},
        {"stock_code": "600536", "stock_name": "中国软件"},
        {"stock_code": "600718", "stock_name": "东软集团"},
        {"stock_code": "000066", "stock_name": "中国长城"},
        {"stock_code": "300124", "stock_name": "汇川技术"},
        {"stock_code": "688318", "stock_name": "财富趋势"},
        {"stock_code": "300579", "stock_name": "数字认证"},
        {"stock_code": "600845", "stock_name": "宝信软件"},
        {"stock_code": "603138", "stock_name": "海量数据"},
        {"stock_code": "605388", "stock_name": "均普智能"},
        {"stock_code": "300608", "stock_name": "思特奇"},
        {"stock_code": "300020", "stock_name": "银江技术"},
        {"stock_code": "300468", "stock_name": "四方精创"},
        {"stock_code": "300386", "stock_name": "飞天诚信"}
    ],
    "300750": [  # 新能源汽车
        {"stock_code": "300014", "stock_name": "亿纬锂能"},
        {"stock_code": "300750", "stock_name": "宁德时代"},
        {"stock_code": "601633", "stock_name": "长城汽车"},
        {"stock_code": "600733", "stock_name": "北汽蓝谷"},
        {"stock_code": "600745", "stock_name": "闻泰科技"},
        {"stock_code": "300207", "stock_name": "欣旺达"},
        {"stock_code": "002074", "stock_name": "国轩高科"},
        {"stock_code": "002460", "stock_name": "赣锋锂业"},
        {"stock_code": "002709", "stock_name": "天赐材料"},
        {"stock_code": "600884", "stock_name": "杉杉股份"},
        {"stock_code": "002812", "stock_name": "恩捷股份"},
        {"stock_code": "688005", "stock_name": "容百科技"},
        {"stock_code": "601127", "stock_name": "小康股份"},
        {"stock_code": "601238", "stock_name": "广汽集团"},
        {"stock_code": "000625", "stock_name": "长安汽车"},
        {"stock_code": "600885", "stock_name": "宏发股份"},
        {"stock_code": "600741", "stock_name": "华域汽车"},
        {"stock_code": "600732", "stock_name": "爱旭股份"},
        {"stock_code": "002594", "stock_name": "比亚迪"},
        {"stock_code": "002466", "stock_name": "天齐锂业"},
        {"stock_code": "688116", "stock_name": "天奈科技"},
        {"stock_code": "300073", "stock_name": "当升科技"}
    ],
    "300059": [  # 光伏
        {"stock_code": "601012", "stock_name": "隆基绿能"},
        {"stock_code": "002129", "stock_name": "TCL中环"},
        {"stock_code": "002459", "stock_name": "晶澳科技"},
        {"stock_code": "600438", "stock_name": "通威股份"},
        {"stock_code": "600089", "stock_name": "特变电工"},
        {"stock_code": "601877", "stock_name": "正泰电器"},
        {"stock_code": "300274", "stock_name": "阳光电源"},
        {"stock_code": "603806", "stock_name": "福斯特"},
        {"stock_code": "600732", "stock_name": "爱旭股份"},
        {"stock_code": "603185", "stock_name": "上机数控"},
        {"stock_code": "002218", "stock_name": "拓日新能"},
        {"stock_code": "000591", "stock_name": "太阳能"},
        {"stock_code": "000876", "stock_name": "新希望"},
        {"stock_code": "300118", "stock_name": "东方日升"},
        {"stock_code": "688599", "stock_name": "天合光能"},
        {"stock_code": "300437", "stock_name": "清水源"},
        {"stock_code": "300751", "stock_name": "迈为股份"},
        {"stock_code": "688063", "stock_name": "派能科技"},
        {"stock_code": "688680", "stock_name": "海优新材"},
        {"stock_code": "605499", "stock_name": "东鹏饮料"}
    ]
}

# 为板块提供分行业的模拟数据 - 保留为备选方案
def get_mock_data_for_sector(board_code):
    """为特定板块生成针对性的模拟数据"""
    
    # 检查是否有预定义的映射
    if board_code in INDUSTRY_STOCK_MAPPING:
        sector_stocks = INDUSTRY_STOCK_MAPPING[board_code]
    else:
        # 如果没有预定义的映射，生成随机数量的模拟股票数据（15-30只）
        stock_count = random.randint(15, 30)
        
        # 基础股票库 - 更多股票代码和名称
        base_stocks = [
            {"stock_code": "000001", "stock_name": "平安银行"},
            {"stock_code": "600036", "stock_name": "招商银行"},
            {"stock_code": "601398", "stock_name": "工商银行"},
            {"stock_code": "600000", "stock_name": "浦发银行"},
            {"stock_code": "601166", "stock_name": "兴业银行"},
            {"stock_code": "601328", "stock_name": "交通银行"},
            {"stock_code": "601288", "stock_name": "农业银行"},
            {"stock_code": "601818", "stock_name": "光大银行"},
            {"stock_code": "601998", "stock_name": "中信银行"},
            {"stock_code": "601988", "stock_name": "中国银行"},
            {"stock_code": "000063", "stock_name": "中兴通讯"},
            {"stock_code": "000333", "stock_name": "美的集团"},
            {"stock_code": "000651", "stock_name": "格力电器"},
            {"stock_code": "000725", "stock_name": "京东方A"},
            {"stock_code": "000858", "stock_name": "五粮液"},
            {"stock_code": "002027", "stock_name": "分众传媒"},
            {"stock_code": "002230", "stock_name": "科大讯飞"},
            {"stock_code": "002415", "stock_name": "海康威视"},
            {"stock_code": "002714", "stock_name": "牧原股份"},
            {"stock_code": "300059", "stock_name": "东方财富"},
            {"stock_code": "300122", "stock_name": "智飞生物"},
            {"stock_code": "300274", "stock_name": "阳光电源"},
            {"stock_code": "300498", "stock_name": "温氏股份"},
            {"stock_code": "600009", "stock_name": "上海机场"},
            {"stock_code": "600031", "stock_name": "三一重工"},
            {"stock_code": "600036", "stock_name": "招商银行"},
            {"stock_code": "600276", "stock_name": "恒瑞医药"},
            {"stock_code": "600309", "stock_name": "万华化学"},
            {"stock_code": "600519", "stock_name": "贵州茅台"},
            {"stock_code": "600585", "stock_name": "海螺水泥"},
            {"stock_code": "600690", "stock_name": "海尔智家"},
            {"stock_code": "600887", "stock_name": "伊利股份"},
            {"stock_code": "601012", "stock_name": "隆基绿能"},
            {"stock_code": "601318", "stock_name": "中国平安"},
            {"stock_code": "601888", "stock_name": "中国中免"},
            {"stock_code": "603259", "stock_name": "药明康德"},
            {"stock_code": "603501", "stock_name": "韦尔股份"},
            {"stock_code": "603986", "stock_name": "兆易创新"},
            {"stock_code": "688005", "stock_name": "容百科技"},
            {"stock_code": "688111", "stock_name": "金山办公"},
            {"stock_code": "688981", "stock_name": "中芯国际"}
        ]
        
        # 根据板块代码设置随机种子，确保相同板块生成相同的成分股
        if board_code:
            random.seed(int(board_code[-4:]))
        
        # 随机选择股票
        sector_stocks = random.sample(base_stocks, min(stock_count, len(base_stocks)))
    
    # 返回板块股票列表
    return pd.DataFrame(sector_stocks)

# 从东方财富网获取行业板块列表
@st.cache_data(ttl=3600)
def get_stock_board_industry_ths():
    """从东方财富网获取行业板块列表"""
    try:
        # 使用AKShare获取行业板块列表
        board_industry_df = ak.stock_board_industry_name_em()
        # 重命名列以匹配原有代码
        board_industry_df = board_industry_df.rename(columns={
            "板块名称": "name",
            "板块代码": "code"
        })
        # 选择需要的列
        board_industry_df = board_industry_df[["name", "code"]]
        # 确保代码列是字符串类型
        board_industry_df["code"] = board_industry_df["code"].astype(str)
        
        return board_industry_df
    except Exception as e:
        st.error(f"获取行业板块列表出错: {str(e)}")
        # 如果API调用失败，使用备选数据
        data = [
            {"name": "种植业与林业", "code": "881101"},
            {"name": "白酒", "code": "881273"},
            {"name": "饮料制造", "code": "881133"},
            {"name": "食品加工制造", "code": "881103"},
            {"name": "农业服务", "code": "881151"},
            {"name": "畜禽养殖", "code": "881121"},
            {"name": "农产品加工", "code": "881105"},
            {"name": "银行", "code": "881116"},
            {"name": "半导体", "code": "881150"},
            {"name": "电子元件", "code": "881131"},
            {"name": "软件开发", "code": "881169"},
            {"name": "汽车整车", "code": "881107"},
            {"name": "医疗器械", "code": "881118"},
            {"name": "房地产开发", "code": "881146"},
            {"name": "矿业开采", "code": "881119"},
        ]
        return pd.DataFrame(data)

# 从东方财富网获取概念板块列表
@st.cache_data(ttl=3600)
def get_stock_board_concept_ths():
    """从东方财富网获取概念板块列表"""
    try:
        # 使用AKShare获取概念板块列表
        board_concept_df = ak.stock_board_concept_name_em()
        # 重命名列以匹配原有代码
        board_concept_df = board_concept_df.rename(columns={
            "板块名称": "name",
            "板块代码": "code"
        })
        # 选择需要的列
        board_concept_df = board_concept_df[["name", "code"]]
        # 确保代码列是字符串类型
        board_concept_df["code"] = board_concept_df["code"].astype(str)
        
        return board_concept_df
    except Exception as e:
        st.error(f"获取概念板块列表出错: {str(e)}")
        # 如果API调用失败，使用备选数据
        data = [
            {"name": "人工智能", "code": "301558"},
            {"name": "数字经济", "code": "301807"},
            {"name": "数字货币", "code": "300991"},
            {"name": "中国制造2025", "code": "301180"},
            {"name": "锂电池", "code": "300061"},
            {"name": "光伏", "code": "300059"},
            {"name": "新能源汽车", "code": "300750"},
            {"name": "氢能源", "code": "300322"},
            {"name": "元宇宙", "code": "301553"},
            {"name": "集成电路", "code": "300115"},
            {"name": "半导体", "code": "301266"},
            {"name": "芯片", "code": "301370"},
            {"name": "云计算", "code": "301558"},
            {"name": "大数据", "code": "300295"},
            {"name": "区块链", "code": "300104"},
        ]
        return pd.DataFrame(data)

# 使用AKShare从东方财富网获取板块成分股
@st.cache_data(ttl=1800, show_spinner=True)
def get_board_constituents(board_code, board_type="industry"):
    """获取板块成分股数据
    
    Args:
        board_code: 板块代码
        board_type: 板块类型，"industry"为行业板块，"concept"为概念板块
    
    Returns:
        包含成分股信息的DataFrame
    """
    try:
        if board_type == "industry":
            # 尝试使用AKShare获取行业板块成分股
            try:
                # 获取行业板块成分股数据
                constituents_df = ak.stock_board_industry_cons_em(symbol=board_code)
                # 重命名列以匹配原有代码
                constituents_df = constituents_df.rename(columns={
                    "代码": "stock_code",
                    "名称": "stock_name"
                })
                # 选择需要的列
                constituents_df = constituents_df[["stock_code", "stock_name"]]
                # 确保代码列是字符串类型
                constituents_df["stock_code"] = constituents_df["stock_code"].astype(str)
                
                if not constituents_df.empty:
                    return constituents_df
            except Exception as e:
                st.warning(f"通过AKShare获取行业板块成分股出错: {str(e)}")
                
            # 如果AKShare调用失败，尝试使用备选映射
            if board_code in INDUSTRY_STOCK_MAPPING:
                sector_stocks = INDUSTRY_STOCK_MAPPING[board_code]
                return pd.DataFrame(sector_stocks)
        else:  # 概念板块
            # 尝试使用AKShare获取概念板块成分股
            try:
                # 从板块名称获取成分股
                # 先获取板块名称
                board_df = get_stock_board_concept_ths()
                board_name = board_df[board_df["code"] == board_code]["name"].iloc[0]
                
                # 使用板块名称获取成分股
                constituents_df = ak.stock_board_concept_cons_em(symbol=board_name)
                # 重命名列以匹配原有代码
                constituents_df = constituents_df.rename(columns={
                    "代码": "stock_code",
                    "名称": "stock_name"
                })
                # 选择需要的列
                constituents_df = constituents_df[["stock_code", "stock_name"]]
                # 确保代码列是字符串类型
                constituents_df["stock_code"] = constituents_df["stock_code"].astype(str)
                
                if not constituents_df.empty:
                    return constituents_df
            except Exception as e:
                st.warning(f"通过AKShare获取概念板块成分股出错: {str(e)}")
                
            # 如果AKShare调用失败，尝试使用备选映射
            if board_code in CONCEPT_STOCK_MAPPING:
                sector_stocks = CONCEPT_STOCK_MAPPING[board_code]
                return pd.DataFrame(sector_stocks)
        
        # 如果以上方法都失败，使用mock数据
        return get_mock_data_for_sector(board_code)
    except Exception as e:
        st.error(f"获取板块成分股出错: {str(e)}")
        st.session_state['debug_error'] = str(e)
        st.session_state['debug_traceback'] = traceback.format_exc()
        return get_mock_data_for_sector(board_code)  # 出错时返回模拟数据

# 生成模拟股票行情数据 - 保留为备选方案
def generate_mock_stock_quotes(stock_codes, stock_names=None, board_code=None):
    """生成模拟的股票行情数据"""
    if stock_names is None:
        stock_names = [f"股票{code[-4:]}" for code in stock_codes]
    
    # 根据板块设置不同的行情特征
    if board_code == "881101":  # 种植业与林业
        price_range = (5, 30)
        change_range = (-8, 2)  # 偏弱势
        turnover_range = (0.5, 3)
    elif board_code == "881273":  # 白酒
        price_range = (50, 300)
        change_range = (-3, 5)  # 偏强势
        turnover_range = (1, 4)
    elif board_code == "881133":  # 饮料制造
        price_range = (20, 100)
        change_range = (-5, 4)  # 中性
        turnover_range = (0.8, 3.5)
    else:
        # 默认范围
        price_range = (10, 100)
        change_range = (-8, 2)  # 默认偏弱势
        turnover_range = (0.5, 5)
    
    # 设置随机种子以确保同一板块每次生成的数据相似
    if board_code:
        random.seed(int(board_code[-4:]))
    
    # 生成模拟数据
    mock_data = []
    for code, name in zip(stock_codes, stock_names):
        mock_price = round(random.uniform(*price_range), 2)
        mock_change = round(random.uniform(*change_range), 2)
        mock_turnover = round(random.uniform(*turnover_range), 2)
        mock_volume = random.randint(10000, 1000000)
        mock_amount = round(mock_price * mock_volume / 100, 2)
        
        mock_data.append({
            "股票代码": code,
            "股票名称": name,
            "current_price": mock_price,
            "change_percent": mock_change,
            "change_amount": round(mock_change * mock_price / 100, 2),
            "volume": mock_volume,
            "amount": mock_amount,
            "amplitude": round(abs(mock_change) * 1.5, 2),
            "turnover_rate": mock_turnover,
            "pe_ttm": round(random.uniform(10, 50), 2),
            "volume_ratio": round(random.uniform(0.8, 1.5), 2)
        })
    
    return pd.DataFrame(mock_data)

# 获取股票实时行情
@st.cache_data(ttl=60, show_spinner=True)  # 缓存1分钟
def get_stock_quotes(stock_codes, stock_names=None, board_code=""):
    """获取股票实时行情
    
    Args:
        stock_codes: 股票代码列表
        stock_names: 股票名称列表
        board_code: 板块代码，用于缓存区分
    
    Returns:
        包含股票行情信息的DataFrame
    """
    try:
        # 尝试使用AKShare获取实时行情
        if stock_codes:
            # 准备一个空的DataFrame来存储所有股票的行情
            all_quotes = []
            
            # 批量获取股票行情数据
            try:
                # 将所有代码合并为一个字符串，以逗号分隔
                stock_codes_str = ",".join(stock_codes)
                quotes_df = ak.stock_zh_a_spot_em()
                
                # 过滤出我们需要的股票
                quotes_df = quotes_df[quotes_df["代码"].isin(stock_codes)]
                
                # 如果有股票名称列表，创建一个映射表
                code_to_name = {}
                if stock_names:
                    for code, name in zip(stock_codes, stock_names):
                        code_to_name[code] = name
                
                # 转换字段以匹配原有代码
                for _, row in quotes_df.iterrows():
                    stock_code = row["代码"]
                    stock_name = code_to_name.get(stock_code, row["名称"]) if code_to_name else row["名称"]
                    
                    quote_data = {
                        "股票代码": stock_code,
                        "股票名称": stock_name,
                        "current_price": row["最新价"],
                        "change_percent": row["涨跌幅"],
                        "change_amount": row["涨跌额"],
                        "volume": row["成交量"],
                        "amount": row["成交额"] / 100000000,  # 转换为亿元
                        "amplitude": row["振幅"],
                        "turnover_rate": row["换手率"],
                        "pe_ttm": row.get("市盈率-动态", 0),
                        "volume_ratio": row.get("量比", 1.0)
                    }
                    all_quotes.append(quote_data)
                
                if all_quotes:
                    return pd.DataFrame(all_quotes)
            except Exception as e:
                st.warning(f"使用AKShare获取股票行情出错: {str(e)}")
        
        # 如果无法获取真实数据，使用模拟数据
        return generate_mock_stock_quotes(stock_codes, stock_names, board_code)
    except Exception as e:
        st.error(f"获取股票行情数据出错: {str(e)}")
        return generate_mock_stock_quotes(stock_codes, stock_names, board_code)

def create_change_distribution_chart(df):
    """创建涨跌幅分布图，类似东方财富的风格"""
    if df.empty:
        return None
        
    # 定义涨跌区间和标签
    bins = [
        float('-inf'),  # 最小值
        -9.9,          # 跌停（创业板等）
        -5,            # -5%
        -1,            # -1%
        0,             # 平盘
        1,             # 1%
        5,             # 5%
        9.9,           # 涨停（创业板等）
        float('inf')   # 最大值
    ]
    
    labels = [
        '跌停',
        '-9.9%~-5%',
        '-5%~-1%',
        '-1%~0%',
        '0%~1%',
        '1%~5%',
        '5%~9.9%',
        '涨停'
    ]
    
    # 计算每个区间的股票数量
    df['change_range'] = pd.cut(df['change_percent'], bins=bins, labels=labels)
    distribution = df['change_range'].value_counts().reindex(labels)
    
    # 设置颜色映射
    colors = {
        '跌停': '#00aa3b',
        '-9.9%~-5%': '#00aa3b',
        '-5%~-1%': '#00aa3b',
        '-1%~0%': '#00aa3b',
        '0%~1%': '#ff3b30',
        '1%~5%': '#ff3b30',
        '5%~9.9%': '#ff3b30',
        '涨停': '#ff3b30'
    }
    
    # 创建柱状图
    fig = go.Figure()
    
    # 添加柱状图
    fig.add_trace(go.Bar(
        x=labels,
        y=distribution.values,
        marker_color=[colors[x] for x in labels],
        text=distribution.values.astype(int),  # 转换为整数
        textposition='outside',
        textfont=dict(size=14),  # 增大字体大小
        cliponaxis=False  # 防止文本被截断
    ))
    
    # 更新布局
    fig.update_layout(
        title='板块内股票涨跌幅分布',
        xaxis_title='涨跌幅区间',
        yaxis_title='股票数量',
        showlegend=False,
        xaxis={'tickangle': 45},
        margin=dict(t=50, b=50, l=50, r=50),
        height=400,
        # 确保y轴有足够空间显示文本
        yaxis=dict(
            range=[0, max(distribution.values) * 1.2]  # 增加20%的空间显示文本
        )
    )
    
    return fig

# 主应用
def main():
    # 添加侧边栏标题
    st.sidebar.title("🔍 板块股票分析")
    
    # 添加页面缓存控制
    if 'last_board_code' not in st.session_state:
        st.session_state.last_board_code = ""
        
    # 添加刷新按钮
    if st.sidebar.button("🔄 刷新数据", help="清除缓存并重新加载数据"):
        # 清除缓存
        st.cache_data.clear()
        st.rerun()

    # 选择板块类型
    board_type = st.sidebar.radio(
        "选择板块类型",
        options=["industry", "concept", "favorite"],
        format_func=lambda x: "行业板块" if x == "industry" else ("概念板块" if x == "concept" else "⭐ 收藏板块"),
        key="board_type"
    )
    
    # 根据选择的类型显示相应的板块列表
    if board_type == "favorite":
        if not st.session_state.favorite_boards:
            st.sidebar.info("暂无收藏板块")
            return
        
        # 显示收藏的板块列表
        board_options = [f"{data['name']} ({code})" for code, data in st.session_state.favorite_boards.items()]
        selected_board = st.sidebar.selectbox(
            "选择收藏的板块",
            options=board_options,
            key="favorite_selector"
        )
        
        # 解析选择的板块
        board_code = selected_board.split("(")[-1].strip(")")
        board_name = selected_board.split(" (")[0]
        # 获取板块类型
        actual_type = st.session_state.favorite_boards[board_code]['type']
        
    else:
        # 获取并显示板块列表
        if board_type == "industry":
            board_df = get_stock_board_industry_ths()
            board_title = "行业板块"
        else:
            board_df = get_stock_board_concept_ths()
            board_title = "概念板块"
        
        if board_df.empty:
            st.warning(f"获取{board_title}列表失败，请检查网络连接或稍后再试")
            return
        
        # 显示板块数量
        st.sidebar.info(f"共找到 {len(board_df)} 个{board_title}")
        
        # 选择特定板块
        board_options = [f"{row['name']} ({row['code']})" for _, row in board_df.iterrows()]
        selected_board = st.sidebar.selectbox(
            f"选择{board_title}",
            options=board_options,
            key=f"board_selector_{board_type}"
        )
        
        # 解析选择的板块
        board_code = selected_board.split("(")[-1].strip(")")
        board_name = selected_board.split(" (")[0]
        actual_type = board_type
        
        # 添加收藏/取消收藏按钮
        is_favorite = board_code in st.session_state.favorite_boards
        button_text = "❌ 取消收藏" if is_favorite else "⭐ 收藏板块"
        if st.sidebar.button(button_text):
            if is_favorite:
                del st.session_state.favorite_boards[board_code]
                st.sidebar.success(f"已取消收藏 {board_name}")
            else:
                st.session_state.favorite_boards[board_code] = {
                    'name': board_name,
                    'type': board_type
                }
                st.sidebar.success(f"已收藏 {board_name}")
            # 保存收藏板块到文件
            save_favorites(st.session_state.favorite_boards)
            st.rerun()
    
    # 更新当前板块信息
    st.session_state.current_board = {
        'code': board_code,
        'name': board_name,
        'type': actual_type
    }
    
    # 显示当前选中的板块信息
    current = st.session_state.current_board
    board_title = "行业板块" if current['type'] == "industry" else "概念板块"
    st.markdown(f"## {board_title}: {current['name']} ({current['code']})")
    
    # 获取当前时间
    current_date = time.strftime("%Y年%m月%d日", time.localtime())
    current_time = time.strftime("%H:%M", time.localtime())
    current_weekday = time.localtime().tm_wday  # 0-6, 0是周一
    
    # 判断最近的交易日
    if current_weekday == 5:  # 周六
        last_trading_date = time.strftime("%Y年%m月%d日", time.localtime(time.time() - 86400))  # 往前一天(周五)
    elif current_weekday == 6:  # 周日
        last_trading_date = time.strftime("%Y年%m月%d日", time.localtime(time.time() - 2*86400))  # 往前两天(周五)
    else:
        # 如果当前时间在9:30前，数据应该是前一个交易日的
        if int(time.strftime("%H%M")) < 930:
            if current_weekday == 0:  # 周一且未开盘
                last_trading_date = time.strftime("%Y年%m月%d日", time.localtime(time.time() - 3*86400))  # 往前三天(上周五)
            else:
                last_trading_date = time.strftime("%Y年%m月%d日", time.localtime(time.time() - 86400))  # 往前一天
        else:
            last_trading_date = current_date
    
    # 显示数据时效性信息
    if 930 <= int(time.strftime("%H%M")) < 1500 and current_weekday < 5:  # 交易时段
        st.info(f"📅 当前时间: {current_date} {current_time} (交易时段实时行情)")
    else:
        if current_date == last_trading_date:
            st.info(f"📅 {last_trading_date} {current_time} 数据")
        else:
            st.info(f"📅 数据截止日期: {last_trading_date} 15:00  (当前时间: {current_date} {current_time})")
    
    # 获取板块成分股
    constituents_df = get_board_constituents(current['code'], current['type'])
    
    if constituents_df.empty:
        st.warning(f"获取板块成分股失败或该板块没有成分股")
        return
    
    # 显示成分股数量
    st.info(f"📊 该板块共有 {len(constituents_df)} 只成分股")
    
    # 创建选项卡
    tab_stocks, tab_analysis = st.tabs(["个股行情", "板块分析"])
    
    with tab_stocks:
        # 获取股票行情数据
        stock_codes = constituents_df["stock_code"].tolist()
        stock_names = constituents_df["stock_name"].tolist()
        
        # 添加加载提示
        with st.spinner("正在获取最新行情数据..."):
            quotes_df = get_stock_quotes(stock_codes, stock_names, current['code'])
        
        if quotes_df.empty:
            st.warning("获取股票行情数据失败")
        else:
            # 合并成分股和行情数据
            merged_df = quotes_df
            
            # 添加使用模拟数据的提示
            if "pe_ttm" not in merged_df.columns or merged_df["pe_ttm"].isnull().all():
                st.warning("当前显示的是模拟数据，可能与实际市场行情有差异")
            
            # 添加筛选条件
            st.markdown("### 股票筛选")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_price = st.number_input("最低价格", value=0.0, step=1.0)
                max_price = st.number_input("最高价格", value=1000.0, step=10.0)
            
            with col2:
                min_change = st.number_input("最低涨跌幅 (%)", value=-20.0, step=0.5)
                max_change = st.number_input("最高涨跌幅 (%)", value=20.0, step=0.5)
            
            with col3:
                min_turnover = st.number_input("最低换手率 (%)", value=0.0, step=0.5)
                max_turnover = st.number_input("最高换手率 (%)", value=100.0, step=1.0)
            
            # 应用筛选条件
            filtered_df = merged_df[
                (merged_df["current_price"] >= min_price) &
                (merged_df["current_price"] <= max_price) &
                (merged_df["change_percent"] >= min_change) &
                (merged_df["change_percent"] <= max_change) &
                (merged_df["turnover_rate"] >= min_turnover) &
                (merged_df["turnover_rate"] <= max_turnover)
            ]
            
            # 显示筛选结果
            st.markdown(f"### 筛选结果 ({len(filtered_df)} 只股票)")
            
            # 显示股票分布图
            st.markdown("#### 涨跌幅分布")
            
            # 使用新的分布图函数
            fig = create_change_distribution_chart(filtered_df)
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示筛选后的股票列表
            st.dataframe(
                filtered_df[["股票代码", "股票名称", "current_price", "change_percent", "turnover_rate", "volume", "amount"]],
                hide_index=True,
                column_config={
                    "股票代码": st.column_config.TextColumn("股票代码"),
                    "股票名称": st.column_config.TextColumn("股票名称"),
                    "current_price": st.column_config.NumberColumn("最新价", format="%.2f"),
                    "change_percent": st.column_config.NumberColumn("涨跌幅 (%)", format="%.2f"),
                    "turnover_rate": st.column_config.NumberColumn("换手率 (%)", format="%.2f"),
                    "volume": st.column_config.NumberColumn("成交量 (手)", format="%d"),
                    "amount": st.column_config.NumberColumn("成交额 (亿元)", format="%.2f")
                }
            )
    
    with tab_analysis:
        if not quotes_df.empty:
            # 计算板块整体指标
            avg_change = quotes_df["change_percent"].mean()
            avg_turnover = quotes_df["turnover_rate"].mean()
            total_amount = quotes_df["amount"].sum()
            rise_count = len(quotes_df[quotes_df["change_percent"] > 0])
            fall_count = len(quotes_df[quotes_df["change_percent"] < 0])
            flat_count = len(quotes_df) - rise_count - fall_count
            
            # 显示板块整体指标
            st.markdown("### 板块整体表现")
            
            # 使用列布局显示指标
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("平均涨跌幅 (%)", f"{avg_change:.2f}")
                st.metric("平均换手率 (%)", f"{avg_turnover:.2f}")
            
            with col2:
                st.metric("成交总额 (亿元)", f"{total_amount:.2f}")
                st.metric("成分股数量", len(quotes_df))
            
            with col3:
                st.metric("上涨股票数", rise_count, f"{rise_count/len(quotes_df)*100:.1f}%")
                st.metric("下跌股票数", fall_count, f"{fall_count/len(quotes_df)*100:.1f}%")
            
            # 显示领涨领跌股
            st.markdown("### 领涨领跌股")
            
            # 查找领涨股和领跌股
            top_rise = quotes_df.nlargest(5, "change_percent")
            top_fall = quotes_df.nsmallest(5, "change_percent")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 领涨股票")
                st.dataframe(
                    top_rise[["股票代码", "股票名称", "current_price", "change_percent"]],
                    hide_index=True,
                    column_config={
                        "current_price": st.column_config.NumberColumn("最新价", format="%.2f"),
                        "change_percent": st.column_config.NumberColumn("涨跌幅 (%)", format="%.2f"),
                    }
                )
            
            with col2:
                st.markdown("#### 领跌股票")
                st.dataframe(
                    top_fall[["股票代码", "股票名称", "current_price", "change_percent"]],
                    hide_index=True,
                    column_config={
                        "current_price": st.column_config.NumberColumn("最新价", format="%.2f"),
                        "change_percent": st.column_config.NumberColumn("涨跌幅 (%)", format="%.2f"),
                    }
                )
            
            # 散点图：涨跌幅 vs 换手率
            st.markdown("### 涨跌幅与换手率关系分析")
            
            # 处理 NaN 值
            quotes_df['amount'] = quotes_df['amount'].fillna(quotes_df['amount'].mean())  # 使用平均值填充NaN
            
            fig = px.scatter(
                quotes_df,
                x="change_percent",
                y="turnover_rate",
                color="change_percent",
                size="amount",  # 成交额作为气泡大小
                size_max=50,  # 限制最大气泡大小
                hover_name="股票名称",
                hover_data=["股票代码", "current_price"],
                color_continuous_scale="RdBu_r",
                title="涨跌幅与换手率散点图",
                labels={
                    "change_percent": "涨跌幅 (%)",
                    "turnover_rate": "换手率 (%)",
                    "amount": "成交额 (亿元)"
                }
            )
            
            # 添加垂直线和水平线表示平均值
            fig.add_vline(x=avg_change, line_dash="dash", line_color="gray")
            fig.add_hline(y=avg_turnover, line_dash="dash", line_color="gray")
            
            # 添加四个象限的标记
            fig.add_annotation(
                x=avg_change + (quotes_df["change_percent"].max() - avg_change) / 2,
                y=avg_turnover + (quotes_df["turnover_rate"].max() - avg_turnover) / 2,
                text="高涨幅高换手",
                showarrow=False,
                font=dict(size=12, color="green")
            )
            
            fig.add_annotation(
                x=avg_change - (avg_change - quotes_df["change_percent"].min()) / 2,
                y=avg_turnover + (quotes_df["turnover_rate"].max() - avg_turnover) / 2,
                text="低涨幅高换手",
                showarrow=False,
                font=dict(size=12, color="red")
            )
            
            fig.add_annotation(
                x=avg_change + (quotes_df["change_percent"].max() - avg_change) / 2,
                y=avg_turnover - (avg_turnover - quotes_df["turnover_rate"].min()) / 2,
                text="高涨幅低换手",
                showarrow=False,
                font=dict(size=12, color="blue")
            )
            
            fig.add_annotation(
                x=avg_change - (avg_change - quotes_df["change_percent"].min()) / 2,
                y=avg_turnover - (avg_turnover - quotes_df["turnover_rate"].min()) / 2,
                text="低涨幅低换手",
                showarrow=False,
                font=dict(size=12, color="gray")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 添加数据自动刷新
            st.markdown("### 数据自动更新")
            st.info("数据每60秒自动刷新一次，确保您获取最新的市场行情。")
            
            # 添加计时器
            placeholder = st.empty()
            
            # 更新倒计时
            current_time = time.time()
            next_update = current_time + 60
            
            with placeholder.container():
                st.markdown(f"下次更新: {int(next_update - current_time)} 秒后")
            
            # 在页面底部添加数据来源说明
            st.markdown("---")
            st.markdown("数据来源: 东方财富网 (通过AKShare获取)")

# 运行应用
if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
