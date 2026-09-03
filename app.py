from datetime import datetime, time, timedelta
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

from model.risk_level import (
    get_all_age_level,
    get_elderly_level,
    get_outdoor_guidance,
)


# 파일 위치를 기준으로 경로를 정하면 다른 폴더에서 실행해도 파일을 찾을 수 있음
BASE_DIR = Path(__file__).resolve().parent
MODEL_INFO = {
    "전체 연령": {
        "file": "heat_patient_model.pkl",
        "csv": "train_dataset.csv",
        "target": "total_patients",
        "level_function": get_all_age_level,
        "bounds": [3, 9, 30],
        "r2": 0.846, "mae": 9.700, "rmse": 14.871,
    },
    "65세 이상": {
        "file": "heat_patient_elderly65_model.pkl",
        "csv": "train_dataset_elderly65_2022_2025.csv",
        "target": "elderly_patients",
        "level_function": get_elderly_level,
        "bounds": [1, 3, 8],
        "r2": 0.837, "mae": 3.209, "rmse": 4.917,
    },
}

st.set_page_config(page_title="온열질환 예측과 외출 안내", page_icon="☀️", layout="wide")


# 화면 입력이 바뀔 때마다 모델을 다시 읽지 않도록 캐시에 보관
@st.cache_resource
def load_model(filename):
    return joblib.load(BASE_DIR / "model" / "saved" / filename)


@st.cache_data
def load_data(filename):
    data = pd.read_csv(BASE_DIR / "data" / "processed" / filename)
    data["일시"] = pd.to_datetime(data["일시"])
    return data


st.caption("HEAT CARE · 온열질환 데이터 프로젝트")
st.title("☀️ 오늘의 기상 조건, 어떻게 해석할까요?")
st.write("기상 조건으로 전국 하루 예상 환자 수를 살펴보고, 외출 일정에 맞는 안내를 확인하세요.")
st.caption("수동 입력 시뮬레이션입니다. 실시간 날씨·폭염특보와 연결되어 있지 않습니다.")

with st.sidebar:
    st.header("예측 대상")
    target = st.radio("어떤 대상을 살펴볼까요?", list(MODEL_INFO), key="target")
    st.caption("전체 연령에는 65세 이상도 포함됩니다. 두 모델의 환자 수를 더하지 않습니다.")
    st.divider()
    st.subheader("이용 순서")
    st.write("① 대상 선택\n\n② 기상·외출 정보 입력\n\n③ 예측 결과와 해석 확인")
    st.info("등급은 과거 데이터 안에서의 상대적 수준입니다. 개인의 외출 안전을 판정하지 않습니다.")

info = MODEL_INFO[target]
try:
    bundle = load_model(info["file"])
    data = load_data(info["csv"])
    model = bundle["model"]
    weather_columns = bundle["weather_columns"]
except Exception as error:
    st.error(f"모델 또는 데이터를 불러오지 못했습니다: {error}")
    st.stop()

if target == "65세 이상":
    st.warning("고령자 자료는 잠정 데이터입니다. 원본과 기존 연보의 2022~2024년 합계 차이는 원인 미확인 상태입니다.")

prediction_tab, model_tab, data_tab = st.tabs(["예측과 해석", "모델 정보", "데이터 분석"])

