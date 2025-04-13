import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import pandas as pd
from sqlalchemy import create_engine
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试多个可能的配置文件路径
def load_env_from_multiple_paths():
    # 配置文件可能的路径
    possible_paths = [
        Path(__file__).parent.parent / "config" / ".env",  # 标准路径: project/config/.env
        Path("config/.env"),  # 如果从项目根目录运行
        Path("../project/config/.env"),  # 如果从上一级目录运行
        Path(__file__).parent.parent.parent / "project" / "config" / ".env",  # 如果从其他目录结构运行
    ]
    
    # 尝试加载每个路径
    for path in possible_paths:
        if path.exists():
            logger.info(f"加载配置文件: {path}")
            load_dotenv(path)
            return True
    
    # 如果没有找到配置文件，使用默认配置
    logger.warning("未找到配置文件，使用默认配置")
    return False

# 加载配置文件
load_env_from_multiple_paths()

class DatabaseConnection:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com")
        self.user = os.getenv("DB_USER", "hucongyanRoot")
        self.password = os.getenv("DB_PASSWORD", "Hu123456")
        self.database = os.getenv("DB_DATABASE", "stock_analysis")
        self.port = os.getenv("DB_PORT", "3306")
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "30"))
        self.socket_timeout = int(os.getenv("DB_SOCKET_TIMEOUT", "60"))
        self.charset = os.getenv("DB_CHARSET", "utf8mb4")
        self.connection = None
        self.engine = None
        
        logger.info(f"数据库配置: host={self.host}, database={self.database}, port={self.port}, connect_timeout={self.connect_timeout}, charset={self.charset}")

    def connect(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    port=int(self.port),
                    connect_timeout=self.connect_timeout,
                    charset=self.charset,
                    use_pure=True # 使用纯Python实现，有时能解决连接问题
                )
                logger.info("数据库连接成功")
                print("数据库连接成功")
        except Error as e:
            logger.error(f"数据库连接错误: {e}")
            print(f"数据库连接错误: {e}")
            raise

    def get_engine(self):
        if not self.engine:
            # 修正SSL参数，移除ssl_mode参数，添加charset
            connection_str = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?connect_timeout={self.connect_timeout}&charset={self.charset}"
            self.engine = create_engine(connection_str)
        return self.engine

    def execute_query(self, query, params=None):
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"查询执行错误: {e}")
            print(f"查询执行错误: {e}")
            raise

    def execute_update(self, query, params=None):
        try:
            self.connect()
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Error as e:
            logger.error(f"更新执行错误: {e}")
            print(f"更新执行错误: {e}")
            self.connection.rollback()
            raise

    def query_to_dataframe(self, query, params=None):
        try:
            return pd.read_sql_query(query, self.get_engine(), params=params)
        except Exception as e:
            logger.error(f"DataFrame转换错误: {e}")
            print(f"DataFrame转换错误: {e}")
            raise

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
            print("数据库连接已关闭")

# 单例模式
db = DatabaseConnection() 