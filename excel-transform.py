import os
import win32com.client as win32

def convert_xls_to_xlsx(folder_path):
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    excel.Visible = False

    for filename in os.listdir(folder_path):
        if filename.endswith('.xls') and not filename.startswith('~$'):
            xls_path = os.path.join(folder_path, filename)
            xlsx_path = os.path.splitext(xls_path)[0] + '.xlsx'

            try:
                wb = excel.Workbooks.Open(xls_path)
                wb.SaveAs(xlsx_path, FileFormat=51)  # 51 表示 xlsx 格式
                wb.Close(False)
                os.remove(xls_path)
                print(f"✅ 已转换并删除：{filename}")
            except Exception as e:
                print(f"❌ 处理 {filename} 时出错：{e}")

    excel.Quit()

# 修改这里的路径为你的文件夹路径
folder = r"C:\Users\hucon\Desktop\wps"
convert_xls_to_xlsx(folder)
