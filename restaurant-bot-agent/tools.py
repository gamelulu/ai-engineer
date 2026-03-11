import streamlit as st
from agents import function_tool, AgentHooks, Agent, Tool, RunContextWrapper
from models import UserAccountContext
import random
from datetime import datetime, timedelta


# =============================================================================
# RESTAURANT - MENU TOOLS
# =============================================================================
@function_tool
def lookup_menu(
    context: UserAccountContext,
    category: str = "",
    item_name: str = "",
) -> str:
    """
    레스토랑 메뉴를 조회합니다. 카테고리 또는 특정 메뉴 이름으로 검색할 수 있습니다.

    Args:
        category: 메뉴 카테고리 ( appetizer, main, dessert, beverage, 전체)
        item_name: 검색할 메뉴 이름 (비어있으면 카테고리 전체 조회)
    """
    menu_db = {
        "appetizer": [
            {
                "name": "시저 샐러드",
                "price": 12000,
                "description": "신선한 로메인, 파마산, 크랜베리",
            },
            {
                "name": "감자튀김",
                "price": 8000,
                "description": "바삭한 수제 감자튀김, 트러플 소스",
            },
            {
                "name": "양송이스프",
                "price": 9000,
                "description": "부드러운 크림 양송이스프",
            },
        ],
        "main": [
            {
                "name": "스테이크 200g",
                "price": 35000,
                "description": "앵거스 비프 그릴드 스테이크",
            },
            {
                "name": "파스타 알리오올리오",
                "price": 14000,
                "description": "마늘 기름 파스타",
            },
            {
                "name": "연어 그릴",
                "price": 28000,
                "description": "노르웨이 연어, 레몬 버터 소스",
            },
        ],
        "dessert": [
            {
                "name": "티라미수",
                "price": 11000,
                "description": "전통 이탈리안 티라미수",
            },
            {
                "name": "치즈케이크",
                "price": 10000,
                "description": "뉴욕 스타일 치즈케이크",
            },
        ],
        "beverage": [
            {"name": "에스프레소", "price": 4500, "description": "시그니처 블렌드"},
            {"name": "아메리카노", "price": 5000, "description": "아이스/핫 선택 가능"},
            {"name": "레몬에이드", "price": 6000, "description": "수제 레몬에이드"},
        ],
    }

    if item_name:
        for cat, items in menu_db.items():
            for item in items:
                if item_name.lower() in item["name"].lower():
                    return f"📋 메뉴 정보\n이름: {item['name']}\n가격: {item['price']:,}원\n설명: {item['description']}"
        return f"❌ '{item_name}' 메뉴를 찾을 수 없습니다."

    cat = category.lower() if category else "main"
    items = menu_db.get(cat, [])
    if not items:
        items = [item for items_list in menu_db.values() for item in items_list]

    result = f"📋 메뉴 목록 ({cat if cat in menu_db else '전체'})\n"
    for item in items:
        result += f"\n• {item['name']}: {item['price']:,}원 - {item['description']}"
    return result


@function_tool
def lookup_ingredients(
    context: UserAccountContext,
    menu_item: str,
) -> str:
    """
    특정 메뉴의 재료 목록을 조회합니다.

    Args:
        menu_item: 재료를 확인할 메뉴 이름
    """
    ingredients_db = {
        "시저 샐러드": ["로메인", "파마산 치즈", "크랜베리", "시저드레싱", "크루통"],
        "감자튀김": ["감자", "식용유", "소금", "트러플 소스"],
        "양송이스프": ["양송이", "생크림", "버터", "양파", "마늘"],
        "스테이크 200g": ["앵거스 비프", "소금", "후추", "버터"],
        "파스타 알리오올리오": [
            "스파게티",
            "마늘",
            "올리브오일",
            "파슬리",
            "칠리플레이크",
        ],
        "연어 그릴": ["노르웨이 연어", "레몬", "버터", "다질", "소금"],
        "티라미수": ["마스카포네", "에스프레소", "레디파이드", "코코아파우더"],
        "치즈케이크": ["크림치즈", "그래함 크래커", "설탕", "계란", "바닐라"],
        "에스프레소": ["커피원두", "물"],
        "아메리카노": ["커피원두", "물"],
        "레몬에이드": ["레몬", "설탕", "탄산수", "민트"],
    }

    for name, ingredients in ingredients_db.items():
        if menu_item.lower() in name.lower():
            return f"🥗 {name} 재료\n" + ", ".join(ingredients)
    return f"❌ '{menu_item}' 메뉴의 재료 정보를 찾을 수 없습니다."


