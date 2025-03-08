from typing import List,TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from models import get_llm
from config import logger


# 定义状态图的状态类型
class State(TypedDict):
    messages: List[BaseMessage]

# 创建状态图
def create_state_graph():
    llm = get_llm()
    graph_builder = StateGraph(state_schema=State)

    def chatbot(state: State):
        try:
            # 裁剪消息以适应最大 token 数限制
            trimmed_messages = trim_messages(
                max_tokens=1024,
                max_messages=20,
                strategy="last",
                token_counter=llm,
                include_system=True,
                allow_partial=False,
                start_on="human",
            ).invoke(state["messages"])

            # 创建提示模板
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "你是来自倍智信息的智能体，小智。你能帮助工厂员工处理相关问题。"),
                MessagesPlaceholder(variable_name="messages"),
            ])

            # 调用大模型生成回复
            prompt = prompt_template.invoke(trimmed_messages)
            response = llm.invoke(prompt)
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Error in chatbot: {e}")
            raise RuntimeError("Error in chatbot processing")

    # 添加节点和边
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    # 使用内存保存检查点
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)