
from fastapi import APIRouter
from src.agentapi.utils.redis_tool import get_conversation_chain

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/chat")
async def query_redis(user_id: str,question: str):
    redis_chain = get_conversation_chain(user_id)
    response1 = redis_chain.run(question)
    print(response1)
    return {"response": response1}
