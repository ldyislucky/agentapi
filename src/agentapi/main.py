from fastapi import FastAPI

from src.agentapi.agent.agent import router as agent_router

# 创建主应用实例
app = FastAPI()

# 挂载子路由到主应用
app.include_router(agent_router)


# 可选：全局中间件或依赖项
@app.middleware("http")
async def add_custom_header(request, call_next):
    response = await call_next(request)
    response.headers["X-Custom-Header"] = "FastAPI-Demo"
    return response

# 根路径接口
@app.get("/")
def root():
    return {"message": "Welcome to the API"}




# 启动命令：uvicorn src.agentapi.main:app --reload
