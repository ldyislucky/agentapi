from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_deepseek import ChatDeepSeek
from langchain.agents import initialize_agent, AgentType
from langchain_community.tools.tavily_search import TavilySearchResults

# 初始化Redis消息历史（每个会话需唯一session_id）
def get_redis_chat_history(session_id: str):
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://:123321@192.168.46.130:6379/0"
    )

# 创建带Redis记忆的Memory组件
def create_memory(session_id: str):
    chat_history = get_redis_chat_history(session_id)
    return ConversationBufferMemory(
        memory_key="chat_history",  # 修改为 "chat_history"
        input_key="input",
        output_key="output",
        chat_memory=chat_history,
        return_messages=True
    )

# 初始化模型和工具
model = ChatDeepSeek(model="deepseek-chat", max_tokens=200)
search = TavilySearchResults(max_results=2)
tools = [search]

# 创建Agent（集成Redis记忆）
def create_agent(session_id: str):
    memory = create_memory(session_id)
    agent_executor = initialize_agent(
        tools=tools,
        llm=model,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,  # 正确传递memory参数
        verbose=True
    )
    return agent_executor

# 示例会话流程
session_id = "user_125"
agent = create_agent(session_id)

# 第一次对话
response = agent.invoke(
    {
        "input": "Hi, I'm Alice. What's the weather in San Francisco?",
        "chat_history": []  # 显式传递空列表作为初始历史
    }
)
print(response["output"])

# 后续对话
response = agent.invoke(
    {
        "input": "我的第一个问题是什么?",
        "chat_history": response.get("chat_history", [])  # 使用上一轮的聊天历史
    }
)
print(response["output"])
