import streamlit as st

from .app_setup import create_agent_and_session
from .streaming_runner import make_run_agent
from .ui import render_app


def run() -> None:
    """Streamlit 앱을 실행하는 진입점."""
    if "agent" not in st.session_state or "session" not in st.session_state:
        agent, session = create_agent_and_session()
        st.session_state["agent"] = agent
        st.session_state["session"] = session
    else:
        agent = st.session_state["agent"]
        session = st.session_state["session"]

    run_agent = make_run_agent(agent, session)
    render_app(run_agent, session)


if __name__ == "__main__":
    run()

