# 온열질환자 수 예측 웹 화면

기존 Streamlit 화면과 별도로 실행하는 Next.js 대시보드입니다. 기존 데이터, 학습 모델, 기상 API 코드는 읽어서 사용하며 원본 Python 파일은 수정하지 않습니다.

## 실행 방법

프로젝트 루트에 Python 가상환경과 모델 파일이 준비되어 있어야 합니다.

```powershell
cd C:\puh\heatwave-risk-ml\web
npm install
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열면 됩니다.

## 화면 구성

- 전국 하루 평균 기상정보 기반 예상 환자 수
- 선택 도시와 외출 시간대 기상정보 기반 참고 예측
- 선택 지역의 기온, 습도, 풍속, 강수량과 폭염특보 표시
- 전체 연령과 65세 이상 모델 성능 비교
- 학습 데이터 추이, 기온과 환자 수 관계, 변수 중요도 차트

## 내부 연결

Next.js API Route가 `web/scripts`의 Python 스크립트를 실행합니다. 스크립트는 프로젝트 루트의 `.venv`, `model/saved`, `data/processed`, `weather_api.py`를 사용합니다. 기상청 특보 키는 기존 `.streamlit/secrets.toml`의 `KMA_API_KEY` 값을 읽습니다.

운영 빌드는 다음 명령으로 확인할 수 있습니다.

```powershell
npm run build
npm start
```
