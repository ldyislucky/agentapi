from langchain.memory import ConversationBufferMemory
from redis import Redis
import json
from typing import Dict, Any
from time import time
from langchain.schema import HumanMessage, AIMessage
from pydantic import BaseModel, Field


class RedisConversationMemory(ConversationBufferMemory):
    redis: Redis = Field(...)  # 必填字段
    session_id: str = Field(...)  # 必填字段
    max_history: int = Field(default=10)  # 可选字段，默认值为 10

    def __init__(self, redis_client: Redis, session_id: str, max_history=10, *args, **kwargs):
        # 将 redis_client 和 session_id 传递给 Pydantic 父类
        super().__init__(
            redis=redis_client,
            session_id=session_id,
            max_history=max_history,
            *args,
            **kwargs
        )
        self._load_initial_history()

    def _load_initial_history(self):
        # 从 Redis 加载历史对话
        stored_messages = self.redis.lrange(f"chat:{self.session_id}", 0, -1)
        for msg in stored_messages[::-1]:  # Redis 列表是反向存储
            message_data = json.loads(msg)
            self.chat_memory.add_message(
                HumanMessage(content=message_data['content']) if message_data['type'] == 'human'
                else AIMessage(content=message_data['content'])
            )

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """保存上下文到内存和 Redis"""
        super().save_context(inputs, outputs)

        # 序列化消息
        user_msg = json.dumps({
            'type': 'human',
            'content': inputs['input'],
            'timestamp': time()
        })
        ai_msg = json.dumps({
            'type': 'ai',
            'content': outputs['response'],
            'timestamp': time()
        })

        # 使用 Pipeline 批量操作
        pipeline = self.redis.pipeline()
        pipeline.lpush(f"chat:{self.session_id}", user_msg, ai_msg)
        pipeline.ltrim(f"chat:{self.session_id}", 0, self.max_history * 2 - 1)  # 保留最近 N 轮
        pipeline.expire(f"chat:{self.session_id}", 86400)  # 24 小时过期
        pipeline.execute()
