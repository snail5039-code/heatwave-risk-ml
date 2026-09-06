"""Next.js 로컬 화면에서 기존 Python 예측 코드를 호출하기 위한 연결 스크립트."""

import argparse
import json
import sys
import tomllib
from datetime import date
from pathlib import Path

import joblib
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from model.risk_level import (  # noqa: E402
    get_all_age_level,
    get_elderly_level,
    get_outdoor_guidance,
)
from weather_api import (  # noqa: E402
    get_city_outing_weather,
    get_heatwave_warning,
    get_national_weather,
)


def load_kma_key():
    secrets_path = ROOT_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return ""

    with secrets_path.open("rb") as secrets_file:
        return str(tomllib.load(secrets_file).get("KMA_API_KEY", "")).strip()


def serializable_weather(weather):
    return {key: float(value) for key, value in weather.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=["전체 연령", "65세 이상"])
    parser.add_argument("--date", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--start-hour", required=True, type=int)
    parser.add_argument("--duration", required=True, type=int)
    args = parser.parse_args()

    selected_date = date.fromisoformat(args.date)
    model_filename = (
        "heat_patient_model.pkl"
        if args.target == "전체 연령"
        else "heat_patient_elderly65_model.pkl"
    )
    model_data = joblib.load(ROOT_DIR / "model" / "saved" / model_filename)
    model = model_data["model"]
    weather_columns = model_data["weather_columns"]

    national_weather = get_national_weather(selected_date)
    city_weather = get_city_outing_weather(
        selected_date,
        args.city,
        args.start_hour,
        args.duration,
    )

    national_input = pd.DataFrame([national_weather])[weather_columns]
    city_input = pd.DataFrame([city_weather])[weather_columns]
    national_prediction = float(model.predict(national_input)[0])
    city_prediction = float(model.predict(city_input)[0])

    level_function = get_all_age_level if args.target == "전체 연령" else get_elderly_level
    national_level = level_function(national_prediction)
    city_level = level_function(city_prediction)
    guidance = get_outdoor_guidance(
        args.target,
        city_level,
        args.start_hour,
        args.duration,
    )
    warning = get_heatwave_warning(
        load_kma_key(),
        args.city,
        selected_date,
    )

    print(json.dumps({
        "target": args.target,
        "date": args.date,
        "city": args.city,
        "startHour": args.start_hour,
        "durationMinutes": args.duration,
        "national": {
            "prediction": national_prediction,
            "level": national_level,
            "weather": serializable_weather(national_weather),
        },
        "cityResult": {
            "prediction": city_prediction,
            "level": city_level,
            "weather": serializable_weather(city_weather),
        },
        "guidance": guidance,
        "warning": warning,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
