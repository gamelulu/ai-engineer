import base64
from typing import Awaitable, Callable

import streamlit as st
from agents import Agent, Runner, SQLiteSession


def _get_tool_call_query(event) -> str | None:
    """웹 검색 도구 호출 시, 검색어를 추출."""
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


def _update_status(status_container, event_type: str | None) -> None:
    """스트리밍 중 툴 사용/상태를 요약해서 보여주는 상태 메시지 업데이트."""
    if not event_type:
        return

    status_messages = {
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": (
            "🔍 Starting web search...",
            "running",
        ),
        "response.web_search_call.searching": (
            "🔍 Web search in progress...",
            "running",
        ),
        "response.file_search_call.completed": ("✅ File search completed.", "complete"),
        "response.file_search_call.in_progress": (
            "🗂️ Starting file search...",
            "running",
        ),
        "response.file_search_call.searching": (
            "🗂️ File search in progress...",
            "running",
        ),
        "response.image_generation_call.generating": (
            "🎨 Drawing image...",
            "running",
        ),
        "response.image_generation_call.in_progress": (
            "🎨 Drawing image...",
            "running",
        ),
        "response.completed": (" ", "complete"),
    }

    label_state = status_messages.get(event_type)
    if not label_state:
        return
    label, state = label_state
    status_container.update(label=label, state=state)


def make_run_agent(agent: Agent, session: SQLiteSession) -> Callable[[str], Awaitable[None]]:
    """Agent와 Session에 바인딩된 run_agent 코루틴을 생성."""

    async def run_agent(message: str) -> None:
        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        with st.chat_message("ai"):
            status_container = st.status("⌛", expanded=False)
            text_placeholder = st.empty()
            image_placeholder = st.empty()

            full_response = ""
            tool_call_lines: list[str] = []

            def _update_text():
                parts: list[str] = []
                for line in tool_call_lines:
                    parts.append(f"**{line}**")
                if full_response:
                    parts.append(full_response)
                text_placeholder.markdown("\n\n".join(parts) if parts else " ")

            async for event in stream.stream_events():
                # WebSearchTool 호출 감지 (run_item_stream_event)
                if event.type == "run_item_stream_event":
                    query = _get_tool_call_query(event)
                    if query:
                        line = f'[웹 검색: "{query}"]'
                        if line not in tool_call_lines:
                            tool_call_lines.append(line)
                        _update_text()
                    continue

                # LLM raw 이벤트 처리 (텍스트/이미지 + 상태)
                if event.type == "raw_response_event":
                    event_type = getattr(event.data, "type", None)
                    _update_status(status_container, event_type)

                    if event_type == "response.output_text.delta":
                        full_response += event.data.delta
                        _update_text()
                    elif event_type == "response.image_generation_call.partial_image":
                        image = base64.b64decode(event.data.partial_image_b64)
                        image_placeholder.image(image)

    return run_agent

