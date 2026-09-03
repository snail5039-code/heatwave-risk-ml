# 기상 조건 기반 온열질환자 수 예측

2022~2025년 기상 자료로 전국 일일 온열질환자 수를 예측합니다.
기존 전체 연령 모델과 65세 이상 모델을 별도로 관리합니다.

## 폴더 안내

```text
analysis/                 EDA 코드
model/                    학습·평가·예측 코드
  saved/                  전체 연령·65세 이상 저장 모델
data/
  raw/
    2022/ ~ 2025/         연도별 원본 XLS·PDF·기상 CSV
    heat_illness_cases_2011_2025.csv  여러 연도 신고 원본
  processed/              일별 집계·학습 CSV·가공 기록
docs/
  기획/                   주제 선정 HWPX·PDF와 초기 기획 메모
  분석보고서/             통합 보고서·모델별 보고서
    그래프/전체연령/      전체 연령 그래프 PNG 6개
    그래프/65세이상/      고령자 그래프 PNG 6개
  화면설계/               Streamlit 화면 시안
steps/                    단계별 학습 안내
plan.md                   전체 계획
HANDOFF.md                인수인계 기록
```

## 보고서

- [통합 분석 보고서](docs/분석보고서/00_통합_분석보고서.hwpx)
- [전체 연령 모델 보고서](docs/분석보고서/01_전체연령_모델_분석보고서.hwpx)
- [65세 이상 모델 보고서](docs/분석보고서/02_65세이상_모델_분석보고서.hwpx)
- [그래프 안내](docs/분석보고서/README.md)

## 학습 데이터와 모델

| 대상 | 학습 CSV (`data/processed`) | 저장 모델 (`model/saved`) |
| --- | --- | --- |
| 전체 연령 | `train_dataset.csv` | `heat_patient_model.pkl` |
| 65세 이상 | `train_dataset_elderly65_2022_2025.csv` | `heat_patient_elderly65_model.pkl` |

두 학습 자료는 각각 536일이며, 입력은 기상 변수 8개입니다.
`cases`는 개별 신고 기록, `daily`는 날짜별 집계, `train_dataset`은 기상값을 결합한 학습 자료입니다.

두 모델의 학습·저장과 주요 EDA, 모델별 등급 변환, 외출 안내 및 Streamlit 초안을 완료했습니다.
`app.py`에서 예측·결과 해석·모델 정보·데이터 분석을 확인할 수 있습니다.
현재는 기상값을 수동 입력하며, 초기값은 과거 자료 예시입니다. 실시간 날씨 API는 아직 연결하지 않았습니다.
다음에는 사용자가 한 단계씩 직접 구현하며 기상 API 자동 수집을 연결할 예정입니다.

## 실행 위치

모든 Python 코드는 프로젝트 루트에서 실행합니다.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

검증 환경은 Python 3.13입니다. 저장 모델은 requirements.txt의 scikit-learn 버전으로 로드했습니다.

학습 스크립트는 실행 시 재학습하거나 저장 모델을 덮어쓸 수 있으므로 필요한 경우에만 실행합니다.

## 자료 해석

고령자 공개 원본과 공식 연보는 2022~2024년 합계가 다르며 원인은 미확인입니다.
신고 기록을 임의로 삭제하거나 합계를 조정하지 않았습니다.
모델 출력은 전국 신고 환자 수 예측이며 개인 발병 확률이나 외출 안전 판정이 아닙니다.

자료 출처: 질병관리청 온열질환 응급실감시체계, 기상청 ASOS 일자료.
고령자 원본: https://www.data.go.kr/data/15149889/fileData.do
