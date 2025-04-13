import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import pandas as pd
import os
import re
import numpy as np
import glob
import sys
import mysql.connector
from datetime import datetime
# 导入数据库连接模块
try:
    from backend.db import db
except ImportError:
    print("Error importing database module")

st.set_page_config(
    page_title="数据导入工具",
    page_icon="📊",
    layout="wide"
)

# ------------------------
# 数据库连接信息 - 从backend.db模块获取
# ------------------------
db_config = {
    "host": db.host,
    "user": db.user,
    "password": db.password,
    "database": db.database,
    "port": int(db.port),
    "connect_timeout": db.connect_timeout,
    "charset": db.charset
}

# ------------------------
# 单位转换函数：将包含"万亿"、"亿"或"万"的字符串转换为统一单位（亿）
# ------------------------
def convert_to_yi(value):
    """
    将包含"万亿"、"亿"或"万"的字符串转换为统一单位（亿）
    - 例如： "1.80万亿" -> 1.80*10000 = 18000
    - "2.4亿"   -> 2.4
    - "150万"   -> 150/10000 = 0.015
    - 纯数字直接转换
    """
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
            if "万亿" in value:
                return float(value.replace("万亿", "")) * 10000
            elif "亿" in value:
                return float(value.replace("亿", ""))
            elif "万" in value:
                return float(value.replace("万", "")) / 10000
            else:
                return float(value)
        return float(value)
    except ValueError:
        return None

# ------------------------
# 需要转换单位的列（统一转换为"亿"）
# ------------------------
unit_conversion_columns = {
    "capital_flow": [
        '主力净流入', '集合竞价', '超大单流入', '超大单流出', '超大单净额',
        '大单流入', '大单流出', '大单净额', '中单流入', '中单流出', '中单净额',
        '小单流入', '小单流出', '小单净额'
    ],
    "market_trend": ['金额'],
    "sector_trend": ['成交量', '金额', '总市值', '流通市值', '平均股本'],
}

# ------------------------
# 表名与正确表头的映射
# 说明：预期表头中已包含"数据日期"。对于板块监测，预期表头中不再包含"涨跌家数"，而是拆分成"涨家数"和"跌家数"
# ------------------------
expected_columns = {
    "DDE分析": (
        "dde_analysis",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', 'DDX', 'DDY', 'DDZ',
         '5日DDX', '5日DDY', '10日DDX', '10日DDY', '连续', '5日内', '10日内',
         '特大买入%', '特大卖出%', '特大单净比%', '大单买入%', '大单卖出%', '大单净比%']
    ),
    "增仓分析": (
        "position_analysis",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', '今日增仓占比',
         '今日排名', '今日排名变化', '今日涨幅%', '3日增仓占比', '3日排名',
         '3日排名变化', '3日涨幅%', '5日增仓占比', '5日排名', '5日排名变化',
         '5日涨幅%', '10日增仓占比', '10日排名', '10日排名变化', '10日涨幅%']
    ),
    "大盘监测": (
        "market_trend",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', '涨跌',
         '金额', '最高', '最低', '开盘', '昨收']
    ),
    "板块监测": (
        "sector_trend",
        ['数据日期', '序', '名称', '涨幅%', '3日涨幅%', '涨速%', '领涨股',
         '涨家数', '跌家数', '涨跌比', '涨停家数', '换手%', '3日换手%',
         '成交量', '金额', '总市值', '流通市值', '平均收益', '平均股本', '市盈率']
    ),
    "资金流": (
        "capital_flow",
        ['数据日期', '序', '代码', '名称', '最新', '涨幅%', '主力净流入', '集合竞价',
         '超大单流入', '超大单流出', '超大单净额', '超大单净占比%', '大单流入', '大单流出',
         '大单净额', '大单净占比%', '中单流入', '中单流出', '中单净额', '中单净占比%',
         '小单流入', '小单流出', '小单净额', '小单净占比%']
    ),
}

