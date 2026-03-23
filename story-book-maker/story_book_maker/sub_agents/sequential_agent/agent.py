from google.adk.agents.sequential_agent import SequentialAgent  # type: ignore[import-unresolved]


def create_sequential_agent(sub_agents) -> SequentialAgent:
    """Writer → ParallelAgent 순차 흐름을 관리합니다."""
    return SequentialAgent(
        name="SequentialAgent",
        description=(
            "어린이 동화책을 만드는 파이프라인입니다. "
            "StoryWriterAgent가 5페이지 동화를 작성한 후, "
            "ParallelAgent가 5개 이미지를 동시에 생성합니다."
        ),
        sub_agents=sub_agents,
    )
