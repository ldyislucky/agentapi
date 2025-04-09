from src.agentapi.utils.redis_tool import get_conversation_chain

redis_chain = get_conversation_chain("user_123")
response1 = redis_chain.run("请问我的第一个问题是什么？")
print(response1)