with prediction_tab:
    input_col, result_col = st.columns([1, 1.2], gap="large")

    with input_col:
        st.subheader("01 · 입력 정보")
        st.caption("기상값은 전국 관측소의 일별 평균 기준입니다. 한 지역의 현재 날씨와는 다릅니다.")

        # 초기값은 실제 과거 하루의 값. 서로 무관한 임의의 기상값을 조합하지 않음
        sample = data.loc[data["일시"] == "2025-08-01"].iloc[0]
        st.caption("초기 기상값: 2025-08-01 관측 자료 예시 · 현재 날씨 아님")
        weather = {}
        weather_cols = st.columns(2)
        for index, column in enumerate(weather_columns):
            with weather_cols[index % 2]:
                # 기온 이외 변수는 음수가 될 수 없도록 입력 범위 지정
                minimum = -50.0 if "기온" in column else 0.0
                maximum = 100.0 if "습도" in column else (24.0 if "일조" in column else None)
                weather[column] = st.number_input(
                    column, min_value=minimum, max_value=maximum,
                    value=round(float(sample[column]), 2), step=0.1,
                    key=f"weather_{index}",
                )

        st.markdown("**외출 계획**")
        time_col, duration_col = st.columns(2)
        with time_col:
            start = st.time_input("외출 시작 시간", value=time(11, 30), key="start")
        with duration_col:
            duration = st.number_input("야외 체류시간 (분)", min_value=0, max_value=1440,
                                       value=120, step=30, key="duration")
        st.caption("외출 시간은 안내에만 사용하며, 환자 수 예측의 입력에는 포함되지 않습니다.")

        # 현재 입력과 결과를 묶어서 보관. 입력이 바뀌면 이전 결과는 지움
        signature = (target, tuple(weather.values()), start.isoformat(), duration)
        previous = st.session_state.get("result")
        if previous and previous["signature"] != signature:
            st.session_state.pop("result")

        temperature_ok = weather["최저기온(°C)"] <= weather["평균기온(°C)"] <= weather["최고기온(°C)"]
        if not temperature_ok:
            st.error("기온은 최저 ≤ 평균 ≤ 최고 순서로 입력해 주세요.")

        if st.button("예측하고 해석 보기", type="primary", width="stretch", disabled=not temperature_ok):
            # 저장할 때 보관한 이름과 순서로 기상 입력 8개를 정렬
            input_data = pd.DataFrame([weather], columns=weather_columns)
            prediction = float(model.predict(input_data)[0])
            # 반올림하기 전 예측값으로 등급을 정함
            level = info["level_function"](prediction)
            start_hour = start.hour + start.minute / 60
            messages = get_outdoor_guidance(target, level, start_hour, duration)
            st.session_state.result = {
                "signature": signature, "prediction": prediction,
                "level": level, "messages": messages,
            }

    with result_col:
        st.subheader("02 · 예측 결과")
        result = st.session_state.get("result")
        if result is None:
            st.info("왼쪽에서 입력을 확인하고 ‘예측하고 해석 보기’를 눌러 주세요.")
            st.write("결과에는 **예상 환자 수 · 상대적 등급 · 결과 해석 · 외출 안내**가 표시됩니다.")
        else:
            with st.container(border=True):
                count_col, level_col = st.columns(2)
                count_col.metric(f"{target} 전국 하루 예상 환자 수", f"{result['prediction']:.1f}명")
                level_col.metric("예측 환자 수의 상대적 등급", result["level"])
                st.caption("표시는 소수 첫째 자리까지, 등급 판단은 반올림 전 값으로 계산합니다.")

            # 사용자가 예측값의 의미를 읽을 수 있도록 기본 펼침 상태
            with st.expander("📖 결과 해석", expanded=True):
                st.write(
                    f"입력한 전국 일별 기상 조건에서 **{target}의 하루 환자 수는 "
                    f"약 {result['prediction']:.1f}명**으로 예상됩니다. "
                    "2022~2025년 데이터로 학습한 모델이 계산한 값입니다."
                )
                a, b, c = info["bounds"]
                st.write(f"이 대상의 경계는 **{a}·{b}·{c}명**이며, 예측값은 **‘{result['level']}’** 구간에 속합니다.")
                st.write("이는 전국 단위 예상 발생 규모입니다. 개인의 발병 확률이나 해당 지역의 환자 수를 뜻하지 않습니다.")
                st.caption(f"기록된 무작위 분할 평가: MAE {info['mae']:.3f}명, RMSE {info['rmse']:.3f}명. "
                           "평가 오차를 요약한 수치이며 이번 예측의 ±오차 범위는 아닙니다.")

            outside_range = [column for column in weather_columns
                             if not data[column].min() <= weather[column] <= data[column].max()]
            if outside_range:
                st.warning("과거 학습 자료의 관측 범위를 벗어난 입력: " + ", ".join(outside_range))

            st.subheader("03 · 외출 계획에 맞는 안내")
            end = datetime.combine(datetime(2025, 1, 1).date(), start) + timedelta(minutes=duration)
            next_day = "다음 날 " if end.day > 1 else ""
            st.caption(f"{start:%H:%M} → {next_day}{end:%H:%M} · 야외 체류 {duration}분")
            for message in result["messages"]:
                st.write(f"• {message}")
            st.caption("외출 내내 야외에 머무는 일정으로 계산합니다.")
            st.markdown("[안내 근거: 질병관리청 온열질환 예방수칙](https://kdca.go.kr/bbs/kdca/46/306747/download.do)")

