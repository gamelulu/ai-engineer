from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import STORY_WRITER_DESCRIPTION, story_writer_instruction
from .tools import save_story_page

MODEL = LiteLlm(model="openai/gpt-4o")


def create_story_writer(page_num: int) -> Agent:
    return Agent(
        name=f"StoryWriter_Page{page_num}",
        model=MODEL,
        description=STORY_WRITER_DESCRIPTION,
        instruction=story_writer_instruction,
        tools=[save_story_page],
    )
