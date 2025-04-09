# === 1. 导入库 ===
from datetime import datetime        # 处理时间相关操作
from langchain_community.cache import RedisCache  # 将LLM缓存存储到Redis
from langchain.globals import set_llm_cache  # 设置全局LLM缓存
import redis                          # 连接和操作Redis数据库
from langchain_deepseek import ChatDeepSeek  # DeepSeek对话模型
from langchain.memory import ConversationBufferMemory  # 对话历史记录管理基类
from langchain.schema import messages_to_dict, messages_from_dict, HumanMessage  # 消息序列化/反序列化
from pydantic import Field           # Pydantic字段定义
from langchain_core.runnables.history import RunnableWithMessageHistory  # 管理对话历史的可执行链
import uuid                          # 生成唯一会话ID
from langchain_core.output_parsers import StrOutputParser  # 将模型输出解析为字符串
from langchain_core.prompts import ChatPromptTemplate  # 构建聊天提示模板

# === 2. 设置 Redis 缓存 ===
redis_client = redis.Redis(
    host='192.168.46.130',  # Redis服务器IP地址
    port=6379,              # Redis服务器端口号
    password='123321'       # Redis访问密码
)
set_llm_cache(RedisCache(redis_client))  # 将全局LLM缓存设置为Redis缓存

# === 3. 自定义 RedisConversationMemory 类 ===
class RedisConversationMemory(ConversationBufferMemory):
    session_key: str = Field(default=None)  # 显式声明会话键字段（用于Redis的键）

    def __init__(self, redis_client, session_id, *args, **kwargs):
        """
        初始化方法：
        - redis_client: 连接Redis的客户端实例
        - session_id: 用户唯一会话标识符（如用户ID）
        - 动态生成Redis键：如 "chat_session:user_123"
        """
        super().__init__(*args, **kwargs)  # 继承父类初始化
        self._redis_client = redis_client  # 存储Redis客户端实例（私有属性）
        self.session_key = f"chat_session:{session_id}"  # 动态生成Redis键

    def load_memory_variables(self, inputs):
        """
        加载Redis中存储的对话历史：
        - 从Redis读取会话数据（messages和last_updated）
        - 将序列化的消息列表反序列化为消息对象列表
        """
        print(f'load_memory_variables: {inputs}')
        # 从Redis加载hash类型的历史对话数据
        stored_data = self._redis_client.hgetall(self.session_key)
        if stored_data:
            # 反序列化消息列表（b'messages'是字节类型，需eval转为Python对象）（注意eval有安全风险，实际建议用json,遇到不得不用的时候怎么办）
            self.chat_memory.messages = messages_from_dict(eval(stored_data[b'messages']))
        return super().load_memory_variables(inputs)  # 返回父类的加载结果

    def save_context(self, inputs, outputs):
        """
        保存当前对话到Redis：
        - 将消息列表序列化为字符串
        - 存储到Redis的哈希表中（键为session_key）
        - 设置键的TTL（生存时间）为24小时
        """
        print(f'save_context:{inputs}')
        print(f'save_context:{outputs}')
        super().save_context(inputs, outputs)  # 先执行父类的保存逻辑
        messages_data = messages_to_dict(self.chat_memory.messages)  # 序列化消息列表
        self._redis_client.hset(  # 存储消息和最后更新时间
            self.session_key,
            mapping={
                'messages': str(messages_data),    # 消息列表转字符串
                'last_updated': str(datetime.now())  # 当前时间
            }
        )
        self._redis_client.expire(self.session_key, 86400)  # 设置24小时过期时间

    def add_messages(self, messages):
        """向对话历史中添加新消息（消息对象列表）"""
        for message in messages:
            self.chat_memory.add_message(message)

    @property
    def messages(self):
        """返回当前对话历史消息列表（只读属性）"""
        return self.chat_memory.messages

# === 4. 创建 RedisConversationMemory 实例 ===
memory = RedisConversationMemory(
    redis_client=redis_client,  # 已初始化的Redis客户端
    session_id="user_123"       # 唯一会话标识（如用户ID）
)

# === 5. 创建 LLM 实例（DeepSeek对话模型）===
llm = ChatDeepSeek(
    model="deepseek-chat",   # 使用的DeepSeek模型名称
    max_tokens=200           # 模型生成的最大输出标记数
)

# === 6. 配置对话链（RunnableWithMessageHistory）===
# session_id = str(uuid.uuid4())  # 生成唯一会话ID（如："a1b2c3d4..."）
session_id = "user_123"

# 定义对话链：输入 -> 提示模板 -> LLM推理 -> 输出解析
chain = (
    ChatPromptTemplate.from_messages([  # 构建提示模板
        ("human", "{input}")  # 用户输入占位符（通过{input}传递）
    ]) |
    llm |
    StrOutputParser()  # 将LLM输出转为字符串
)

# 正确实现：根据session_id动态创建记忆实例
def get_memory(session_id):
    return RedisConversationMemory(redis_client=redis_client, session_id=session_id)

# 初始化RunnableWithMessageHistory
conversation = RunnableWithMessageHistory(
    chain,
    get_memory,  # 传入函数，根据session_id返回对应实例
    input_messages_key="input",
    history_messages_key="history"
)

# 调用示例
resp = conversation.invoke(
    {"input": [HumanMessage(content="你好")]},
    {"configurable": {"session_id": session_id}}  # 传递会话ID
)
print(resp)  # 打印模型生成的回复内容


resp1 = conversation.invoke(
    {"input": [HumanMessage(content="我的第一句话是？")]},  # 使用消息对象列表
    {"configurable": {"session_id": session_id}}
)
print(resp1)  # 打印输出内容