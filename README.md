以下是基于 **LangChain 0.3.x+ 版本**的 Agent 创建方式、应用场景及参数详解：

---

### 一、Agent 的常用创建方式
LangChain 提供多种类型的 Agent，常见创建方式如下：

#### 1. **使用 `create_react_agent`（基于 ReAct 框架）**
   ```python
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.tools import Tool
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek

# 这个函数内必须含有第一行注释供 langchain-community 的工具注册
@tool
def search_tool(s: str) -> str:
    """查询天气"""
    print(s)
    return f"今天天气很好"


tools = [
    Tool(
        name="Search",
        func=search_tool,  # 自定义的工具函数
        description="查询天气情况", # 这个描述不可缺少，大模型通过该描述来选择工具，否则无法选择，应该也可以跟函数内部的描述保持一致
    )
]

# 加载基础 Prompt
prompt = hub.pull("hwchase17/react")

# 初始化模型
model = ChatDeepSeek(model="deepseek-chat", max_tokens=200)

# 创建 Agent
agent = create_react_agent(model, tools, prompt)

# 包装为执行器（添加容错逻辑）
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# 运行Agent
response = agent_executor.invoke({"input": "10的平方是多少？"})
print(response["output"])  # 输出：10的平方是 100


# # 运行Agent
# response = agent_executor.invoke({"input": "今天天气怎样？"})
# print(response["output"])  # 输出：今天天气很好
   ```

#### 2. **使用 `create_structured_chat_agent`（结构化输入）**

   用于需要结构化输入/输出的场景（如处理 JSON 数据）：
   ```python
   from langchain.agents import create_structured_chat_agent

   prompt = hub.pull("hwchase17/structured-chat")
   agent = create_structured_chat_agent(model, tools, prompt)
   ```

#### 3. **使用 `create_tool_calling_agent`（工具调用优化）**
   **新版本推荐**，支持模型直接调用工具的结构化输出：
   ```python
   from langchain.agents import create_tool_calling_agent

   agent = create_tool_calling_agent(model, tools, prompt)
   ```

---

### 二、应用场景

| **Agent 类型**            | **适用场景**                                                 |
| ------------------------- | ------------------------------------------------------------ |
| **ReAct Agent**           | 需要推理（Reasoning）与行动（Action）的循环场景，如复杂问题分步解决、实时数据查询。 |
| **Structured Chat Agent** | 处理结构化数据输入/输出（如 JSON）、多工具协作场景。         |
| **Self-Debug Agent**      | 支持自我纠错，适用于代码生成或需要迭代调试的任务。           |
| **Conversational Agent**  | 长期对话场景，依赖 Memory 模块维护上下文（如客服聊天机器人）。 |

---

### 三、关键参数详解

#### 1. **核心参数**

| 参数                    | 说明                                  | 示例值                       |
| ----------------------- | ------------------------------------- | ---------------------------- |
| `llm`                   | 必选，语言模型实例                    | `ChatOpenAI(model="gpt-4")`  |
| `tools`                 | 必选，Agent可调用的工具列表           | `[tool1, tool2]`             |
| `agent_type`            | Agent类型（如ReAct、Structured Chat） | `"structured-chat-react"`    |
| `memory`                | 记忆模块，保存对话历史                | `ConversationBufferMemory()` |
| `verbose`               | 输出详细日志                          | `True`                       |
| `max_iterations`        | 最大执行迭代次数，防无限循环          | `5`                          |
| `handle_parsing_errors` | 解析错误时自动修复或提示              | `True`                       |

   - **`model`**: 必填，LLM 实例（如 `ChatOpenAI`、`ChatAnthropic`）。
   - **`tools`**: 必填，工具列表（`Tool` 对象或等效的 List）。
   - **`prompt`**: Agent 的提示模板，可通过 `hub.pull()` 加载预置模板或自定义。
     ```python
     from langchain.promorts import PromptTemplate
     prompt = PromptTemplate.from_template("...")
     ```

#### 2. **AgentExecutor 参数**
   - **`max_iterations`**: 最大执行步数（默认 15），防止无限循环。
   - **`early_stopping`**: 早停机制（如 `"force"` 强制返回最终答案）。
   - **`handle_parsing_errors`**: 处理解析失败的策略（设为 `True` 自动重试或返回错误消息）。
   - **`memory`**: 添加对话历史（如 `ConversationBufferMemory`）。

   ```python
   agent_executor = AgentExecutor(
       agent=agent,
       tools=tools,
       verbose=True,
       max_iterations=20,
       handle_parsing_errors=True,
       memory=ConversationBufferMemory()
   )
   ```

#### 3. **高级参数**
   - **`return_intermediate_steps`**: 返回中间步骤结果（用于调试）。
   - **`output_parser`**: 自定义输出解析逻辑（覆盖默认解析）。

---

### 四、老版本LangChain 示例代码

#### 带记忆的对话 Agent
```python
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(memory_key="chat_history")
agent_executor = initialize_agent(
    tools,
    ChatOpenAI(),
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    handle_parsing_errors=True
)
```

#### 自定义工具与解析
使用 `@tool` 装饰器快速定义工具：
```python
from langchain.agents import tool

@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    # 实现天气查询逻辑
    return f"Weather in {city}: Sunny"
```

---

### 五、注意事项
1. **版本兼容性**：LangChain 0.3.x+ 删除了部分旧接口（如 `AgentType.ZERO_SHOT_REACT_DESCRIPTION`），改用更明确的创建函数。
2. **错误处理**：建议开启 `handle_parsing_errors=True` 避免因输出格式错误导致崩溃。
3. **性能调优**：限制 `max_iterations` 并在生产环境禁用 `verbose`。

如需最新 API 文档，建议参考 [LangChain 官方文档](https://python.langchain.com/docs/modules/agents/)。





















































