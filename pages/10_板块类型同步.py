import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import akshare as ak
import pandas as pd
from sqlalchemy import create_engine, text
import os
import time
import io

# 页面配置
st.set_page_config(page_title="板块类型同步", page_icon="🔄", layout="wide")

# 地区板块列表
REGION_BOARD_CODES = [
    "BK0159", "BK0153", "BK0145", "BK0154", "BK0155", "BK0166", "BK0157", "BK0171", 
    "BK0173", "BK0163", "BK0158", "BK0150", "BK0167", "BK0174", "BK0148", "BK0149", 
    "BK0161", "BK0162", "BK0176", "BK0170", "BK0156", "BK0152", "BK0160", "BK0151", 
    "BK0146", "BK0175", "BK0165", "BK0169", "BK0172", "BK0164", "BK0147"
]

# 风格板块列表
STYLE_BOARD_CODES = [
    "BK0500", "BK0821", "BK1005", "BK1059", "BK0536", "BK0568", "BK0638", "BK0743",
    "BK0499", "BK0612", "BK0999", "BK1000", "BK0611", "BK0571", "BK0742", "BK0804",
    "BK0718", "BK0610", "BK0868", "BK0520", "BK0636", "BK0685", "BK0511", "BK1053",
    "BK0498", "BK1139", "BK0596", "BK0803", "BK0535", "BK0867", "BK0600", "BK0528",
    "BK0705", "BK0823", "BK1112", "BK0707", "BK0567", "BK0817", "BK0701", "BK0552",
    "BK0816", "BK1001", "BK0505", "BK0879", "BK0570", "BK1051", "BK0815", "BK1050"
]

# 板块名称映射
BOARD_NAME_MAPPING = {
    # 地区板块
    "BK0159": "江苏板块", "BK0153": "广东板块", "BK0145": "上海板块",
    "BK0154": "广西板块", "BK0155": "河北板块", "BK0166": "天津板块",
    "BK0157": "湖北板块", "BK0171": "云南板块", "BK0173": "贵州板块",
    "BK0163": "青海板块", "BK0158": "湖南板块", "BK0150": "北京板块",
    "BK0167": "山西板块", "BK0174": "西藏板块", "BK0148": "吉林板块",
    "BK0149": "安徽板块", "BK0161": "辽宁板块", "BK0162": "宁夏板块",
    "BK0176": "海南板块", "BK0170": "重庆板块", "BK0156": "河南板块",
    "BK0152": "甘肃板块", "BK0160": "江西板块", "BK0151": "福建板块",
    "BK0146": "黑龙江", "BK0175": "内蒙古", "BK0165": "陕西板块",
    "BK0169": "四川板块", "BK0172": "浙江板块", "BK0164": "山东板块",
    "BK0147": "新疆板块",
    
    # 风格板块
    "BK0500": "HS300_", "BK0821": "MSCI中国", "BK1005": "专精特新",
    "BK1059": "百元股", "BK0536": "基金重仓", "BK0568": "深成500",
    "BK0638": "创业成份", "BK0743": "深证100R", "BK0499": "AH股",
    "BK0612": "上证180_", "BK0999": "茅指数", "BK1000": "宁组合",
    "BK0611": "上证50_", "BK0571": "预盈预增", "BK0742": "创业板综",
    "BK0804": "深股通", "BK0718": "证金持股", "BK0610": "央视50_",
    "BK0868": "GDR", "BK0520": "社保重仓", "BK0636": "B股",
    "BK0685": "举牌", "BK0511": "ST股", "BK1053": "低价股",
    "BK0498": "AB股", "BK1139": "中特估", "BK0596": "融资融券",
    "BK0803": "股权转让", "BK0535": "QFII重仓", "BK0867": "富时罗素",
    "BK0600": "参股新三板", "BK0528": "转债标的", "BK0705": "上证380",
    "BK0823": "养老金", "BK1112": "破净股", "BK0707": "沪股通",
    "BK0567": "股权激励", "BK0817": "昨日触板", "BK0701": "中证500",
    "BK0552": "机构重仓", "BK0816": "昨日连板", "BK1001": "内贸流通",
    "BK0505": "中字头", "BK0879": "标准普尔", "BK0570": "预亏预减",
    "BK1051": "昨日连板_含一字", "BK0815": "昨日涨停", "BK1050": "昨日涨停_含一字"
}

