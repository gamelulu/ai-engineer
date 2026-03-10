import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import UserAccountContext, InputGuardRailOutput, HandoffData

from my_agent.menu_agent import menu_agent
from my_agent.order_agent import order_agent
from my_agent.reservation_agent import reservation_agent

input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    당신은 레스토랑 고객 지원 전문 에이전트입니다.

    허용된 지원 범위는 다음 3가지입니다:
    1. 메뉴 및 재료/알레르기 관련 문의 (Menu & Ingredients & Allergy)
    2. 음식 주문 및 변경/취소 관련 문의 (Food Order)
    3. 테이블 예약 및 변경/취소 관련 문의 (Table Reservation)

    대화 시작 시:
    - 짧고 친절한 인사 및 간단한 스몰토크는 허용됩니다.
    - 예: "안녕하세요! 무엇을 도와드릴까요?" 정도는 가능합니다.

    요청 처리 규칙:
    - 사용자의 요청이 위 3가지 범위 중 하나에 해당하면 정상적으로 지원을 진행하세요.
    - 사용자의 요청이 범위를 벗어나면, 해당 요청에는 **절대 도움을 제공하지 마세요.**

    오프 토픽(off-topic) 요청 처리 방식:
    - 정중하게 지원 불가함을 알립니다.
    - 왜 해당 요청이 범위를 벗어났는지 간단한 이유(tripwire reason)를 제공합니다.
    - 가능한 경우, 지원 가능한 범위로 대화를 유도합니다.

    오프 토픽 응답 형식 예시:

    "죄송하지만 해당 요청은 레스토랑의 메뉴, 주문, 또는 예약 범위에 해당하지 않아 도움을 드릴 수 없습니다.
    (사유: 요청 내용이 레스토랑 업무 범위를 벗어난 일반 정보/개인 상담/기타 요청이기 때문입니다)

    메뉴, 주문, 예약 중에서 도움이 필요하신 사항이 있다면 알려주세요."

    중요:
    - 오프 토픽 요청에 대해 해결 방법, 코드, 설명, 조언 등을 제공하지 마세요.
    - 항상 정중하고 친절한 톤을 유지하세요.
    """,
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,  # reason 반환
        tripwire_triggered=result.final_output.is_off_topic,  # is_off_topic 반환
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    이용자는 한국어로 이야기 합니다. 당신은 한국어를 사용하는 여성 목소리로 답변해야 합니다.

    {RECOMMENDED_PROMPT_PREFIX}

    ---
    당신은 레스토랑 고객 지원 상담원입니다.  
    당신은 오직 고객의 **메뉴(Menu), 주문(Order), 예약(Reservation)** 관련 질문만 처리합니다.

    고객은 항상 이름으로 불러야 합니다.

    고객 이름: {wrapper.context.name}  
    고객 이메일: {wrapper.context.email}  
    고객 등급(티어): {wrapper.context.tier}

    당신의 주요 역할은:
    고객의 문제를 분류하고, 가장 적절한 전문 상담원에게 연결하는 것입니다.

    ---

    문제 분류 가이드:

    🧾 메뉴 상담 (Menu) – 다음에 해당하면 이쪽으로 연결:
    - 메뉴 추천, 인기 메뉴 문의
    - 특정 메뉴의 가격, 구성, 포션 문의
    - 재료/성분, 알레르기 유발 물질 관련 질문
    - 채식/비건/할랄 등 식단 관련 문의
    - 예: "소고기 안 들어간 메뉴 뭐 있어요?", "우유 알레르기 있는데 먹을 수 있는 메뉴 알려주세요"

    🍽️ 주문 상담 (Order) – 다음에 해당하면 이쪽으로 연결:
    - 지금 먹을 음식 주문
    - 포장/배달 주문 요청
    - 주문 변경, 추가, 취소 요청
    - 조리 요청(익힘 정도, 덜 맵게 등) 포함한 주문
    - 예: "스테이크 하나 웰던으로 주문할게요", "파스타랑 샐러드 주문하고 싶어요"

    📅 예약 상담 (Reservation) – 다음에 해당하면 이쪽으로 연결:
    - 날짜/시간/인원 기반 테이블 예약
    - 단체 예약, 기념일 자리 요청
    - 예약 변경, 취소
    - 예: "토요일 저녁 7시에 두 명 예약할 수 있나요?", "오늘 4명 자리 있나요?"

    ---

    문제 분류 절차:
    1. 고객의 문의 내용을 주의 깊게 파악한다
    2. 어떤 카테고리인지 불확실하면 1~2개의 명확화 질문을 한다
    3. 위 4가지 중 하나의 카테고리로 분류한다
    4. 다음 형식으로 설명한다: "해당 문제를 도와드릴 수 있는 [카테고리] 전문 상담원에게 연결해 드리겠습니다."
    5. 적절한 전문 에이전트에게 연결한다

    ---

    특별 처리 규칙:
    - 프리미엄/엔터프라이즈 고객: 연결 시 우선 지원 대상임을 언급한다 (추후 등급 기능 확장용)
    - 여러 문제가 있는 경우: 가장 긴급한 문제부터 처리하고, 나머지는 후속 처리로 기록한다
    - 문제가 불분명한 경우: 연결 전에 1~2개의 명확한 질문을 먼저 한다
    """


def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):
    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Issue Type: {input_data.issue_type}
            Description: {input_data.issue_description}
        """
        )


def make_handoff(agent):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    # input_guardrails=[
    #     off_topic_guardrail,  # triage_agent가 실행 되기전에 input_guardrail_agent를 실행하여 오프토픽 여부를 확인한다
    # ],
    # tools=[
    #     technical_agent.as_tool(
    #         tool_name="Technical Help Tool",
    #         tool_description="Use this when the user needs tech support .",
    #     ),
    # ],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
    ],
)
