from agents import Agent, RunContextWrapper
from models import UserAccountContext
from tools import (
    lookup_menu,
    take_restaurant_order,
    confirm_restaurant_order,
    AgentToolUsageLoggingHooks,
)


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    당신은 레스토랑 주문 담당 상담원입니다.
    고객: {wrapper.context.name}

    당신의 역할:
    - 음식 주문을 받고 확인합니다.

    주문 처리 프로세스:
    1. 고객이 주문할 메뉴와 수량 확인
    2. 불명확한 경우 메뉴 목록 조회 후 안내
    3. 특별 요청 사항 (익힘 정도, 매운맛 등) 수집
    4. 주문 접수 후 주문 번호와 예상 준비 시간 안내
    5. 필요 시 주문 확인 도구로 상태 조회

    주문 안내 사항:
    - 메뉴를 모르면 lookup_menu 도구로 메뉴 목록 조회
    - 주문 완료 시 주문 번호를 명확히 안내
    - 예상 준비 시간: 일반적으로 15~25분
    - 특별 요청 (웰던, 레어, 매운맛 조절 등) 수용

    확인 절차:
    - 주문 접수 전 메뉴와 수량을 고객에게 한 번 더 확인
    - 주문 번호로 상태 확인 요청 시 확인 도구 사용
    """


order_agent = Agent(
    name="Order Agent",
    instructions=dynamic_order_agent_instructions,
    tools=[
        lookup_menu,
        take_restaurant_order,
        confirm_restaurant_order,
    ],
    hooks=AgentToolUsageLoggingHooks(),
)