# 获取板块数据
def fetch_board_data(get_func, board_type):
    try:
        df = get_func()
        df["board_type"] = board_type
        df["bk_code"] = df["板块代码"].apply(lambda x: f"BK{x[-4:]}")
        return df[["bk_code", "板块名称", "board_type"]]
    except Exception as e:
        st.error(f"获取{board_type}板块数据失败: {str(e)}")
        return pd.DataFrame()

# 将DataFrame转换为Excel字节流
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='板块数据', index=False)
    output.seek(0)
    return output.getvalue()

# 从数据库获取现有数据
def get_existing_data():
    try:
        engine = create_engine(
            "mysql+pymysql://root:123456@localhost:3306/stock_analysis?charset=utf8mb4"
        )
        
        # 检查表是否存在
        with engine.connect() as conn:
            table_exists = conn.execute(
                text("SHOW TABLES LIKE 'bk_type_mapping'")
            ).fetchone() is not None
            
        if not table_exists:
            return None, "数据表不存在"
            
        # 读取现有数据
        df = pd.read_sql("SELECT * FROM bk_type_mapping", engine)
        return df, None
    except Exception as e:
        return None, str(e)

# 同步板块数据到数据库
def sync_boards_to_db():
    try:
        # 创建数据库连接引擎
        engine = create_engine(
            "mysql+pymysql://root:123456@localhost:3306/stock_analysis?charset=utf8mb4"
        )

        # 检查表是否存在
        with engine.connect() as conn:
            table_exists = conn.execute(
                text("SHOW TABLES LIKE 'bk_type_mapping'")
            ).fetchone() is not None

        # 获取各类型板块数据
        try:
            concept_df = fetch_board_data(ak.stock_board_concept_name_em, "概念")
            st.write("概念板块获取成功")
        except Exception as e:
            st.error(f"获取概念板块失败: {str(e)}")
            concept_df = pd.DataFrame()

        try:
            industry_df = fetch_board_data(ak.stock_board_industry_name_em, "行业")
            st.write("行业板块获取成功")
        except Exception as e:
            st.error(f"获取行业板块失败: {str(e)}")
            industry_df = pd.DataFrame()

        # 合并所有板块
        all_boards_df = pd.concat([concept_df, industry_df]).drop_duplicates(subset=['bk_code'])
        
        if len(all_boards_df) == 0:
            return False, "未能获取任何板块数据"
        
        # 获取合并前的板块计数和代码列表，用于调试
        found_region_codes = all_boards_df[all_boards_df['bk_code'].isin(REGION_BOARD_CODES)]['bk_code'].tolist()
        found_style_codes = all_boards_df[all_boards_df['bk_code'].isin(STYLE_BOARD_CODES)]['bk_code'].tolist()
        
        st.write(f"在API数据中找到地区板块数量: {len(found_region_codes)}")
        st.write(f"在API数据中找到风格板块数量: {len(found_style_codes)}")
        
        # 添加缺失的板块
        missing_boards = []
        
        # 检查缺失的地区板块
        missing_region_codes = [code for code in REGION_BOARD_CODES if code not in all_boards_df['bk_code'].values]
        if missing_region_codes:
            st.write(f"添加缺失的地区板块: {len(missing_region_codes)}")
            for code in missing_region_codes:
                board_name = BOARD_NAME_MAPPING.get(code, f"{code}地区板块")
                missing_boards.append({"bk_code": code, "板块名称": board_name, "board_type": "地区"})
        
        # 检查缺失的风格板块
        missing_style_codes = [code for code in STYLE_BOARD_CODES if code not in all_boards_df['bk_code'].values]
        if missing_style_codes:
            st.write(f"添加缺失的风格板块: {len(missing_style_codes)}")
            for code in missing_style_codes:
                board_name = BOARD_NAME_MAPPING.get(code, f"{code}风格板块")
                missing_boards.append({"bk_code": code, "板块名称": board_name, "board_type": "风格"})
        
        # 如果有缺失的板块，添加到数据框中
        if missing_boards:
            missing_df = pd.DataFrame(missing_boards)
            all_boards_df = pd.concat([all_boards_df, missing_df])
        
        # 将地区板块和风格板块的类型分别设置为"地区"和"风格"
        all_boards_df.loc[all_boards_df['bk_code'].isin(REGION_BOARD_CODES), 'board_type'] = "地区"
        all_boards_df.loc[all_boards_df['bk_code'].isin(STYLE_BOARD_CODES), 'board_type'] = "风格"
        
        # 调试输出
        region_count = len(all_boards_df[all_boards_df['board_type'] == "地区"])
        style_count = len(all_boards_df[all_boards_df['board_type'] == "风格"])
        st.write(f"设置为地区类型的板块数量: {region_count}")
        st.write(f"设置为风格类型的板块数量: {style_count}")
        
        # 确保所有特殊板块都在结果中
        missing_region_after = set(REGION_BOARD_CODES) - set(all_boards_df[all_boards_df['board_type'] == "地区"]['bk_code'])
        missing_style_after = set(STYLE_BOARD_CODES) - set(all_boards_df[all_boards_df['board_type'] == "风格"]['bk_code'])
        
        if missing_region_after:
            st.warning(f"警告：仍有{len(missing_region_after)}个地区板块未包含在结果中")
        if missing_style_after:
            st.warning(f"警告：仍有{len(missing_style_after)}个风格板块未包含在结果中")
        
        all_boards_df.columns = ["bk_code", "board_name", "board_type"]

        # 写入数据库前再次验证板块数量
        region_df = all_boards_df[all_boards_df['board_type'] == "地区"]
        style_df = all_boards_df[all_boards_df['board_type'] == "风格"]
        st.write(f"写入数据库前的地区板块数量: {len(region_df)}")
        st.write(f"写入数据库前的风格板块数量: {len(style_df)}")
        
        # 写入数据库
        if table_exists:
            # 如果表存在，先清空表
            with engine.connect() as conn:
                conn.execute(text("TRUNCATE TABLE bk_type_mapping"))
                conn.commit()
            # 然后插入新数据
            all_boards_df.to_sql("bk_type_mapping", engine, index=False, if_exists="append")
        else:
            # 如果表不存在，创建新表并插入数据
            all_boards_df.to_sql("bk_type_mapping", engine, index=False, if_exists="fail")
        
        return True, all_boards_df
    except Exception as e:
        return False, str(e)

