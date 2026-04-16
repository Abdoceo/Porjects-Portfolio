from dotenv import load_dotenv  # Import environment variable loader
from typing import Annotated, List  # Import types for validation
from langgraph.graph import StateGraph, START, END  # Import core graph structures
from numpy.f2py.crackfortran import usermodules

load_dotenv()  # Load secrets/API keys once
from langgraph.graph.message import add_messages  # Helper to append messages
from langchain.chat_models import init_chat_model  # Quickly initialize AI models
from typing_extensions import TypedDict  # Define structured dictionary states
from pydantic import BaseModel, Field  # Create schemas for validation
from web_operations import serp_search, reddit_search_api, reddit_post_retrieval
from prompts import (
    get_reddit_analysis_messages,
    get_google_analysis_messages,
    get_bing_analysis_messages,
    get_reddit_url_analysis_messages,
    get_synthesis_messages
)

llm = init_chat_model("gemini-3.1-flash-lite-preview", model_provider="google_genai")
#llm = init_chat_model("gemini-1.5-flash", model_provider="google_genai")

# we write everything down here so it doesn't lose its way
class State(TypedDict):
    # The record of every conversation
    messages: Annotated[list, add_messages]

    # What the user actually asked
    user_question: str | None
    # What the Google search found
    google_results: str | None
    # What the Bing search found
    bing_results: str | None
    # What the Reddit search found
    reddit_results: str | None
    # The specific links worth visiting
    selected_reddit_urls: list[str] | None
    # The deep details inside Reddit
    reddit_post_data: list | None
    # The AI's thoughts on Google
    google_analysis: str | None
    # The AI's thoughts on Bing
    bing_analysis: str | None
    # The AI's thoughts on Reddit
    reddit_analysis: str | None
    # The grand conclusion for user
    final_answer: str | None

# THE SMART TEMPLATE: so i did this because i want to make sure the formats in clean, structured way
class RedditURLAnalysis(BaseModel):
    # THE RESTRICTION: This must be a LIST of STRINGS (URLs)
    # Field(description=...): Acts as a direct instruction to the AI's "brain"
    selected_urls: List[str] = Field(
        description="List of Reddit URLs that contain valuable information for answering the user's question"
    )
def google_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Google for: {user_question}")

    google_results = serp_search(user_question, engine="google")
    #print(google_results)

    return {"google_results": google_results}

def bing_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Bing for: {user_question}")

    bing_results = serp_search(user_question, engine= "bing")
    #print( bing_results)

    return {"bing_results": bing_results}


def reddit_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching reddit for: {user_question}")

    reddit_results = reddit_search_api(user_question)
    print(reddit_results)

    return {"reddit_results": reddit_results}


def analyze_reddit_posts(state: State):
    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")

    if not reddit_results:
        return {"selected_reddit_urls": []}

    structured_llm = llm.with_structured_output(RedditURLAnalysis) # force llm model to output in the particular format, we call it pydantic model
    messages = get_reddit_url_analysis_messages(user_question, reddit_results)

    try:
        analysis = structured_llm.invoke(messages)
        selected_urls = analysis.selected_urls

        # DISPLAY: Show a clear title so we know what follows
        print("Selected URLs:")
        # LOOP: Go through the list one by one
        # enumerate(..., 1) starts the counting at 1 instead of 0 (for humans!)
        for i, url in enumerate(selected_urls, 1):
            # OUTPUT: Print a numbered list (e.g., "1. https://reddit.com/...")
            print(f"   {i}. {url}")

    except Exception as e:
        print(e)
        selected_urls = []

    return {"selected_reddit_urls": selected_urls}

def retrieve_reddit_posts(state: State):
    print("Getting reddit post comments")

    selected_urls = state.get("selected_reddit_urls", [])

    if not selected_urls:
        return {"reddit_post_data": []}

    print(f"Processing {len(selected_urls)} Reddit URLs")

    reddit_post_data = reddit_post_retrieval(selected_urls)

    if reddit_post_data:
        print(f"Successfully got {len(reddit_post_data)} posts")
    else:
        print("Failed to get post data")
        reddit_post_data = []

    print(reddit_post_data)
    return {"reddit_post_data": reddit_post_data}


