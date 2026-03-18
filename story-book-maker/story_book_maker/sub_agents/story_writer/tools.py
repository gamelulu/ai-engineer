from google.adk.tools.tool_context import ToolContext


async def save_story_page(
    tool_context: ToolContext,
    title: str,
    page_number: int,
    text: str,
    visual_description: str,
):
    """작성한 동화 페이지를 State에 저장합니다.

    Args:
        title: 동화 제목
        page_number: 페이지 번호 (1-5)
        text: 해당 페이지의 동화 텍스트 (한국어)
        visual_description: 해당 페이지의 시각적 설명 (이미지 생성용, 한국어)
    """
    pages = tool_context.state.get("story_pages", [])

    page_data = {
        "page_number": page_number,
        "text": text,
        "visual_description": visual_description,
    }
    pages.append(page_data)

    tool_context.state["story_title"] = title
    tool_context.state["story_pages"] = pages
    tool_context.state["current_page_data"] = page_data
    tool_context.state["current_page_number"] = page_number

    return {
        "status": "saved",
        "page_number": page_number,
    }
