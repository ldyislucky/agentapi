import mysql.connector
from mysql.connector import Error

class MysqlTool:
    def __init__(self):
        self.host = '127.0.0.1'
        self.user = 'root'
        self.password = 'root'
        self.database = 'reggie'
        self.port = 3306
        self.conn = None
        self.cursor = None

        # 初始化连接
        self.connect()

    def connect(self):
        """建立 MySQL 数据库连接"""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.conn.is_connected():
                print("数据库连接成功")
                self.cursor = self.conn.cursor()
            else:
                print("数据库连接失败")
        except Error as e:
            print("数据库连接失败:", e)

    def execute_query(self, query: str):
        """执行 SQL 查询并返回结果"""
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Error as e:
            print("Error:", e)
            return None
        finally:
            # 资源清理：关闭游标
            if self.conn.is_connected():
                self.cursor.close()

    def get_connection_params(self):
        """返回数据库连接参数"""
        return {
            'host': self.host,
            'user': self.user,
            'password': self.password,
            'database': self.database
        }

    def close(self):
        """关闭数据库连接"""
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print("数据库连接已关闭")
        else:
            print("数据库连接已关闭")

    def get_url(self):
        return f'mysql+mysqldb://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4'

mysqltool = MysqlTool()
