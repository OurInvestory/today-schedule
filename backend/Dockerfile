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

EXPOSE 8000

# 개발 모드: --reload 옵션으로 코드 변경 시 자동 재시작
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]