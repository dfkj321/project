from db import db

def create_tables():
    """创建数据库表"""
    
    # 创建股票基本信息表
    create_stocks_table = """
    CREATE TABLE IF NOT EXISTS stocks (
        stock_code VARCHAR(10) PRIMARY KEY,
        stock_name VARCHAR(50) NOT NULL,
        listing_date DATE,
        industry VARCHAR(50),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建资金流向表
    create_capital_flow_table = """
    CREATE TABLE IF NOT EXISTS capital_flow (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock_code VARCHAR(10),
        date DATE,
        main_net_inflow DECIMAL(20,2),
        big_order_net_inflow DECIMAL(20,2),
        mid_order_net_inflow DECIMAL(20,2),
        small_order_net_inflow DECIMAL(20,2),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_stock_date (stock_code, date),
        FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    )
    """
    
    # 创建DDE分析表
    create_dde_analysis_table = """
    CREATE TABLE IF NOT EXISTS dde_analysis (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock_code VARCHAR(10),
        date DATE,
        ddx DECIMAL(10,4),
        ddy DECIMAL(10,4),
        ddz DECIMAL(10,4),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_stock_date (stock_code, date),
        FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    )
    """
    
    # 创建持仓分析表
    create_position_analysis_table = """
    CREATE TABLE IF NOT EXISTS position_analysis (
        id INT AUTO_INCREMENT PRIMARY KEY,
        stock_code VARCHAR(10),
        date DATE,
        increase_ratio_1d DECIMAL(10,4),
        increase_ratio_3d DECIMAL(10,4),
        increase_ratio_5d DECIMAL(10,4),
        increase_ratio_10d DECIMAL(10,4),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_stock_date (stock_code, date),
        FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
    )
    """
    
    # 创建板块趋势表
    create_sector_trend_table = """
    CREATE TABLE IF NOT EXISTS sector_trend (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sector_name VARCHAR(50),
        date DATE,
        turnover_rate DECIMAL(10,4),
        rise_fall_ratio DECIMAL(10,4),
        net_inflow DECIMAL(20,2),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_sector_date (sector_name, date)
    )
    """
    
    # 创建大盘趋势表
    create_market_trend_table = """
    CREATE TABLE IF NOT EXISTS market_trend (
        id INT AUTO_INCREMENT PRIMARY KEY,
        index_code VARCHAR(10),
        index_name VARCHAR(50),
        date DATE,
        close_price DECIMAL(10,2),
        change_ratio DECIMAL(10,4),
        turnover DECIMAL(20,2),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_index_date (index_code, date)
    )
    """
    
    # 执行创建表操作
    tables = [
        create_stocks_table,
        create_capital_flow_table,
        create_dde_analysis_table,
        create_position_analysis_table,
        create_sector_trend_table,
        create_market_trend_table
    ]
    
    for table_query in tables:
        try:
            db.execute_update(table_query)
            print(f"表创建成功")
        except Exception as e:
            print(f"创建表时出错: {str(e)}")

if __name__ == "__main__":
    create_tables()
    print("数据库初始化完成") 