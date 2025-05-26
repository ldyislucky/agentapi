import uvicorn
from fastapi import FastAPI

from src.agentapi.agent.agent import router as agent_router
from src.agentapi.agent.langchat import router as langchat_router
from src.agentapi.agent.login import router as login_router
from fastapi.middleware.cors import CORSMiddleware

# 创建主应用实例
app = FastAPI()

# 添加跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"]
)

# 挂载子路由到主应用
app.include_router(agent_router)
app.include_router(langchat_router)
app.include_router(login_router)

@app.middleware("http")  # 声明这是一个 HTTP 中间件
async def add_custom_header(request, call_next):
    # 1. 先将请求传递给路由处理，得到响应, 也可以提前对请求进行验证等操作
    response = await call_next(request)

    # 2. 在响应头中添加自定义字段，键和值都是自定义，但是不能自定义中文
    response.headers["Custom-Response-Headers"] = "Lidongyang Service"

    # 3. 返回修改后的响应
    return response


# 根路径接口
@app.get("/")
def root():
    return {"message": "Welcome to the API"}



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


# 启动命令：uvicorn src.agentapi.main:app --reload
