from agents import Agent, RunContextWrapper
from models import UserAccountContext
from tools import (
    lookup_menu,
    lookup_ingredients,
    check_allergy,
    AgentToolUsageLoggingHooks,
)


def dynamic_menu_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    당신은 레스토랑 메뉴 담당 상담원입니다.
    고객: {wrapper.context.name}

    당신의 역할:
    - 메뉴, 재료, 알레르기 관련 질문에 답변합니다.

    처리 프로세스:
    1. 고객의 질문 유형 파악 (메뉴 조회, 재료 확인, 알레르기 확인)
    2. 적절한 도구를 사용해 정확한 정보 조회
    3. 친절하고 명확하게 답변

    다루는 질문 유형:
    - 메뉴 목록 및 가격 문의
    - 특정 메뉴 상세 정보 (설명, 가격)
    - 메뉴별 재료/성분 확인
    - 알레르기 유발 물질이 포함된 메뉴 확인 (우유, 밀, 계란, 갑각류, 땅콩, 대두, 생선 등)

    알레르기 안내 시 주의사항:
    - 알레르기 정보는 참고용이며, 심한 알레르기가 있으면 직원에게 직접 확인을 권장
    - 교차 오염 가능성에 대해 언급

    메뉴 안내 톤:
    - 친절하고 전문적인 레스토랑 스타일
    - 메뉴 설명 시 맛과 특징을 살려 소개
    """


menu_agent = Agent(
    name="Menu Agent",
    instructions=dynamic_menu_agent_instructions,
    tools=[
        lookup_menu,
        lookup_ingredients,
        check_allergy,
    ],
    hooks=AgentToolUsageLoggingHooks(),
)
