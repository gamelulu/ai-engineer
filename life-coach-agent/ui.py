import os
import asyncio

import streamlit as st
from openai import OpenAI


def _chat_role(role: str | None, item: dict | object | None = None) -> str:
    """세션 role / type → st.chat_message 이름."""
    if role == "user":
        return "human"

    item_type = None
    if isinstance(item, dict):
        item_type = item.get("type")
    elif item is not None:
        item_type = getattr(item, "type", None)

    if item_type in ("file_search_call", "web_search_call"):
        return "tool"

    return "ai"


def _raw_role_and_type(item) -> tuple[str | None, str | None]:
    """세션 아이템에서 role, type을 안전하게 추출."""
    if isinstance(item, dict):
        return item.get("role"), item.get("type")
    return getattr(item, "role", None), getattr(item, "type", None)


def _text_from_item(item) -> str | None:
    """세션 아이템에서 표시할 텍스트 추출."""
    content = (
        item.get("content")
        if isinstance(item, dict)
        else getattr(item, "content", None)
    )
    if isinstance(content, str):
        return content
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            return first["text"]
        if hasattr(first, "text"):
            return getattr(first, "text", None)

    # content 가 없고, tool 호출 아이템인 경우 queries 기반으로 텍스트 구성
    if isinstance(item, dict):
        _role, item_type = _raw_role_and_type(item)
        # file_search_call / web_search_call 공통 처리:
        # - 우선 최상위 queries
        # - 없으면 action.queries / action.query
        if item_type in ("file_search_call", "web_search_call"):
            queries = item.get("queries") or []
            if not (isinstance(queries, list) and queries):
                action = item.get("action") or {}
                if isinstance(action, dict):
                    queries = action.get("queries") or []
                    query = action.get("query")
                    if not (isinstance(queries, list) and queries) and isinstance(
                        query, str
                    ):
                        return f"[{item_type}] {query}"
            if isinstance(queries, list) and queries:
                return f"[{item_type}] {queries[0]}"

    return None


def _preview(text: str, max_len: int = 10) -> str:
    """내용 일부만 한 줄로만 보여주기."""
    if not text:
        return ""
    # 줄바꿈 제거해서 항상 한 줄로만 표시
    text = text.replace("\n", " ").strip()
    return (text[:max_len] + "…") if len(text) > max_len else text


def render_app(run_agent, session) -> None:
    """메모리(세션) 전체 대화를 보여주고, 좌측에 메모리 내용을 요약해서 표시."""
    try:
        items = asyncio.run(session.get_items())
    except Exception:
        items = []

    with st.sidebar:
        uploaded_file = st.file_uploader(
            "파일 선택", type=None, key="memory_sidebar_uploader"
        )
        if uploaded_file is not None:
            # 벡터 스토어에 업로드 (환경 변수 OPENAI_VECTOR_STORE_ID 필요)
            vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")
            if vector_store_id:
                try:
                    client = OpenAI()
                    # Streamlit UploadedFile 객체를 직접 업로드
                    uploaded_file.seek(0)
                    file_obj = client.files.create(
                        file=uploaded_file, purpose="assistants"
                    )
                    client.vector_stores.files.create(
                        vector_store_id=vector_store_id,
                        file_id=file_obj.id,
                    )
                    st.caption(f"벡터 스토어({vector_store_id})에도 업로드 완료")
                except Exception as e:
                    st.caption(f"벡터 스토어 업로드 오류: {e}")
            else:
                st.caption("벡터 스토어 ID가 설정되지 않아 업로드를 건너뛰었습니다.")

        # 메모리 전체 클리어 버튼
        if st.button("Clear", key="clear_memory_sidebar"):
            try:
                asyncio.run(session.clear_session())
            except Exception as e:
                st.warning(f"메모리 초기화 중 오류: {e}")
            # 세션이 비워졌으니 화면도 초기 상태로 리렌더링
            st.rerun()

        for i, item in enumerate(reversed(items)):
            raw_role, item_type = _raw_role_and_type(item)

            if raw_role == "user":
                label_role = "user"
            elif raw_role in ("assistant", "ai"):
                label_role = "assistant"
            elif item_type in ("file_search_call", "web_search_call"):
                label_role = "tool"
            else:
                label_role = raw_role or "?"

            text = _text_from_item(item) or ""
            preview = _preview(text)
            label = f"{label_role}: {preview}"
            with st.expander(label, expanded=(i == 0)):
                st.json(item)

    for item in items:
        role, _item_type = _raw_role_and_type(item)
        text = _text_from_item(item)
        if text is None:
            continue
        with st.chat_message(_chat_role(role, item)):
            st.markdown(text)

    # 하단: 기본 채팅 입력만 배치
    prompt = st.chat_input("무엇이든 물어보세요")

    if prompt:
        with st.chat_message("human"):
            st.write(prompt)
        asyncio.run(run_agent(prompt))
        st.rerun()
