"""Next.js 데이터 분석 탭에 기존 학습 자료를 전달한다."""

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=["전체 연령", "65세 이상"])
    args = parser.parse_args()

    if args.target == "전체 연령":
        csv_path = ROOT_DIR / "data" / "processed" / "train_dataset.csv"
        patient_column = "total_patients"
        model_path = ROOT_DIR / "model" / "saved" / "heat_patient_model.pkl"
    else:
        csv_path = ROOT_DIR / "data" / "processed" / "train_dataset_elderly65_2022_2025.csv"
        patient_column = "elderly_patients"
        model_path = ROOT_DIR / "model" / "saved" / "heat_patient_elderly65_model.pkl"

    data = pd.read_csv(csv_path)
    model_data = joblib.load(model_path)
    model = model_data["model"]
    columns = model_data["weather_columns"]

    time_series = [
        {"date": str(row["일시"]), "patients": int(row[patient_column])}
        for _, row in data.iterrows()
    ]
    scatter = [
        {"temperature": float(row["최고기온(°C)"]), "patients": int(row[patient_column])}
        for _, row in data.iterrows()
    ]
    importance = [
        {"feature": column.replace("평균 ", "").replace("합계 ", ""), "value": float(value)}
        for column, value in zip(columns, model.feature_importances_)
    ]

    print(json.dumps({
        "target": args.target,
        "rowCount": int(len(data)),
        "timeSeries": time_series,
        "scatter": scatter,
        "importance": importance,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
