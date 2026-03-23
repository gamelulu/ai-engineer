from typing import List

from google.adk.agents import Agent  # type: ignore[import-unresolved]
from google.adk.models.lite_llm import LiteLlm  # type: ignore[import-unresolved]
from pydantic import BaseModel, Field, ConfigDict

from .prompt import STORY_WRITER_AGENT_DESCRIPTION, STORY_WRITER_AGENT_PROMPT

MODEL = LiteLlm(model="openai/gpt-4o")


class PageData(BaseModel):
    model_config = ConfigDict(json_schema_extra={"additionalProperties": False})

    page_number: int = Field(description="페이지 번호 (1~5)")
    text: str = Field(description="해당 페이지의 동화 텍스트 (한국어)")
    visual_description: str = Field(
        description="해당 페이지의 일러스트를 위한 시각적 설명 (한국어)"
    )


class StoryData(BaseModel):
    model_config = ConfigDict(json_schema_extra={"additionalProperties": False})

    title: str = Field(description="동화 제목")
    pages: List[PageData] = Field(description="5개 페이지 리스트")


def create_story_writer_agent(before_cb=None, after_cb=None) -> Agent:
    return Agent(
        name="StoryWriterAgent",
        model=MODEL,
        description=STORY_WRITER_AGENT_DESCRIPTION,
        instruction=STORY_WRITER_AGENT_PROMPT,
        include_contents="none",
        output_schema=StoryData,
        output_key="story_data",
        before_agent_callback=before_cb,
        after_agent_callback=after_cb,
    )
