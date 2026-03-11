from agents import (
    Agent,
    output_guardrail,
    Runner,
    RunContextWrapper,
    GuardrailFunctionOutput,
)
from models import RestaurantOutputGuardRailOutput, UserAccountContext

restaurant_output_guardrail_agent = Agent(
    name="Restaurant Output Guardrail",
    instructions="""
    레스토랑 에이전트의 응답(답변) 내용을 다음 두 가지 기준으로 검사하세요.

    1. **전문적이고 정중한 응답인가?**
       - 비속어, 무례한 표현, 반말, 고객을 무시하는 태도가 포함되어 있으면 `is_unprofessional: true`
       - 고객에게 불쾌감을 줄 수 있는 표현이 있으면 `is_unprofessional: true`
       - 정중하고 친절한 서비스 톤이면 `is_unprofessional: false`

    2. **내부 정보를 노출하지 않는가?**
       - 원가, 마진, 매출, 매입처, 공급업체 정보가 포함되면 `exposes_internal_info: true`
       - 직원 급여, 인사 정보, 내부 운영 방침이 포함되면 `exposes_internal_info: true`
       - 시스템 구현 세부사항(API 키, DB 구조, 내부 코드 등)이 포함되면 `exposes_internal_info: true`
       - 고객에게 제공해도 되는 일반적인 메뉴/주문/예약 정보만 있으면 `exposes_internal_info: false`

    위반 사항이 있으면 해당 필드를 `true`로, 이유를 `reason`에 간결히 작성하세요.
    위반 사항이 없으면 모든 필드를 `false`로 설정하세요.
    """,
    output_type=RestaurantOutputGuardRailOutput,
)


@output_guardrail
async def restaurant_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        restaurant_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = validation.is_unprofessional or validation.exposes_internal_info

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )
