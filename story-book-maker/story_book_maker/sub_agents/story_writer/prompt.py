from google.adk.agents.readonly_context import ReadonlyContext

STORY_WRITER_DESCRIPTION = (
    "테마를 바탕으로 어린이 동화의 한 페이지를 작성하고 State에 저장하는 에이전트입니다."
)

PAGE_GUIDE = {
    1: "주인공과 배경 소개",
    2: "사건의 시작 또는 모험의 출발",
    3: "갈등이나 도전",
    4: "문제 해결 과정",
    5: "결말과 교훈",
}

BASE_INSTRUCTION = """\
당신은 4~8세 어린이를 위한 동화 작가입니다.

## 규칙
- 한국어로 작성합니다.
- text는 2~3문장, 짧고 따뜻하게 작성합니다.
- visual_description은 일러스트를 그릴 수 있도록 장면, 캐릭터, 색감을 구체적으로 한국어로 묘사합니다.
- 캐릭터와 배경의 시각적 일관성을 유지하세요.
- 폭력적이거나 무서운 내용은 피하세요.
- 반드시 `save_story_page` 도구를 호출하여 작성한 페이지를 저장하세요.
"""


def story_writer_instruction(context: ReadonlyContext) -> str:
    current = context.state.get("current_page_number", 0)
    next_page = current + 1
    previous_pages = context.state.get("story_pages", [])
    story_title = context.state.get("story_title", "")

    guide = PAGE_GUIDE.get(next_page, "")

    if next_page == 1:
        return (
            BASE_INSTRUCTION
            + f"\n지금 **1페이지**를 작성하세요.\n"
            f"사용자의 테마를 바탕으로 동화 제목을 짓고, 첫 페이지를 만드세요.\n"
            f"가이드: {guide}\n\n"
            f"`save_story_page` 도구를 호출하여 저장하세요."
        )

    prev_summary = "\n".join(
        [f"  - {p['page_number']}페이지: {p['text']}" for p in previous_pages]
    )
    return (
        BASE_INSTRUCTION
        + f"\n## 현재 진행\n"
        f"- 제목: {story_title}\n"
        f"- 완성: {current}/5\n"
        f"- 이전 내용:\n{prev_summary}\n\n"
        f"지금 **{next_page}페이지**를 작성하세요.\n"
        f"가이드: {guide}\n"
        f"이전 흐름을 자연스럽게 이어가고 `save_story_page` 도구를 호출하여 저장하세요."
    )