def import_excel_files(directory, result_callback=None, test_mode=False):
    """
    将指定目录中的Excel文件导入到数据库
    
    参数:
    - directory: Excel文件所在的目录
    - result_callback: 回调函数，用于返回处理结果
    - test_mode: 测试模式，不实际写入数据库
    
    返回:
    - 处理结果的字典
    """
    results = []
    
    # 获取所有 Excel 文件（排除 ~$ 开头的临时文件）
    files = [f for f in os.listdir(directory) if (f.endswith(".xlsx") or f.endswith(".xls")) and not f.startswith("~$")]
    
    if not files:
        if result_callback:
            result_callback(f"⚠️ 目录 {directory} 中没有找到Excel文件")
        return [], 0
    
    try:
        # 连接数据库
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        processed_count = 0
        success_count = 0
        
        for file in files:
            file_path = os.path.join(directory, file)
            
            # ------------------------
            # 根据文件名关键词匹配目标数据库表和预期表头
            # ------------------------
            table_name = None
            expected_table_cols = None
            for keyword, (db_table, exp_cols) in expected_columns.items():
                if keyword in file:
                    table_name = db_table
                    expected_table_cols = exp_cols  # 保存预期表头
                    break
            if not table_name:
                message = f"⚠️ 未找到匹配的数据库表，跳过文件：{file}"
                if result_callback:
                    result_callback(message)
                results.append({
                    "file": file,
                    "status": "失败",
                    "error": "无法匹配数据库表"
                })
                continue
            
            try:
                message = f"📌 处理文件：{file}"
                if result_callback:
                    result_callback(message)
                
                # ------------------------
                # 从文件名中解析数据日期（假设文件名中包含 YYYY-MM-DD 格式的日期）
                # ------------------------
                match = re.search(r"(\d{4}-\d{2}-\d{2})", file)
                if not match:
                    message = f"⚠️ 无法解析文件日期，跳过文件：{file}"
                    if result_callback:
                        result_callback(message)
                    results.append({
                        "file": file,
                        "status": "失败",
                        "error": "无法解析文件日期"
                    })
                    continue
                data_date = match.group(1)
                
                # ------------------------
                # 读取 Excel 文件
                # ------------------------
                df = pd.read_excel(file_path, sheet_name=0)
                
                # ------------------------
                # 标准化列名：去除前后空格、替换多个空格，并填充空值
                # ------------------------
                df.columns = df.columns.astype(str).str.strip().str.replace(r"\s+", "", regex=True).fillna("")
                
                # ------------------------
                # 删除完全为空的列，避免多余空列
                # ------------------------
                df = df.dropna(axis=1, how="all")
                
                # ------------------------
                # 确保"数据日期"列存在：如果Excel中没有，则插入；如果已存在则覆盖
                # ------------------------
                if "数据日期" not in df.columns:
                    df.insert(0, "数据日期", data_date)
                else:
                    df["数据日期"] = data_date
                
                # ------------------------
                # 强制"代码"列为字符串，并补齐前导零（假设代码应为6位）
                # ------------------------
                if "代码" in df.columns:
                    df["代码"] = df["代码"].astype(str).str.strip()
                    df["代码"] = df["代码"].apply(lambda x: x.zfill(6) if x.isdigit() else x)
                
                # ------------------------
                # 删除"序"列（假设数据库"序"字段为自增主键，不参与插入）
                # ------------------------
                if "序" in df.columns:
                    df = df.drop(columns=["序"])
                    expected_table_cols = [col for col in expected_table_cols if col != "序"]
                
                # ------------------------
                # 针对板块监测表：拆分"涨跌家数"为"涨家数"和"跌家数"
                # ------------------------
                if table_name == "sector_trend" and "涨跌家数" in df.columns:
                    df[['涨家数', '跌家数']] = df['涨跌家数'].str.split('/', expand=True)
                    df['涨家数'] = pd.to_numeric(df['涨家数'].astype(str).str.strip(), errors='coerce')
                    df['跌家数'] = pd.to_numeric(df['跌家数'].astype(str).str.strip(), errors='coerce')
                    df.drop(columns=['涨跌家数'], inplace=True)
                
                # ------------------------
                # 数据单位转换：对于需要转换单位的字段，统一转换为"亿"
                # ------------------------
                if table_name in unit_conversion_columns:
                    for col in unit_conversion_columns[table_name]:
                        if col in df.columns:
                            df[col] = df[col].apply(lambda x: convert_to_yi(x) if pd.notnull(x) else None)
                
                # ------------------------
                # 替换 DataFrame 中的 NaN 为 None，防止 SQL 错误
                # ------------------------
                df = df.replace({np.nan: None})
                
                # ------------------------
                # 如果是板块监测，需要重新排序列以符合预期顺序
                # ------------------------
                if table_name == "sector_trend":
                    available_cols = [col for col in expected_table_cols if col in df.columns]
                    df = df[available_cols]
                else:
                    # 检查表头匹配情况
                    missing_cols = [col for col in expected_table_cols if col not in df.columns]
                    if missing_cols:
                        message = f"❌ 表头不完整，缺少字段：{missing_cols}，跳过文件：{file}"
                        if result_callback:
                            result_callback(message)
                        results.append({
                            "file": file,
                            "status": "失败",
                            "error": f"表头不完整，缺少：{missing_cols}"
                        })
                        continue
                
                # 测试模式不实际写入数据库
                if not test_mode:
                    # ------------------------
                    # 删除旧数据（相同数据日期）
                    # ------------------------
                    cursor.execute(f"DELETE FROM `{table_name}` WHERE `数据日期` = %s", (data_date,))
                    conn.commit()
                    message = f"🗑️ 已清除 {data_date} 的旧数据"
                    if result_callback:
                        result_callback(message)
                    
                    # ------------------------
                    # 构建 INSERT SQL 语句，自动为所有字段加反引号
                    # ------------------------
                    columns_str = ", ".join([f"`{col}`" for col in df.columns])
                    values_placeholder = ", ".join(["%s"] * len(df.columns))
                    insert_query = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_placeholder})"
                    
                    # ------------------------
                    # 批量插入数据
                    # ------------------------
                    cursor.executemany(insert_query, df.values.tolist())
                    conn.commit()
                
                message = f"✅ 成功导入：{file} -> {table_name}"
                if result_callback:
                    result_callback(message)
                
                success_count += 1
                results.append({
                    "file": file,
                    "status": "成功",
                    "table": table_name, 
                    "date": data_date,
                    "rows": len(df)
                })
                
            except Exception as e:
                message = f"❌ 解析 Excel 失败：{file}，错误：{e}"
                if result_callback:
                    result_callback(message)
                results.append({
                    "file": file,
                    "status": "失败",
                    "error": str(e)
                })
            
            processed_count += 1
            
        cursor.close()
        conn.close()
        
        message = f"🚀 所有数据导入完成！成功 {success_count}/{processed_count} 个文件"
        if result_callback:
            result_callback(message)
            
    except mysql.connector.Error as e:
        message = f"❌ 数据库连接错误：{e}"
        if result_callback:
            result_callback(message)
        results.append({
            "file": "数据库连接",
            "status": "失败",
            "error": str(e)
        })
    except Exception as e:
        message = f"❌ 意外错误：{e}"
        if result_callback:
            result_callback(message)
        results.append({
            "file": "系统错误",
            "status": "失败",
            "error": str(e)
        })
    
    return results, len(files)