@function_tool
def check_allergy(
    context: UserAccountContext,
    allergen: str,
) -> str:
    """
    특정 알레르기 유발 물질이 포함된 메뉴를 조회합니다.

    Args:
        allergen: 알레르기 유발 물질 (우유, 밀, 계란, 갑각류, 땅콩, 대두, 생선 등)
    """
    allergy_db = {
        "우유": [
            "시저 샐러드",
            "양송이스프",
            "스테이크 200g",
            "파스타 알리오올리오",
            "연어 그릴",
            "티라미수",
            "치즈케이크",
        ],
        "밀": ["감자튀김", "파스타 알리오올리오", "티라미수", "치즈케이크", "크루통"],
        "계란": ["시저 샐러드", "양송이스프", "티라미수", "치즈케이크"],
        "갑각류": [],
        "땅콩": [],
        "대두": [],
        "생선": ["연어 그릴"],
        "글루텐": ["감자튀김", "파스타 알리오올리오", "티라미수", "치즈케이크"],
    }

    allergen_key = allergen.strip()
    for key in allergy_db:
        if allergen_key in key or key in allergen_key:
            menus = allergy_db.get(key, [])
            if menus:
                return (
                    f"⚠️ '{key}' 알레르기: 다음 메뉴에 포함되어 있습니다.\n"
                    + "\n".join(f"• {m}" for m in menus)
                )
            return f"✅ '{key}' 알레르기: 해당 성분이 포함된 메뉴가 없습니다."
    return f"⚠️ '{allergen}' 알레르기 정보를 확인했습니다. 상세 문의는 직원에게 연락해 주세요."


# =============================================================================
# RESTAURANT - ORDER TOOLS
# =============================================================================
@function_tool
def take_restaurant_order(
    context: UserAccountContext,
    items: str,
    special_requests: str = "",
) -> str:
    """
    레스토랑 음식 주문을 접수합니다.

    Args:
        items: 주문할 메뉴와 수량 (예: "스테이크 1, 아메리카노 2")
        special_requests: 특별 요청 사항 (예: "웰던으로 해주세요", "매운맛 줄여주세요")
    """
    order_id = f"ORD-{random.randint(1000, 9999)}"
    return f"""
    ✅ 주문이 접수되었습니다
    📋 주문 번호: {order_id}
    📝 주문 내용: {items}
    📌 특별 요청: {special_requests if special_requests else "없음"}
    👤 고객: {context.name}
    ⏱️ 예상 준비 시간: 15~25분
    """.strip()


@function_tool
def confirm_restaurant_order(
    context: UserAccountContext,
    order_id: str,
) -> str:
    """
    접수된 주문 상태를 확인하고 고객에게 최종 확인합니다.

    Args:
        order_id: 확인할 주문 번호 (예: ORD-1234)
    """
    statuses = ["준비 중", "조리 중", "완료 대기"]
    status = random.choice(statuses)
    return f"""
    📋 주문 확인
    🔗 주문 번호: {order_id}
    📊 현재 상태: {status}
    👤 고객: {context.name}
    ℹ️  주문이 정상적으로 접수되었습니다.
    """.strip()


# =============================================================================
# RESTAURANT - RESERVATION TOOLS
# =============================================================================
@function_tool
def check_table_availability(
    context: UserAccountContext,
    date: str,
    time: str,
    party_size: int = 2,
) -> str:
    """
    특정 날짜와 시간의 테이블 가용 여부를 확인합니다.

    Args:
        date: 예약 희망일 (YYYY-MM-DD 형식)
        time: 예약 희망 시간 (HH:MM 형식)
        party_size: 인원 수
    """
    # 간단한 시뮬레이션: 랜덤으로 가용 여부 반환
    available = random.random() > 0.3
    if available:
        slots = ["18:00", "18:30", "19:00", "19:30", "20:00"]
        return f"""
    ✅ 테이블 예약 가능
    📅 날짜: {date}
    ⏰ 시간: {time}
    👥 인원: {party_size}명
    📋 가능한 시간대: {', '.join(slots)}
    """.strip()
    return f"""
    ❌ 해당 시간대에 예약 가능한 테이블이 없습니다
    📅 날짜: {date}
    ⏰ 시간: {time}
    👥 인원: {party_size}명
    💡 다른 날짜나 시간을 문의해 주세요.
    """.strip()


