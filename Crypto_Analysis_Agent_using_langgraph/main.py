from llm import react_graph,react_graph_memory ,SystemMessage, HumanMessage, config

print("✨ Crypto ReAct Agent — type 'exit' to quit. ✨ \n")
# messages = [HumanMessage(content="Compare BTC and ETH: current data + 3 latest headlines each. Which looks stronger short-term? Keep it concise")]
#
# out = react_graph.invoke({"messages": messages})
# print(out["messages"])
#
# for m in out["messages"]:
#     try:
#         m.pretty_print()
#     except Exception:
#         print(m)


# if __name__ == "__main__":



while True:
    try:
        user_input = input("👤 Ask me anything about Crypto: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n👋 Bye!")
        break

    if not user_input:
        continue
    if user_input.lower() in {"exit", "quit"}:
        print("👋 Bye!")
        break

    try:
        messages = [HumanMessage(content=user_input)]
        result = react_graph_memory.invoke({"messages": messages}, config)

        final_ai_response = next((m for m in reversed(result["messages"]) if m.type == "ai"), None)
        if final_ai_response:
            print(f"🤖 Agent: {final_ai_response.content}\n")
        else:
            print("🤖 Agent: [No reply]\n")
    except Exception as e:
        print(f"⚠️ Error: {e}")


