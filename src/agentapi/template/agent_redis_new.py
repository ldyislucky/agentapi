from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.tools import Tool
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek


# 初始化Redis消息历史
def get_redis_chat_history(session_id: str):
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://:123321@192.168.46.130:6379/0"
    )

# 创建带Redis记忆的Memory组件
def create_memory(session_id: str):
    chat_history = get_redis_chat_history(session_id)
    return ConversationBufferMemory(
        memory_key="chat_history",
        input_key="input",
        output_key="output",
        chat_memory=chat_history,
        return_messages=True
    )


# 这个函数内必须含有第一行注释供 langchain-community 的工具注册
@tool
def search_tool(s: str) -> str:
    """查询天气"""
    print(s)
    return f"今天天气很好"


tools = [
    Tool(
        name="Search",
        func=search_tool,  # 自定义的工具函数
        description="查询天气情况", # 这个描述不可缺少，大模型通过该描述来选择工具，否则无法选择，应该也可以跟函数内部的描述保持一致
    )
]

# 加载基础 Prompt
prompt = hub.pull("hwchase17/react-chat")
print(prompt)

# 初始化模型
model = ChatDeepSeek(model="deepseek-chat", max_tokens=200)

# 创建 Agent
agent = create_react_agent(model, tools, prompt)

session_id = "user_126"

# 包装为执行器（添加容错逻辑）
# 必须在此阶段配置的参数
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,                               # `verbose`
    max_iterations=5,                           # `max_iterations`
    handle_parsing_errors=True,                 # `handle_parsing_errors`
    memory=create_memory(session_id)           # `memory`
)

# 运行Agent
response = agent_executor.invoke(
    {
        "input": "10的平方是多少？"
    }
)
print(response["output"])  # 输出：10的平方是 100


# 运行Agent
response = agent_executor.invoke(
    {
        "input": "我的第一个问题是？"
    }
)
print(response["output"])  # 输出：10的平方是 100