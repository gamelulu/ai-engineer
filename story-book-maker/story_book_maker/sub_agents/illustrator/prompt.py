from google.adk.agents.readonly_context import ReadonlyContext

ILLUSTRATOR_DESCRIPTION = (
    "State의 현재 페이지 데이터를 읽어 일러스트 이미지를 1장 생성하는 에이전트입니다."
)


def illustrator_instruction(context: ReadonlyContext) -> str:
    current_page = context.state.get("current_page_data")
    page_num = context.state.get("current_page_number", 0)

    if not current_page or page_num == 0:
        return "생성할 페이지가 없습니다. 도구를 호출하지 마세요."

    text = current_page.get("text", "") if isinstance(current_page, dict) else ""
    visual = (
        current_page.get("visual_description", "")
        if isinstance(current_page, dict)
        else ""
    )

    return (
        "당신은 어린이 동화책 일러스트레이터입니다.\n\n"
        "`generate_page_image` 도구를 호출하여 이미지를 생성하세요.\n"
        "도구 호출 후, 결과를 아래 형식 그대로 출력하세요. "
        "다른 말은 추가하지 마세요.\n\n"
        f'Page {page_num}:\n'
        f'Text: "{text}"\n'
        f'Visual: "{visual}"\n'
        "Image: [생성된 이미지가 Artifact로 저장됨]\n"
    )
