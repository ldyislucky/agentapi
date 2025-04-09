import redis
from langchain.chains import ConversationChain
from langchain_deepseek import ChatDeepSeek

from src.agentapi.utils.redis_tool import RedisConversationMemory

redis_client = redis.Redis(
    host='192.168.46.130',  # Redis服务器IP地址
    port=6379,              # Redis服务器端口号
    password='123321'       # Redis访问密码
)

def get_conversation_chain(session_id: str):
    memory = RedisConversationMemory(
        redis_client=redis_client,
        session_id=session_id,
        max_history=5  # 保留最近 5 轮对话
    )

    return ConversationChain(
        llm=ChatDeepSeek(model="deepseek-chat", max_tokens=200),
        memory=memory,
        verbose=True
    )



# 使用示例
chain = get_conversation_chain("user_123")
response = chain.run("请问最近的新闻是什么？")
print(response)

response1 = chain.run("请问我的第一个问题是什么？")
print(response1)