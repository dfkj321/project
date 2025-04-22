import streamlit as st
from backend.db import db
import pandas as pd

def update_bk_type_mapping():
    """更新板块类型映射表，添加名称字段并填充数据"""
    try:
        # 检查是否已经存在名称字段
        check_query = "SHOW COLUMNS FROM `bk_type_mapping` LIKE '名称';"
        result = db.query_to_dataframe(check_query)
        
        if not result.empty:
            st.success("名称字段已存在，无需更新")
            return
        
        # 添加名称字段
        alter_query = """
        ALTER TABLE `bk_type_mapping`
        ADD COLUMN `名称` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL AFTER `bk_code`;
        """
        db.execute_query(alter_query)
        st.info("已添加名称字段")
        
        # 从capital_flow表填充名称数据
        update_query = """
        UPDATE `bk_type_mapping` bkt
        JOIN (
            SELECT DISTINCT `代码`, `名称` 
            FROM `capital_flow` 
            WHERE `代码` LIKE 'BK%'
        ) cf ON bkt.`bk_code` = cf.`代码`
        SET bkt.`名称` = cf.`名称`;
        """
        db.execute_query(update_query)
        st.success("已从capital_flow表填充名称数据")
        
        # 创建索引
        index_query = "CREATE INDEX idx_bk_name ON `bk_type_mapping`(`名称`);"
        db.execute_query(index_query)
        st.success("已创建名称索引")
        
        # 显示更新后的数据
        data_query = "SELECT * FROM `bk_type_mapping` LIMIT 10;"
        data = db.query_to_dataframe(data_query)
        st.write("板块类型映射表示例数据：")
        st.dataframe(data)
        
    except Exception as e:
        st.error(f"更新板块类型映射表时出错: {str(e)}")

def main():
    st.title("更新板块类型映射表")
    st.write("此脚本将添加名称字段到bk_type_mapping表并从capital_flow表填充数据")
    
    if st.button("执行更新", type="primary"):
        update_bk_type_mapping()

if __name__ == "__main__":
    main() 