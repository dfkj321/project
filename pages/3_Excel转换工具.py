import streamlit as st
# 导入全局助手
try:
    from backend.helper import add_global_assistant
except ImportError:
    print("Error importing assistant helper")
import os
import tempfile
import glob
import sys
import pandas as pd
from pathlib import Path
try:
    import pythoncom
    import win32com.client as win32
    has_win32 = True
except ImportError:
    has_win32 = False

st.set_page_config(
    page_title="Excel格式转换工具",
    page_icon="📊",
    layout="wide"
)

def convert_xls_to_xlsx(folder_path, keep_original=False):
    """
    使用Excel应用程序将xls文件转换为xlsx格式
    参考excel-transform.py的转换方法
    """
    results = []
    
    # 查找所有xls文件
    xls_files = glob.glob(os.path.join(folder_path, "*.xls"))
    
    if not xls_files:
        return results, 0
    
    try:
        # 初始化COM环境
        pythoncom.CoInitialize()
        
        # 初始化Excel应用
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        
        for file_path in xls_files:
            try:
                if not os.path.exists(file_path):
                    continue
                    
                # 跳过临时文件
                file_name = os.path.basename(file_path)
                if file_name.startswith('~$'):
                    continue
                
                base_name = os.path.splitext(file_name)[0]
                xlsx_path = os.path.join(folder_path, f"{base_name}.xlsx")
                
                # 打开工作簿并以xlsx格式保存
                wb = excel.Workbooks.Open(os.path.abspath(file_path))
                wb.SaveAs(os.path.abspath(xlsx_path), FileFormat=51)  # 51表示xlsx格式
                wb.Close(False)
                
                # 如果不保留原文件，则删除
                if not keep_original:
                    try:
                        os.remove(file_path)
                    except Exception as del_error:
                        st.warning(f"无法删除原文件 {file_name}: {str(del_error)}")
                
                results.append({
                    "file": file_name,
                    "status": "成功",
                    "new_path": xlsx_path
                })
                
            except Exception as e:
                results.append({
                    "file": file_name,
                    "status": "失败",
                    "error": str(e)
                })
        
        # 关闭Excel应用
        excel.Quit()
        
        # 释放COM资源
        pythoncom.CoUninitialize()
        
    except Exception as e:
        st.error(f"Excel应用程序初始化失败: {str(e)}")
        return results, len(xls_files)
    
    return results, len(xls_files)

def main():
    st.title("📊 Excel格式转换工具")
    
    st.markdown("""
    ### 将xls文件转换为xlsx格式
    
    此工具可以将旧版Excel文件(.xls)转换为新版Excel文件(.xlsx)格式。
    支持转换WPS格式的Excel文件，以及标准Microsoft Excel文件。
    
    使用方法：
    1. 输入包含Excel文件的文件夹路径
    2. 选择是否保留原始文件
    3. 点击"开始转换"按钮
    """)
    
    # 检查是否安装了必要的库
    if not has_win32:
        st.error("""
        **错误：未安装必要的库**
        
        此工具需要安装pywin32库才能正常工作。请使用以下命令安装：
        
        ```
        pip install pywin32
        ```
        
        安装后重新启动应用程序。
        """)
        st.stop()
    
    # 文件夹路径输入
    folder_path = st.text_input("输入要转换的文件夹路径（绝对路径）", "C:\\Users\\hucon\\Desktop\\wps")
    
    # 保留原文件选项
    keep_original = st.checkbox("保留原始文件", value=False)
    
    # 检查路径是否存在
    path_exists = False
    if folder_path:
        path_exists = os.path.exists(folder_path) and os.path.isdir(folder_path)
        if not path_exists:
            st.error("指定的文件夹路径不存在，请检查后重新输入")
    
    # 转换按钮
    if path_exists and st.button("开始转换"):
        with st.spinner("正在转换文件夹中的Excel文件..."):
            results, total_files = convert_xls_to_xlsx(folder_path, keep_original)
            
            if total_files > 0:
                success_count = sum(1 for r in results if r["status"] == "成功")
                fail_count = total_files - success_count
                
                st.success(f"转换完成！共处理 {total_files} 个文件，成功 {success_count} 个，失败 {fail_count} 个")
                
                # 显示转换结果
                if results:
                    result_df = pd.DataFrame(results)
                    st.dataframe(result_df)
            else:
                st.info("文件夹中没有发现 .xls 文件，无需转换")

if __name__ == "__main__":
    main() 

# 添加全局悬浮助手
try:
    add_global_assistant()
except Exception as e:
    print(f"Error adding global assistant: {e}")
