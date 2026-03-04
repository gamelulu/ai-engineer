import dotenv

dotenv.load_dotenv()
import os
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID")

if "agent" not in st.session_state:
    tools = [WebSearchTool()]
    if VECTOR_STORE_ID:
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=[VECTOR_STORE_ID],
            )
        )

    st.session_state["agent"] = Agent(
        name="ChatGPT Clone",
        model="gpt-4o",
        instructions="""
        당신은 도움이 되는 어시스턴트입니다.

        다음과 같은 내용을 찾고 요약하기 위해 웹 검색 도구를 사용할 수 있습니다:
        - 동기부여 및 영감을 주는 콘텐츠
        - 자기계발 팁
        - 습관 형성과 행동 변화에 대한 조언

        또한 사용자가 업로드한 문서를 검색하기 위해
        OpenAI Vector Store 기반의 파일 검색 도구가 설정되어 있다면
        이를 사용하여 문서를 검색할 수 있습니다.

        사용자에게 답변할 때는 한국어를 우선적으로 사용하세요.
        """,
        tools=tools,
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


from ui import render_app

render_app(run_agent, session)
