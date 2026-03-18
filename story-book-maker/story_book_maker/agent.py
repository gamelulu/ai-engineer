from google.adk.agents.sequential_agent import SequentialAgent

from .sub_agents.story_writer.agent import create_story_writer
from .sub_agents.illustrator.agent import create_illustrator

page_units = []
for i in range(1, 6):
    unit = SequentialAgent(
        name=f"PageUnit_{i}",
        description=f"{i}페이지: 스토리 작성 → 일러스트 생성",
        sub_agents=[create_story_writer(i), create_illustrator(i)],
    )
    page_units.append(unit)

root_agent = SequentialAgent(
    name="StoryBookMakerAgent",
    description=(
        "어린이 동화책을 만드는 에이전트입니다. "
        "페이지 1부터 5까지 순서대로, 각 페이지마다 "
        "StoryWriter가 이야기를 쓰고 Illustrator가 일러스트를 생성합니다. "
        "Agent State를 통해 두 에이전트가 데이터를 공유합니다."
    ),
    sub_agents=page_units,
)
