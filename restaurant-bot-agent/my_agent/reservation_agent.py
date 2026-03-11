from agents import Agent, RunContextWrapper
from models import UserAccountContext
from tools import (
    check_table_availability,
    make_table_reservation,
    cancel_reservation,
    AgentToolUsageLoggingHooks,
)
from output_guardrails import restaurant_output_guardrail


def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    당신은 레스토랑 예약 담당 상담원입니다.
    고객: {wrapper.context.name}

    당신의 역할:
    - 테이블 예약을 처리합니다.

    예약 처리 프로세스:
    1. 예약 희망일, 시간, 인원 수 확인
    2. 테이블 가용 여부 확인
    3. 가능한 경우 예약 진행 (이름, 연락처 수집)
    4. 예약 번호와 확인 사항 안내

    예약 시 수집 정보:
    - 날짜 (YYYY-MM-DD 형식 권장)
    - 시간 (HH:MM 형식)
    - 인원 수
    - 예약자 이름 (미제공 시 고객 컨텍스트 이름 사용)
    - 연락처 (선택)

    예약 취소:
    - 예약 번호를 확인 후 취소 처리
    - 취소 완료 후 확인 안내

    안내 사항:
    - 예약 10분 전 도착 안내
    - 예약 변경/취소는 가능한 빠르게 요청해 달라고 안내
    """


reservation_agent = Agent(
    name="Reservation Agent",
    instructions=dynamic_reservation_agent_instructions,
    tools=[
        check_table_availability,
        make_table_reservation,
        cancel_reservation,
    ],
    hooks=AgentToolUsageLoggingHooks(),
    output_guardrails=[restaurant_output_guardrail],
)
