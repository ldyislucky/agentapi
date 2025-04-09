# dbtool.py
import mysql.connector
from mysql.connector import Error
import redis
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import chat_agent_executor
from langchain_deepseek import ChatDeepSeek

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
