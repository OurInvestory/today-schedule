## 🚀 시작하기

1. 저장소 클론 및 이동
```
git clone https://github.com/ibm-ai-hackathon/five-today-schedule.git
cd five-today-schedule/backend
```
</br>

2. 가상 환경 설정 및 패키지 설치
```
# 가상 환경 설정
python -m venv venv

# 가상 환경 활성화
.\venv\Scripts\activate       # Windows
source venv/bin/activate      # Mac/Linux

# 필수 패키치 설치
pip install -r requirements.txt
```
</br>

3. .env 파일 설정 </br>
.env.example 파일을 복사해 .env 파일 생성 및 수정
```
DATABASE_URL=mysql+pymysql://[사용자 이름]:[비밀번호]@localhost:3306/[DB 이름]
```
</br>

4. DB 마이그레이션 (Alembic)
로컬에서 DB 생성 후 테이블 구성
```
alembic upgrade head
```
</br>

5. 서버 실행
서버 실행 후 http://127.0.0.1:8000/ 에 접속해 메시지 확인
```
uvicorn app.main:app --reload
```

## 📂 프로젝트 구조
```
backend/ 
├── app/                 
│   ├── main.py
│   ├── db/            # MySQL 연결
│   ├── models/        # ERD 기반 테이블 설계
│   └── schemas/       # 데이터 검증 모델 (Pydantic)
│   └── api/       
│   └── crud/          # DB 처리 로직
├── .env                 
└── alembic/             
```
