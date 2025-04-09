# agent.py
from fastapi import HTTPException, APIRouter
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agentapi.utils.dbtool import mysqltool, agent_tools

# 创建路由实例，设置前缀和标签
router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/server")
async def query_database(question: str):
    """
    接收用户问题，调用 LangChain 代理执行 SQL 查询，并返回结果。
    """
    try:
        # 调用代理处理问题
        resp = agent_tools.agent_executor.invoke({
            'messages': [
                SystemMessage(content=agent_tools.system_prompt),
                HumanMessage(content=question)
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

        return {"question": question, "answer": final_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
