import asyncio

import dotenv
import streamlit as st

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)
from models import UserAccountContext
from my_agent.triage_agent import triage_agent


dotenv.load_dotenv()


user_account_ctx = UserAccountContext(
    customer_id=1,
    name="정영",
    tier="basic",
)


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message.get("type") == "message":
                        st.write(message["content"][0]["text"].replace("$", "\\$"))


async def run_agent(message: str):
    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        try:
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=user_account_ctx,  # 모든 function tool에 전달되는 context
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\\$"))
                elif event.type == "agent_updated_stream_event":
                    if st.session_state["agent"].name != event.new_agent.name:
                        st.write(
                            f"🤖 Transfered from {st.session_state['agent'].name} to {event.new_agent.name}"
                        )
                        st.session_state["agent"] = event.new_agent
                        text_placeholder = st.empty()
                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""
        except InputGuardrailTripwireTriggered:
            st.write("I can't help you with that.")
        except OutputGuardrailTripwireTriggered:
            st.write("Cant show you that answer.")
            st.session_state["text_placeholder"].empty()


# 이전 대화 이력 렌더링
asyncio.run(paint_history())

message = st.chat_input(
    "레스토랑 메뉴, 주문, 예약에 대해 물어보세요.",
)

if message:
    with st.chat_message("user"):
        st.write(message)
    asyncio.run(run_agent(message))


with st.sidebar:
    st.title("세션 관리")
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
