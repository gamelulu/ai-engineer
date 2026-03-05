import os
import asyncio
import base64

import streamlit as st
from openai import OpenAI


client = OpenAI()


def _chat_role(role: str | None, item: dict | object | None = None) -> str:
    """세션 role / type → st.chat_message 이름."""
    if role == "user":
        return "human"

    item_type = None
    if isinstance(item, dict):
        item_type = item.get("type")
    elif item is not None:
        item_type = getattr(item, "type", None)

    if item_type in ("file_search_call", "web_search_call", "image_generation_call"):
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

    # content 가 없고, tool 호출 아이템인 경우 queries / prompt 기반으로 텍스트 구성
    if isinstance(item, dict):
        _role, item_type = _raw_role_and_type(item)
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

        if item_type == "image_generation_call":
            prompt = (
                item.get("revised_prompt")
                or item.get("prompt")
                or item.get("input")
                or ""
            )
            if prompt:
                return f"[image_generation_call] {prompt}"

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
        # FilteredSQLiteSession 이 있으면 원본 get_items_raw()를 사용해
        # action 필드를 포함한 전체 메모리를 UI 에서 볼 수 있게 한다.
        if hasattr(session, "get_items_raw"):
            items = asyncio.run(session.get_items_raw())
        else:
            items = asyncio.run(session.get_items())
    except Exception:
        items = []

    with st.sidebar:
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
            elif item_type in (
                "file_search_call",
                "web_search_call",
                "image_generation_call",
            ):
                label_role = "tool"
            else:
                label_role = raw_role or "?"

            text = _text_from_item(item) or ""
            preview = _preview(text)
            label = f"{label_role}: {preview}"
            with st.expander(label, expanded=(i == 0)):
                st.json(item)

    for item in items:
        role, item_type = _raw_role_and_type(item)

        # 이미지 생성 툴 호출 결과는 실제 이미지를 렌더링
        if isinstance(item, dict) and item_type == "image_generation_call":
            result_b64 = item.get("result")
            if isinstance(result_b64, str) and result_b64:
                try:
                    image_bytes = base64.b64decode(result_b64)
                    with st.chat_message(_chat_role(role, item)):
                        st.image(image_bytes)
                except Exception:
                    text = _text_from_item(item)
                    if text:
                        with st.chat_message(_chat_role(role, item)):
                            st.markdown(text)
            continue

        text = _text_from_item(item)
        if text is None:
            continue
        with st.chat_message(_chat_role(role, item)):
            st.markdown(text)

    # 하단: 파일 첨부를 지원하는 기본 채팅 입력 배치
    prompt = st.chat_input(
        "Write a message for the assistant..",
        accept_file=True,
        file_type=["txt", "md", "pdf", "jpg", "jpeg", "png"],
    )

    if not prompt:
        return

    # 1) 첨부 파일 처리
    files = getattr(prompt, "files", None) or []
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")

    for file in files:
        # 텍스트/문서 파일은 벡터 스토어에 업로드
        if vector_store_id and file.type.startswith(("text/", "application/")):
            with st.chat_message("ai"):
                with st.status("⌛ Uploading file...") as status:
                    try:
                        uploaded = client.files.create(
                            file=(file.name, file.getvalue()),
                            purpose="assistants",
                        )
                        status.update(label="⌛ Attaching file")
                        client.vector_stores.files.create(
                            vector_store_id=vector_store_id,
                            file_id=uploaded.id,
                        )
                        status.update(label="✅ File uploaded", state="complete")
                    except Exception as e:
                        status.update(
                            label=f"❌ File upload failed: {e}", state="error"
                        )

        # 이미지 파일은 세션에 이미지 메시지로 추가하고 바로 보여줌
        elif file.type.startswith("image/"):
            with st.status("⌛ Uploading image...") as status:
                file_bytes = file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                data_url = f"data:{file.type};base64,{base64_data}"
                try:
                    asyncio.run(
                        session.add_items(
                            [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_image",
                                            "detail": "auto",
                                            "image_url": data_url,
                                        }
                                    ],
                                }
                            ]
                        )
                    )
                    status.update(label="✅ Image uploaded", state="complete")
                except Exception as e:
                    status.update(label=f"❌ Image upload failed: {e}", state="error")
            with st.chat_message("human"):
                st.image(data_url)

    # 2) 텍스트 메시지 처리
    text = getattr(prompt, "text", None)
    if text:
        with st.chat_message("human"):
            st.write(text)
        asyncio.run(run_agent(text))
        st.rerun()

