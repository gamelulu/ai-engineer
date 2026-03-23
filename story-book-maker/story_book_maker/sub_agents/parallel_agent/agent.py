from typing import Optional

from google.adk.agents import Agent  # type: ignore[import-unresolved]
from google.adk.agents.context import Context  # type: ignore[import-unresolved]
from google.adk.agents.parallel_agent import ParallelAgent  # type: ignore[import-unresolved]
from google.adk.models.lite_llm import LiteLlm  # type: ignore[import-unresolved]
from google.genai import types  # type: ignore[import-unresolved]

from .prompt import PARALLEL_AGENT_DESCRIPTION
from .tools import generate_image_for_page

MODEL = LiteLlm(model="openai/gpt-4o")


def _create_generate_callback(page_num: int):
    async def _generate(callback_context: Context) -> Optional[types.Content]:
        result = await generate_image_for_page(
            page_number=page_num,
            tool_context=callback_context,
        )
        if result.get("status") in ("completed", "already_exists"):
            return types.Content(
                role="model",
                parts=[types.Part.from_text(text="OK")],
            )
        return types.Content(
            role="model",
            parts=[
                types.Part.from_text(
                    text=(
                        f"ERROR: page {page_num} image generation failed - "
                        f"{result.get('error', result.get('message', 'unknown'))}"
                    )
                )
            ],
        )

    return _generate


def create_parallel_agent(
    page_before_cb_factory=None,
    page_after_cb_factory=None,
    before_cb=None,
    after_cb=None,
) -> ParallelAgent:
    """5개 페이지의 일러스트를 동시에 생성하는 ParallelAgent를 구성합니다.

    각 페이지 에이전트는 before callback에서 직접 이미지를 생성하므로
    LLM chat completion 호출 없이 실행됩니다.
    """
    illustrators = []

    for i in range(1, 6):
        callback_chain = []
        if page_before_cb_factory:
            callback_chain.append(page_before_cb_factory(i))
        callback_chain.append(_create_generate_callback(i))

        agent = Agent(
            name=f"Illustrator_Page{i}",
            model=MODEL,
            description=PARALLEL_AGENT_DESCRIPTION,
            instruction="Generate page image in callback.",
            before_agent_callback=callback_chain,
            after_agent_callback=(
                page_after_cb_factory(i) if page_after_cb_factory else None
            ),
        )
        illustrators.append(agent)

    return ParallelAgent(
        name="ParallelAgent",
        description="5개 페이지의 일러스트 이미지를 동시에 생성합니다.",
        sub_agents=illustrators,
        before_agent_callback=before_cb,
        after_agent_callback=after_cb,
    )
