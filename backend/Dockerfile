FROM python:3.11.9-slim

WORKDIR /app

# 시스템 패키지 설치 (MySQL, OCR용 OpenCV 의존성)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 설치 (캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "fastapi[standard]"

# 소스 코드 복사 (개발 모드에서는 volume으로 마운트되므로 생략 가능)
COPY . .

# 시작 스크립트 실행 권한 부여
RUN chmod +x /app/start.sh

EXPOSE 8000

# 개발 모드: DB 연결 대기 후 마이그레이션 실행 후 서버 시작
CMD ["/bin/bash", "/app/start.sh"]