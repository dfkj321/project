import socket
import time

print("正在尝试导入pymysql模块...")
try:
    import pymysql
    print("pymysql模块导入成功")
except ImportError:
    print("无法导入pymysql模块，尝试安装...")
    try:
        import pip
        pip.main(['install', 'pymysql'])
        import pymysql
        print("pymysql安装并导入成功")
    except Exception as e:
        print(f"安装pymysql失败: {e}")
        exit(1)

# 数据库连接配置
db_config = {
    "host": "rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com",
    "user": "hucongyanRoot",
    "password": "Hu123456",
    "database": "stock_analysis",
    "port": 3306,
    "connect_timeout": 30,
    "charset": "utf8mb4"
}

print("开始测试数据库连接...")

try:
    # 尝试连接到数据库
    print(f"正在连接到 {db_config['host']}:{db_config['port']}...")
    connection = pymysql.connect(**db_config)
    
    print("数据库连接成功!")
    
    # 获取一些基本信息
    with connection.cursor() as cursor:
        # 获取当前数据库
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print(f"当前数据库: {record[0]}")
        
        # 获取数据库表列表
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"数据库中的表 (前10个):")
        for i, table in enumerate(tables[:10]):
            print(f"  - {table[0]}")
        
        if len(tables) > 10:
            print(f"  ... 共 {len(tables)} 个表")
    
    connection.close()
    print("数据库连接已关闭")
    
except Exception as e:
    print(f"数据库连接失败: {e}") 