def main():
    st.title("📊 数据导入工具")
    
    st.markdown("""
    ### 将Excel文件批量导入数据库
    
    此工具可将以下类型的Excel文件自动导入到数据库：
    - 资金流（含关键词"资金流"）
    - 增仓分析（含关键词"增仓分析"）
    - DDE分析（含关键词"DDE分析"）
    - 板块监测（含关键词"板块监测"）
    - 大盘监测（含关键词"大盘监测"）
    
    文件名中需要包含日期格式如：YYYY-MM-DD
    """)
    
    # 文件夹路径输入
    folder_path = st.text_input("输入要导入的Excel文件夹路径（绝对路径）", "C:\\Users\\hucon\\Desktop\\wps")
    
    # 测试模式，不实际写入数据库
    test_mode = st.checkbox("测试模式（不实际写入数据库）", value=False)
    
    # 检查路径是否存在
    path_exists = False
    if folder_path:
        path_exists = os.path.exists(folder_path) and os.path.isdir(folder_path)
        if not path_exists:
            st.error("指定的文件夹路径不存在，请检查后重新输入")
    
    # 创建输出区域
    output_area = st.empty()
    
    # 用于存储日志消息
    log_messages = []
    
    # 回调函数，用于更新界面
    def update_log(message):
        log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        output_area.text("\n".join(log_messages))
    
    # 导入按钮
    if path_exists and st.button("开始导入"):
        log_messages = []  # 清空之前的日志
        update_log(f"开始处理文件夹：{folder_path}")
        
        with st.spinner("正在导入数据..."):
            # 调用导入函数，并传入回调函数
            results, total_files = import_excel_files(folder_path, update_log, test_mode)
            
            if total_files > 0:
                success_count = sum(1 for r in results if r["status"] == "成功")
                fail_count = total_files - success_count
                
                if test_mode:
                    st.success(f"测试完成！共检查 {total_files} 个文件，可成功处理 {success_count} 个，失败 {fail_count} 个")
                else:
                    st.success(f"导入完成！共处理 {total_files} 个文件，成功 {success_count} 个，失败 {fail_count} 个")
                
                # 显示导入结果
                if results:
                    result_df = pd.DataFrame(results)
                    st.dataframe(result_df)
            else:
                st.info(f"文件夹 {folder_path} 中没有找到Excel文件")

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
