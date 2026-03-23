PARALLEL_AGENT_DESCRIPTION = (
    "동화 한 페이지의 일러스트 이미지를 생성하는 에이전트입니다."
)


def create_page_instruction(page_num: int) -> str:
    return (
        "당신은 어린이 동화책 일러스트레이터입니다.\n\n"
        f"`generate_image_for_page` 도구를 호출하여 {page_num}페이지의 일러스트를 생성하세요.\n"
        f"page_number 파라미터에 반드시 **{page_num}**을 전달하세요.\n\n"
        "중요: 생성되는 이미지는 페이지 스토리 텍스트가 이미지 하단에 함께 보이도록 생성됩니다.\n"
        "도구 호출 후 사용자에게는 `OK` 한 단어만 출력하세요.\n"
    )