with model_tab:
    st.subheader(f"{target} · Random Forest 회귀 모델")
    st.caption("아래 수치는 HANDOFF.md에 기록된 무작위 80:20 분할 평가 결과입니다. 앱에서 재학습하지 않습니다.")
    metrics = st.columns(3)
    metrics[0].metric("결정계수 R²", f"{info['r2']:.3f}")
    metrics[1].metric("평균 절대 오차 MAE", f"{info['mae']:.3f}명")
    metrics[2].metric("제곱근 평균 제곱 오차 RMSE", f"{info['rmse']:.3f}명")
    st.write("**R²**는 환자 수 변동을 설명하는 정도이며 정확도가 아닙니다. "
             "**MAE**는 실제값과 예측값 차이의 절댓값 평균, **RMSE**는 큰 오차를 더 크게 반영한 지표입니다.")
    st.caption("연도별 보조 평가는 분할·튜닝 조건이 달라 위 결과와 직접 비교하지 않습니다.")
    a, b, c = info["bounds"]
    st.dataframe(pd.DataFrame({"등급": ["낮음", "보통", "높음", "매우 높음"],
                              "예측 환자 수": [f"{a}명 미만", f"{a}명 이상 ~ {b}명 미만",
                                          f"{b}명 이상 ~ {c}명 미만", f"{c}명 이상"]}), hide_index=True)
    importance = pd.DataFrame({"기상 변수": weather_columns, "중요도": model.feature_importances_})
    fig = px.bar(importance.sort_values("중요도"), x="중요도", y="기상 변수", orientation="h",
                 title="모델이 예측에 활용한 변수 중요도", color_discrete_sequence=["#168a8a"])
    fig.update_layout(margin=dict(l=0, r=10, t=45, b=0), height=350)
    st.plotly_chart(fig, width="stretch")
    st.caption("중요도는 모델 전체의 특성이며, 이번 예측의 원인이나 인과관계를 설명하지 않습니다.")

with data_tab:
    st.subheader(f"{target} · 과거 데이터 살펴보기")
    st.caption(f"2022~2025년 감시기간 {len(data)}일 · 실제 학습 CSV 기준")
    scatter_col, distribution_col = st.columns(2)
    with scatter_col:
        fig = px.scatter(data, x="최고기온(°C)", y=info["target"],
                         labels={info["target"]: "실제 일일 환자 수 (명)"},
                         title="전국 평균 최고기온과 실제 환자 수", opacity=0.55,
                         color_discrete_sequence=["#168a8a"])
        st.plotly_chart(fig, width="stretch")
    with distribution_col:
        fig = px.histogram(data, x=info["target"], nbins=30,
                           labels={info["target"]: "실제 일일 환자 수 (명)"},
                           title="하루 환자 수의 분포", color_discrete_sequence=["#eea64a"])
        fig.update_yaxes(title="날짜 수")
        st.plotly_chart(fig, width="stretch")
    st.caption("점 하나는 하루입니다. 그래프는 과거 실제 자료이며 현재 예측 결과가 아닙니다.")
    with st.expander("통계와 원본 행 보기"):
        st.dataframe(data[[info["target"]] + weather_columns].describe(), width="stretch")
        st.dataframe(data, hide_index=True, width="stretch")