@function_tool
def make_table_reservation(
    context: UserAccountContext,
    date: str,
    time: str,
    party_size: int,
    name: str = "",
    phone: str = "",
) -> str:
    """
    테이블 예약을 완료합니다.

    Args:
        date: 예약일 (YYYY-MM-DD)
        time: 예약 시간 (HH:MM)
        party_size: 인원 수
        name: 예약자 이름
        phone: 연락처
    """
    res_id = f"RES-{random.randint(10000, 99999)}"
    cust_name = name or context.name
    return f"""
    ✅ 예약이 완료되었습니다
    🔗 예약 번호: {res_id}
    📅 날짜: {date}
    ⏰ 시간: {time}
    👥 인원: {party_size}명
    👤 예약자: {cust_name}
    📞 연락처: {phone or '등록됨'}
    ⏱️ 예약 10분 전 도착 부탁드립니다.
    """.strip()


@function_tool
def cancel_reservation(
    context: UserAccountContext,
    reservation_id: str,
) -> str:
    """
    기존 예약을 취소합니다.

    Args:
        reservation_id: 취소할 예약 번호 (예: RES-12345)
    """
    return f"""
    ✅ 예약이 취소되었습니다
    🔗 예약 번호: {reservation_id}
    📧 취소 확인이 {context.email or '등록된 이메일'}로 전송되었습니다.
    💡 재예약을 원하시면 말씀해 주세요.
    """.strip()


# =============================================================================
# RESTAURANT - COMPLAINTS TOOLS
# =============================================================================
@function_tool
def log_complaint(
    context: UserAccountContext,
    complaint_type: str,
    description: str,
    severity: str = "medium",
) -> str:
    """
    고객 불만 사항을 접수하고 기록합니다.

    Args:
        complaint_type: 불만 유형 (food_quality, service, wait_time, hygiene, other)
        description: 불만 상세 내용
        severity: 심각도 (low, medium, high, critical)
    """
    complaint_id = f"CMP-{random.randint(10000, 99999)}"
    return f"""
    📝 불만 사항이 접수되었습니다
    🔗 접수 번호: {complaint_id}
    📂 유형: {complaint_type}
    ⚡ 심각도: {severity.upper()}
    📝 내용: {description}
    👤 고객: {context.name}
    """.strip()


@function_tool
def offer_compensation(
    context: UserAccountContext,
    compensation_type: str,
    details: str = "",
) -> str:
    """
    고객에게 보상을 제안합니다 (환불, 할인, 무료 제공 등).

    Args:
        compensation_type: 보상 유형 (refund, discount, free_item, voucher)
        details: 보상 상세 내용 (예: "디저트 무료 제공", "10% 할인 쿠폰")
    """
    comp_id = f"COMP-{random.randint(10000, 99999)}"
    type_labels = {
        "refund": "환불",
        "discount": "할인 쿠폰",
        "free_item": "무료 메뉴 제공",
        "voucher": "이용권 발급",
    }
    label = type_labels.get(compensation_type, compensation_type)
    return f"""
    🎁 보상이 제안되었습니다
    🔗 보상 번호: {comp_id}
    📋 보상 유형: {label}
    📝 상세: {details if details else label}
    👤 고객: {context.name}
    ✅ 고객 동의 후 적용됩니다.
    """.strip()


@function_tool
def escalate_to_manager(
    context: UserAccountContext,
    issue_summary: str,
    urgency: str = "normal",
) -> str:
    """
    심각한 불만 사항을 매니저에게 에스컬레이션합니다.

    Args:
        issue_summary: 문제 요약
        urgency: 긴급도 (normal, urgent, critical)
    """
    ticket_id = f"ESC-{random.randint(10000, 99999)}"
    callback_time = "30분" if urgency == "critical" else "1시간" if urgency == "urgent" else "2시간"
    return f"""
    🚨 매니저 에스컬레이션 완료
    🔗 티켓 번호: {ticket_id}
    ⚡ 긴급도: {urgency.upper()}
    📝 요약: {issue_summary}
    👤 고객: {context.name}
    📞 매니저 콜백 예상 시간: {callback_time} 이내
    """.strip()


class AgentToolUsageLoggingHooks(AgentHooks):

    async def on_tool_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** starting tool: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
        result: str,
    ):
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** completed tool: `{tool.name}`")
            st.code(result)

    async def on_handoff(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        source: Agent[UserAccountContext],
    ):
        with st.sidebar:
            st.write(f"🔄 Handoff: **{source.name}** → **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
    ):
        with st.sidebar:
            st.write(f"🚀 **{agent.name}** activated")

    async def on_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        output,
    ):
        with st.sidebar:
            st.write(f"🏁 **{agent.name}** completed")
