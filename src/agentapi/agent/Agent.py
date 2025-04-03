from fastapi import FastAPI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.prebuilt import chat_agent_executor
from src.agentapi.utils.DbTool import MysqlTool
import logging
from langchain.globals import set_debug

app = FastAPI()

class DbAgent:
    def __init__(self, model_name="deepseek-chat", max_tokens=200):
        """
        初始化 DbAgent 类。
        """
        # # 启用LangChain调试模式（可选）
        # set_debug(True)
        # # 设置日志级别（可选）
        # logging.basicConfig(level=logging.DEBUG)

        # 初始化模型
        self.model = ChatDeepSeek(model=model_name, max_tokens=max_tokens)

        # 初始化 DbTool 并获取连接参数
        self.mysqltool = MysqlTool()
        self.dburl = self.mysqltool.get_url()
        self.db = SQLDatabase.from_uri(self.dburl)

        # 创建工具
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
        self.tools = self.toolkit.get_tools()

        # 系统提示词
        self.system_prompt = """
        您是一个被设计用来与SQL数据库交互的代理。
        给定一个输入问题，创建一个语法正确的SQL语句并执行，然后查看查询结果并返回答案。
        除非用户指定了他们想要获得的示例的具体数量，否则始终将SQL查询限制为最多10个结果。
        你可以按相关列对结果进行排序，以返回MySQL数据库中最匹配的数据。
        你可以使用与数据库交互的工具。在执行查询之前，你必须仔细检查。如果在执行查询时出现错误，请重写查询SQL并重试。
        不要对数据库做任何DML语句(插入，更新，删除，删除等)。

        首先，你应该查看数据库中的表，看看可以查询什么。
        不要跳过这一步。
        然后查询最相关的表的模式。
        """

        # 创建代理
        self.agent_executor = chat_agent_executor.create_tool_calling_executor(
            self.model,
            self.tools,
        )

    # app = FastAPI()

    @app.post("/server")
    def query(self, user_question):
        """
        执行用户问题的查询并返回最终答案。
        :param user_question: 用户提出的问题
        :return: 最终答案
        """
        # 执行代理
        resp = self.agent_executor.invoke({
            'messages': [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_question)
            ]
        })

        # 提取最终答案
        final_answer = next(
            (
                msg.content
                for msg in reversed(resp['messages'])
                if isinstance(msg, AIMessage)
            ),
            "未找到有效回答"
        )
        return final_answer

db_agent = DbAgent()

# 示例用法
if __name__ == "__main__":
    db_agent = DbAgent()
    result = db_agent.query('套餐1都有哪些菜品？')
    print("最终答案：", result)