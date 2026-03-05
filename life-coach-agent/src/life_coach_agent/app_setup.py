import os
import copy

from agents import (
    Agent,
    SQLiteSession,
    WebSearchTool,
    FileSearchTool,
    ImageGenerationTool,
)
from .prompts.loader import load_prompt


SYSTEM_PROMPT = load_prompt("system_prompt")
VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID")


class FilteredSQLiteSession(SQLiteSession):
    """세션 히스토리에서 action 필드만 제거한 버전을 모델에 전달하기 위한 세션 래퍼.

    - 모델(API)에 전달할 때는 action 필드를 제거해서
      'input[n].action' 같은 알 수 없는 파라미터 에러를 방지한다.
    - UI(메모리 뷰어 등)에서는 get_items_raw()를 통해 원본을 그대로 볼 수 있다.
    """

    def __init__(self, session_id: str, database: str):
        super().__init__(session_id, database)

    def _remove_action_recursive(self, obj):
        if isinstance(obj, dict):
            cleaned = {k: v for k, v in obj.items() if k != "action"}
            return {k: self._remove_action_recursive(v) for k, v in cleaned.items()}
        if isinstance(obj, list):
            return [self._remove_action_recursive(item) for item in obj]
        return obj

    async def get_items(self):
        """모델에 전달할 때 사용하는, action 필드가 제거된 히스토리."""
        items = await super().get_items()
        return [self._remove_action_recursive(copy.deepcopy(item)) for item in items]

    async def get_items_raw(self):
        """UI 등에서 사용할, action 필드가 포함된 원본 히스토리."""
        return await super().get_items()


def create_session() -> SQLiteSession:
    """필터링된 SQLite 세션 인스턴스를 생성."""
    return FilteredSQLiteSession("chat-history", "chat-gpt-clone-memory.db")


def create_agent() -> Agent:
    """현재 프로젝트용 기본 Agent 인스턴스를 생성."""
    tools = [WebSearchTool()]
    if VECTOR_STORE_ID:
        tools.append(
            FileSearchTool(
                max_num_results=5,
                vector_store_ids=[VECTOR_STORE_ID],
            )
        )

    tools.append(
        ImageGenerationTool(
            tool_config={
                "type": "image_generation",
                "quality": "high",
                "output_format": "jpeg",
                "moderation": "low",
                "partial_images": 1,
            },
        )
    )

    return Agent(
        name="ChatGPT Clone",
        model="gpt-4o",
        instructions=SYSTEM_PROMPT,
        tools=tools,
    )


def create_agent_and_session() -> tuple[Agent, SQLiteSession]:
    """Agent와 Session을 함께 생성하는 헬퍼."""
    session = create_session()
    agent = create_agent()
    return agent, session