def analyze_google_results(state: State):
    print("Analyzing google search results")

    user_question = state.get("user_question", "")
    google_results = state.get("google_results", "")

    messages = get_google_analysis_messages(user_question, google_results)
    reply = llm.invoke(messages)

    return {"Google_analysis": reply.content}

def analyze_bing_results(state: State):
    print("Analyzing bing search results")

    user_question = state.get("user_question", "")
    bing_results = state.get("bing_results", "")

    messages = get_bing_analysis_messages(user_question, bing_results)
    reply = llm.invoke(messages)

    return {"bing_analysis": reply.content}


def analyze_reddit_results(state: State):
    print("Analyzing reddit search results")

    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")
    reddit_post_data = state.get("reddit_post_data", "")

    messages = get_reddit_analysis_messages(user_question, reddit_results, reddit_post_data)
    reply = llm.invoke(messages)

    return {"reddit_analysis": reply.content}

def synthesize_analyses(state: State):    # agreggate all func above
    print("Combine all results together")

    user_question = state.get("user_question", "")
    google_analysis = state.get("google_analysis", "")
    bing_analysis = state.get("bing_analysis", "")
    reddit_analysis = state.get("reddit_analysis", "")

    messages = get_synthesis_messages(
        user_question, google_analysis, bing_analysis, reddit_analysis
    )

    reply = llm.invoke(messages)
    final_answer = reply.content

    return {"final_answer": final_answer, "messages": [{"role": "assistant", "content": final_answer}]}


graph_builder = StateGraph(State)

graph_builder.add_node("google_search", google_search) # creating the nodes of the graph
graph_builder.add_node("bing_search", bing_search)
graph_builder.add_node("reddit_search", reddit_search)
graph_builder.add_node("analyze_reddit_posts", analyze_reddit_posts)
graph_builder.add_node("retrieve_reddit_posts", retrieve_reddit_posts)
graph_builder.add_node("analyze_google_results", analyze_google_results)
graph_builder.add_node("analyze_bing_results", analyze_bing_results)
graph_builder.add_node("analyze_reddit_results", analyze_reddit_results)
graph_builder.add_node("synthesize_analyses", synthesize_analyses)

graph_builder.add_edge(START, "google_search") # creating the connecter(lines) of the graph
graph_builder.add_edge(START, "bing_search") # so here w econnect the start node with all three nodes
graph_builder.add_edge(START, "reddit_search")

graph_builder.add_edge("google_search", "analyze_reddit_posts")
graph_builder.add_edge("bing_search", "analyze_reddit_posts")
graph_builder.add_edge("reddit_search", "analyze_reddit_posts") # reddit takes time to scrapping posts
graph_builder.add_edge("analyze_reddit_posts", "retrieve_reddit_posts")

graph_builder.add_edge("retrieve_reddit_posts", "analyze_google_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_bing_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_reddit_results")

graph_builder.add_edge("analyze_google_results", "synthesize_analyses")
graph_builder.add_edge("analyze_bing_results", "synthesize_analyses")
graph_builder.add_edge("analyze_reddit_results", "synthesize_analyses")

graph_builder.add_edge("synthesize_analyses", END)

graph = graph_builder.compile()  # execute the graph

def run_chatbot():
    print("Multi-Source Research Agent")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("Ask me anything: ")
        if user_input.lower() == "exit":
            print("Bye")
            break

        # otherwise, initallize starting state

        state = {
            "messages": [{"role": "user", "content": user_input}],
            "user_question": user_input,
            "google_results": None,   # # The Google scroll is blank
            "bing_results": None,
            "reddit_results": None,
            "selected_reddit_urls": None,
            "reddit_post_data": None,
            "google_analysis": None,
            "bing_analysis": None,
            "reddit_analysis": None,
            "final_answer": None,
        }

        print("\nStarting parallel research process...")
        print("Launching Google, Bing, and Reddit searches...\n")
        final_state = graph.invoke(state)  # pass our state

        # If the prize was found
        if final_state.get("final_answer"):
            print(f"\nFinal Answer is:\n{final_state.get('final_answer')}\n")

        print("-" * 50)

# execute the function if the file name is main
if __name__ == "__main__":
    run_chatbot()
