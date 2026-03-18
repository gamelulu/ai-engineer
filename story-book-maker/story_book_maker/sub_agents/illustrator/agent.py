from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import ILLUSTRATOR_DESCRIPTION, illustrator_instruction
from .tools import generate_page_image

MODEL = LiteLlm(model="openai/gpt-4o")


def create_illustrator(page_num: int) -> Agent:
    return Agent(
        name=f"Illustrator_Page{page_num}",
        model=MODEL,
        description=ILLUSTRATOR_DESCRIPTION,
        instruction=illustrator_instruction,
        tools=[generate_page_image],
    )
