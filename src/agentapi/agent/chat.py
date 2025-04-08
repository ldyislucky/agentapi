from datetime import datetime
from langchain_community.cache import RedisCache
from langchain.globals import set_llm_cache
import redis
from langchain_deepseek import ChatDeepSeek
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_to_dict, messages_from_dict, HumanMessage
from pydantic import Field
from langchain_core.runnables.history import RunnableWithMessageHistory
import uuid

# 设置 Redis 缓存
redis_client = redis.Redis(
    host='192.168.46.130',
    port=6379,
    password='123321',
)
set_llm_cache(RedisCache(redis_client))

class RedisConversationMemory(ConversationBufferMemory):
    session_key: str = Field(default=None)  # 显式声明 session_key 字段

    def __init__(self, redis_client, session_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redis_client = redis_client  # 使用私有属性存储 Redis 客户端
        self.session_key = f"chat_session:{session_id}"  # 动态赋值

    def load_memory_variables(self, inputs):
        # 从 Redis 加载历史记录
        stored_data = self._redis_client.hgetall(self.session_key)
        if stored_data:
            self.chat_memory.messages = messages_from_dict(eval(stored_data[b'messages']))
        return super().load_memory_variables(inputs)

    def save_context(self, inputs, outputs):
        super().save_context(inputs, outputs)
        # 持久化到 Redis
        messages_data = messages_to_dict(self.chat_memory.messages)
        self._redis_client.hset(self.session_key, mapping={
            'messages': str(messages_data),
            'last_updated': str(datetime.now())
        })
        self._redis_client.expire(self.session_key, 86400)  # 设置 24 小时 TTL

    @property
    def messages(self):
        """Expose the messages attribute from chat_memory."""
        return self.chat_memory.messages

# 使用 RunnableWithMessageHistory 替代 ConversationChain
memory = RedisConversationMemory(
    redis_client=redis_client,
    session_id="user_123"  # 唯一会话标识
)

# 创建 LLM 实例
llm = ChatDeepSeek(model="deepseek-chat", max_tokens=200)

# 调用 invoke，添加 configurable 配置
session_id = str(uuid.uuid4())  # 生成唯一会话 ID

# 修改两处代码实现：

# 1. 调整 RunnableWithMessageHistory 配置（新增输出解析）
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser

# 修改模型调用链
from langchain_core.prompts import ChatPromptTemplate

chain = ChatPromptTemplate.from_messages([
    ("human", "{input}"),  # 使用模板接收字符串
]) | llm | StrOutputParser()

# 然后配置到 RunnableWithMessageHistory
conversation = RunnableWithMessageHistory(
    chain,
    lambda session_id: memory,
    input_messages_key="input",
    history_messages_key="history"
)

# 2. 修改调用方式（使用消息对象）
resp = conversation.invoke(
    {"input": [HumanMessage(content="你好")]},  # 使用消息对象列表
    {"configurable": {"session_id": session_id}}
)
print(resp)  # 打印输出内容
