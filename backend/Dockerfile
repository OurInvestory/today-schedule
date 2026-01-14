FROM python:3.11.9-slim

WORKDIR /app

# 시스템 패키지 설치 (MySQL, OCR용 OpenCV 의존성)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "fastapi[standard]"


COPY . .

EXPOSE 8000

# Ensure the server runs on 0.0.0.0 and port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]