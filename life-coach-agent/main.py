import dotenv

dotenv.load_dotenv()
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="ChatGPT Clone",
        model="gpt-4o",
        instructions="""
        You are a helpful assistant.

        You can use a web search tool to find and summarize:
        - motivation and inspirational content
        - self-development tips
        - habit formation and behavior change advice

        Prefer Korean when replying to the user.
        """,
        tools=[
            WebSearchTool(),
        ],
    )
agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db",
    )
session = st.session_state["session"]


def _get_tool_call_query(event) -> str | None:
    if getattr(event, "type", None) != "run_item_stream_event":
        return None

    item = getattr(event, "item", None)
    if getattr(item, "type", None) != "tool_call_item":
        return None

    raw = getattr(item, "raw_item", None)
    if getattr(raw, "type", None) != "web_search_call":
        return None

    action = getattr(raw, "action", None)
    if not action:
        return None

    if isinstance(action, dict):
        queries = action.get("queries")
    else:
        queries = getattr(action, "queries", None)

    if isinstance(queries, (list, tuple)) and queries:
        return str(queries[0])

    return None


async def run_agent(message):
    stream = Runner.run_streamed(
        agent,
        message,
        session=session,
    )

    full_response = ""
    tool_call_lines = []  # e.g. [웹 검색: "검색어"]
    with st.chat_message("ai"):
        placeholder = st.empty()

        def _update_ui():
            parts = []
            for line in tool_call_lines:
                parts.append(f"**{line}**")
            if full_response:
                parts.append(full_response)
            placeholder.markdown("\n\n".join(parts) if parts else " ")

        async for event in stream.stream_events():
            # WebSearchTool 호출 감지
            if event.type == "run_item_stream_event":
                query = _get_tool_call_query(event)
                if query:
                    line = f'[웹 검색: "{query}"]'
                    # 같은 검색어가 여러 번 찍히는 것을 방지
                    if line not in tool_call_lines:
                        tool_call_lines.append(line)
                    _update_ui()
                continue

            # 모델 텍스트 스트리밍
            if event.type == "raw_response_event":
                if event.data.type == "response.output_text.delta":
                    full_response += event.data.delta
                    _update_ui()


prompt = st.chat_input("Write a message for your assistant")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
