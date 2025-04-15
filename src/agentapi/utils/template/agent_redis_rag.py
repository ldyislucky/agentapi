from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.tools import Tool
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek
from langchain_community.document_loaders import Docx2txtLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 初始化模型
model = ChatDeepSeek(model="deepseek-chat", max_tokens=200)


# 初始化Redis消息历史
def get_redis_chat_history(session_id: str):
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://:123321@192.168.46.130:6379/0"
    )

# 创建带Redis记忆的Memory组件
def create_memory(session_id: str):
    chat_history = get_redis_chat_history(session_id)
    return ConversationBufferMemory(
        memory_key="chat_history",
        input_key="input",
        output_key="output",
        chat_memory=chat_history,
        return_messages=True
    )


# 这个函数内必须含有第一行注释供 langchain-community 的工具注册
@tool
def search_tool(s: str) -> str:
    """查询天气"""
    print(s)
    return f"今天天气很好"


# Step 1: 文档加载与处理
# 配置Word文档加载器
def load_documents():
    loader = DirectoryLoader(
        "D:/D/document/python/程序操作空间/操作读取",
        glob="**/*.docx",
        loader_cls=Docx2txtLoader,
        use_multithreading=True  # 启用多线程加速加载
    )
    docs = loader.load()

    # 文本分割（根据需求调整参数）
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", "。", "！", "？"]  # 中文分段优化
    )
    return text_splitter.split_documents(docs)

# Step 2: 创建向量数据库
def create_vector_store():
    docs = load_documents()
    # 2、指定使用的预训练模型名称
    model_name = "D:/D/document/donotdelete/models/bge-large-zh/bge-large-zh-v1.5"

    # 配置模型加载参数，指定设备为 GPU（如果可用），则需修改为 'cuda'
    model_kwargs = {'device': 'cpu'}

    # 配置编码参数，设置 normalize_embeddings 为 True 以支持余弦相似度计算
    encode_kwargs = {'normalize_embeddings': True}

    # 初始化嵌入语义理解模型（使用镜像或本地路径），传入模型名称、加载参数、编码参数和查询指令
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )
    return Chroma.from_documents(docs, embeddings)


# Step 3: 封装 RAG 为工具
def rag_tool(query: str) -> str:
    """当需要回答基于文档的问题时，使用此工具。输入应为具体问题。"""
    vector_db = create_vector_store()
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})  # 返回前3相关片段

    # 构建问答链
    qa_chain = RetrievalQA.from_chain_type(
        llm=model,
        chain_type="stuff",
        retriever=retriever
    )
    return qa_chain.invoke(query)["result"]


# 将 RAG 包装成 LangChain Tool 对象
tools = [
    Tool(
        name="饭店信息",
        func=rag_tool,
        description="""使用场景：当问题涉及饭店和吃饭时调用。
        输入要求：明确的问题文本，例如 '我们的退货政策是什么？'"""
    ),
    Tool(
        name="Search",
        func=search_tool,  # 自定义的工具函数
        description="查询天气情况",  # 这个描述不可缺少，大模型通过该描述来选择工具，否则无法选择，应该也可以跟函数内部的描述保持一致
    )
]


# 加载基础 Prompt
prompt = hub.pull("hwchase17/react-chat")
print(prompt)


# 创建 Agent
agent = create_react_agent(model, tools, prompt)

session_id = "user_126"

# 包装为执行器（添加容错逻辑）
# 必须在此阶段配置的参数
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,                               # `verbose`
    max_iterations=5,                           # `max_iterations`
    handle_parsing_errors=True,                 # `handle_parsing_errors`
    memory=create_memory(session_id)           # `memory`
)

# 4. 测试智能体
question = "你们这里都有哪些套餐？"
result = agent_executor.invoke({"input": question})
print(f"最终答案：{result['output']}")


question = "这个套餐里都有啥？"
result = agent_executor.invoke({"input": question})
print(f"最终答案：{result['output']}")
