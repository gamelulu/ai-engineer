from typing import Optional
import json

from google.adk.agents import Agent  # type: ignore[import-unresolved]
from google.adk.agents.context import Context  # type: ignore[import-unresolved]
from google.adk.models.lite_llm import LiteLlm  # type: ignore[import-unresolved]
from google.genai import types  # type: ignore[import-unresolved]

_DUMMY_MODEL = LiteLlm(model="openai/gpt-4o")


def create_progress_agent(name: str, message: str) -> Agent:
    async def _show(callback_context: Context) -> Optional[types.Content]:
        return types.Content(parts=[types.Part(text=message)])

    return Agent(
        name=name,
        model=_DUMMY_MODEL,
        instruction="progress",
        before_agent_callback=_show,
    )


async def on_story_writer_end(
    callback_context: Context,
) -> Optional[types.Content]:
    story_data = callback_context.state.get("story_data")
    if not story_data:
        return types.Content(
            role="model",
            parts=[types.Part.from_text(text="✅ 스토리 작성이 완료되었습니다.")],
        )

    if not isinstance(story_data, dict):
        try:
            story_data = json.loads(story_data)
        except Exception:
            try:
                story_data = story_data.model_dump()  # type: ignore[attr-defined]
            except Exception:
                return types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text="✅ 스토리 작성이 완료되었습니다.")
                    ],
                )

    title = story_data.get("title", "제목 없음")
    pages = story_data.get("pages", [])
    pages = sorted(
        [p for p in pages if isinstance(p, dict)],
        key=lambda p: p.get("page_number", 0),
    )

    lines = [f'✅ 제목: "{title}"', ""]
    for page in pages:
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        visual = page.get("visual_description", "")
        # Markdown 렌더러가 줄바꿈을 합치지 않도록 강제 개행(두 칸 + 개행) 사용
        page_block = f"Page {page_num}:  \n" f"Text: {text}  \n" f'Visual: "{visual}"'
        lines.extend([page_block, ""])

    return types.Content(
        role="model",
        parts=[types.Part.from_text(text="\n".join(lines).strip())],
    )
