import mysql.connector
from mysql.connector import Error
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import chat_agent_executor
from langchain_deepseek import ChatDeepSeek
import pymysql
from dbutils.pooled_db import PooledDB


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
                # dictionary=True 将查询结果以 字典（Dictionary） 形式返回，而不是默认的 元组（Tuple） 形式。
                self.cursor = self.conn.cursor(dictionary=True)
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

# 通用性代码添加到 dbtool.py
class AgentTools:
    def __init__(self):
        self.model = ChatDeepSeek(model="deepseek-chat", max_tokens=200)
        self.db = SQLDatabase.from_uri(self.get_url())
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
        self.tools = self.toolkit.get_tools()
        self.system_prompt = """
        您是一个被设计用来与SQL数据库交互的代理。
        给定一个输入问题，创建一个语法正确的SQL语句并执行，然后查看查询结果并返回答案。
        除非用户指定了他们想要获得的示例的具体数量，否则始终将SQL查询限制为最多10个结果。
        你可以按相关列对结果进行排序，以返回MySQL数据库中最匹配的数据。
        您可以使用与数据库交互的工具。在执行查询之前，你必须仔细检查。如果在执行查询时出现错误，请重写查询SQL并重试。
        不要对数据库做任何DML语句(插入，更新，删除，删除等)。

        首先，你应该查看数据库中的表，看看可以查询什么。
        不要跳过这一步。
        然后查询最相关的表的模式。
        """
        self.agent_executor = chat_agent_executor.create_tool_calling_executor(
            self.model,
            self.tools,
        )

    def get_url(self):
        return mysqltool.get_url()

agent_tools = AgentTools()



class MySQLPool(object):
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 3306
        self.user = 'root'
        self.password = 'root'
        self.database = 'agent'
        self.charset = 'utf8'

        # 创建连接池
        self.pool = PooledDB(
            creator=pymysql,  # 使用PyMySQL驱动
            maxconnections=5,  # 连接池最大连接数
            mincached=2,  # 初始化时创建的连接数
            blocking=True,  # 连接数不足时阻塞等待
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset,
            autocommit=True  # 自动提交事务
        )

    def get_conn(self):
        """获取数据库连接"""
        return self.pool.connection()

    def close(self):
        """关闭连接池"""
        self.pool.close()

    def execute_query(self, sql, args=None):
        """执行查询操作"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, args)
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            conn.close()

    def execute_update(self, sql, args=None):
        """执行更新操作"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            rows = cursor.execute(sql, args)
            conn.commit()
            return rows
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

mysql_pool = MySQLPool()

# 使用示例
if __name__ == '__main__':
    mysql_pool = MySQLPool()

    # 测试连接
    try:
        conn = mysql_pool.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        data = cursor.fetchone()
        print("Database version:", data[0])
    finally:
        cursor.close()
        conn.close()

    # 关闭连接池（在程序退出时调用）
    mysql_pool.close()