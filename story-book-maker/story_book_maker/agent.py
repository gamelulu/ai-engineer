from .callbacks import (
    create_progress_agent,
    on_parallel_start,
    on_story_writer_end,
)
from .sub_agents.sequential_agent.agent import create_sequential_agent
from .sub_agents.story_writer_agent.agent import create_story_writer_agent
from .sub_agents.parallel_agent.agent import create_parallel_agent

story_writer = create_story_writer_agent(
    after_cb=on_story_writer_end,
)

parallel = create_parallel_agent(
    before_cb=on_parallel_start,
)

root_agent = create_sequential_agent(
    sub_agents=[
        create_progress_agent(
            "Progress_StoryStart",
            "📖 스토리 작성을 시작합니다...",
        ),
        story_writer,
        create_progress_agent(
            "Progress_ImageStart",
            "✅ 스토리 작성 완료!\n🎨 5개 이미지를 동시에 생성합니다...",
        ),
        parallel,
    ],
)