# 主应用
def main():
    st.title("🔄 板块类型同步")
    
    # 显示现有数据
    st.markdown("### 当前数据库数据")
    existing_data, error = get_existing_data()
    
    if error:
        st.warning(f"获取现有数据失败: {error}")
    elif existing_data is not None:
        st.markdown(f"#### 现有数据统计")
        st.markdown(f"- 总板块数: {len(existing_data)}")
        st.markdown(f"- 概念板块: {len(existing_data[existing_data['board_type'] == '概念'])}")
        st.markdown(f"- 行业板块: {len(existing_data[existing_data['board_type'] == '行业'])}")
        st.markdown(f"- 地区板块: {len(existing_data[existing_data['board_type'] == '地区'])}")
        st.markdown(f"- 风格板块: {len(existing_data[existing_data['board_type'] == '风格'])}")
        
        st.markdown("#### 现有数据预览")
        st.dataframe(existing_data.head(10))
        
        # 下载现有数据按钮
        excel_data = convert_df_to_excel(existing_data)
        st.download_button(
            label="下载现有数据 (Excel)",
            data=excel_data,
            file_name='current_board_type_mapping.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    
    # 同步功能
    st.markdown("---")
    st.markdown("### 同步板块数据")
    if st.button("开始同步"):
        with st.spinner("正在同步板块数据..."):
            success, result = sync_boards_to_db()
            
            if success:
                st.success("✅ 同步成功！")
                st.markdown(f"#### 同步结果统计")
                st.markdown(f"- 总板块数: {len(result)}")
                st.markdown(f"- 概念板块: {len(result[result['board_type'] == '概念'])}")
                st.markdown(f"- 行业板块: {len(result[result['board_type'] == '行业'])}")
                st.markdown(f"- 地区板块: {len(result[result['board_type'] == '地区'])}")
                st.markdown(f"- 风格板块: {len(result[result['board_type'] == '风格'])}")
                
                # 显示数据预览
                st.markdown("#### 数据预览")
                
                if not result[result['board_type'] == '地区'].empty:
                    st.markdown("##### 地区板块:")
                    st.dataframe(result[result['board_type'] == '地区'].head(10))
                
                if not result[result['board_type'] == '风格'].empty:
                    st.markdown("##### 风格板块:")
                    st.dataframe(result[result['board_type'] == '风格'].head(10))
                
                st.markdown("##### 所有板块:")
                st.dataframe(result.head(10))
                
                # 下载数据按钮
                excel_data = convert_df_to_excel(result)
                st.download_button(
                    label="下载完整数据 (Excel)",
                    data=excel_data,
                    file_name='board_type_mapping.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
            else:
                st.error(f"❌ 同步失败: {result}")

    # 在页面底部添加数据来源说明
    st.markdown("---")
    st.markdown("数据来源: 东方财富网 (通过AKShare获取)")

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
