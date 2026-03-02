import streamlit as st
from datetime import datetime
from api import fetch_all_flights
from utils import format_hhmm
from config import KST


# ✅ 5분 캐싱
@st.cache_data(ttl=300)
def _get_flights_cached(date_str: str):
    arrivals = fetch_all_flights("getFltArrivalsDeOdp", date_str)
    departures = fetch_all_flights("getFltDeparturesDeOdp", date_str)
    return arrivals, departures


def render(tab, today, now, min_date, max_date):
    with tab:
        st.markdown(f"현재: **{now.strftime('%Y-%m-%d %H:%M')}** (KST)")

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            search_date = st.date_input(
                "조회 날짜",
                value=today,
                min_value=min_date,
                max_value=max_date,
                key="gate_date",
            )

        with col2:
            search_time = st.time_input(
                "기준 시간",
                value=now.time().replace(second=0, microsecond=0),
                key="gate_time",
            )

        with col3:
            gate_input = st.text_input(
                "게이트(주기장) 번호",
                placeholder="예: 43, 123 ...",
                key="gate_input",
            )

        gate_value = gate_input.strip().upper()

        if st.button("🔍 조회", type="primary", key="gate_search"):

            # ✅ 입력 검증 최소화
            if not gate_value:
                st.warning("게이트 번호를 입력해주세요.")
                return

            if not gate_value.isdigit():
                st.warning("게이트 번호는 숫자만 입력 가능합니다.")
                return

            search_date_str = search_date.strftime("%Y%m%d")
            cutoff = datetime.combine(search_date, search_time).replace(tzinfo=KST)

            # ✅ 캐싱된 API 호출
            with st.spinner("운항 데이터 조회 중..."):
                arrivals, departures = _get_flights_cached(search_date_str)

            nearest = None
            nearest_time = None
            future_flights = []

            # ✅ 단일 루프 처리 함수
            def process(flights, flight_type):
                nonlocal nearest, nearest_time

                for item in flights:

                    if item.get("codeshare") != "Master":
                        continue

                    if (item.get("gate_number") or "").strip().upper() != gate_value:
                        continue

                    scheduled = item.get("scheduled_datetime")
                    if not scheduled or scheduled == "-":
                        continue

                    try:
                        parsed = datetime.strptime(
                            str(scheduled).strip(), "%Y%m%d%H%M"
                        ).replace(tzinfo=KST)
                    except ValueError:
                        continue

                    if parsed < cutoff:
                        continue

                    new_item = item.copy()
                    new_item["_flight_type"] = flight_type
                    new_item["_parsed_time"] = parsed

                    future_flights.append(new_item)

                    # ✅ 최근편 즉시 갱신 (정렬 불필요)
                    if nearest_time is None or parsed < nearest_time:
                        nearest = new_item
                        nearest_time = parsed

            # arrivals / departures 한 번씩만 순회
            process(arrivals, "A")
            process(departures, "D")

            # ✅ 결과 없음
            if not future_flights:
                st.info(f"게이트 **{gate_value}** 에 기준 시간 이후 운항편이 없습니다.")
                return

            # ✅ 가장 가까운 항공편 먼저 렌더
            _render_main_card(nearest, gate_value)

            # ✅ 이후 편 정렬은 필요할 때만
            if len(future_flights) > 1:
                st.markdown(f"**이후 운항 예정 ({len(future_flights) - 1}건)**")

                # nearest 제외 후 정렬
                others = [f for f in future_flights if f is not nearest]
                others.sort(key=lambda x: x["_parsed_time"])

                for item in others:
                    _render_flight_row(item)

        st.markdown(
            '<div class="gate-caption">게이트 번호 숫자로만 검색하세요</div>',
            unsafe_allow_html=True,
        )
