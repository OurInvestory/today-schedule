from dotenv import load_dotenv
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# .env 파일 로드
load_dotenv()   
DATABASE_URL = os.getenv("DATABASE_URL")


# DB 연결 엔진 생성
engine = create_engine(DATABASE_URL)

# DB 세션 클래스 생성
db_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# 모델 base 클래스 생성
Base = declarative_base()


# 의존성 주입
def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()