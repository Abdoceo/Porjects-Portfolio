from app import crypto_news_tool, crypto_list_tool, crypto_data_tool, llm
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END  # Import core graph structures
from langgraph.prebuilt import tools_condition
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver

# which custom functions it is allowed to use
tools = [crypto_list_tool, crypto_data_tool, crypto_news_tool]
#  executing whichever tool the model requests
tool_node = ToolNode(tools=tools)
llm_with_tools = llm.bind_tools(tools)


system_msg = SystemMessage(
    content="""
You are a professional Crypto Market Analyst Agent.
You answer user questions about cryptocurrencies, market data, and recent news.

AVAILABLE TOOLS:
- crypto_list_tool(limit): get a condensed list of available crypto tickers.
- crypto_data_tool(symbol): get data for a symbol (e.g., BTC, ETH).
- crypto_news_tool(query, max_items): get condensed news (headlines + URLs + snippets).

GUIDELINES:
1) Think step-by-step about the user's question and decide which tools to call.
2) Use tools to retrieve data; do not fabricate metrics or prices.
3) Cite evidence explicitly by referencing the fields you retrieved (e.g., “priceUsd”).
4) Keep responses concise and scannable with bullet points where appropriate.
5) Provide helpful context/definitions when the user seems new to crypto.

DO'S AND DON'TS:
- If an endpoint returns errors or lacks access, explain clearly and propose alternatives.
- Don’t reveal API keys or tokens.

FORMAT:
- Use sections when helpful: “Summary”, “Data”, “What it means”, “Next steps”.
"""
)

# building the graph
# answer and check if there is tool need to excute
def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([system_msg] + state["messages"])]}

builder = StateGraph(MessagesState)

memory = MemorySaver()
config = {"configurable": {"thread_id": "crypto-thread-1"}}


builder.add_node("assistant", assistant)
# runs that tool and gets the answer
builder.add_node("tools", tool_node)

builder.add_edge(START, "assistant")
# A built-in LangGraph router that examines the assistant’s output, If the output does include a tool call → execution is routed to the "tools" node.
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

react_graph = builder.compile()
react_graph_memory = builder.compile(checkpointer=memory)


# Start a conversation state with a user message
#state = {"messages": [HumanMessage(content="What's the latest Bitcoin news?")]}
#state = {"messages": [HumanMessage(content= "Look at the most recent news for both xrp and doge as well as the prices. Tell me is it worth investing and in which one?")]}
state = {"messages": [HumanMessage(content= "Which one did you say was stronger again? And summarize their news in 3 bullets.")]}


#result = react_graph.invoke(state)
result = react_graph_memory.invoke(state, config)





# Print out the agent's reply
# print(result)
# show the latest output message content to neglect the first tool call
# print(result["messages"][-1].content)

# for m in result["messages"]:
#     try:
#         m.pretty_print()
#     except Exception:
#         print(m)