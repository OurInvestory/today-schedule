"""
Prometheus 메트릭 수집 및 모니터링
- API 응답 시간
- 요청 횟수
- DB 쿼리 성능
- 캐시 히트율
"""

import time
from typing import Callable
from functools import wraps

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess, REGISTRY
)
from starlette.middleware.base import BaseHTTPMiddleware


# =========================================================
# 메트릭 정의
# =========================================================

# HTTP 요청 카운터
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# HTTP 요청 지연 시간
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 활성 요청 수
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# DB 쿼리 시간
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# DB 쿼리 카운터
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

# 캐시 히트/미스
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']  # operation: get/set, result: hit/miss
)

# 캐시 응답 시간
cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05]
)

# AI API 호출
ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['model', 'operation', 'status']
)

# AI API 응답 시간
ai_api_duration_seconds = Histogram(
    'ai_api_duration_seconds',
    'AI API call duration in seconds',
    ['model', 'operation'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

# 활성 사용자 수
active_users = Gauge(
    'active_users',
    'Number of active users in the last hour'
)

# Celery 태스크
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

# 애플리케이션 정보
app_info = Info('app', 'Application information')


# =========================================================
# 미들웨어
# =========================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """HTTP 요청 메트릭 수집 미들웨어"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = request.url.path
        
        # 메트릭 엔드포인트는 제외
        if path == "/metrics":
            return await call_next(request)
        
        # 경로 정규화 (ID 등 동적 부분 제거)
        endpoint = self._normalize_path(path)
        
        # 진행 중 요청 증가
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # 시간 측정 시작
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            # 소요 시간 기록
            duration = time.time() - start_time
            
            # 메트릭 기록
            http_requests_total.labels(
                method=method, 
                endpoint=endpoint, 
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)
            
            # 진행 중 요청 감소
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """경로 정규화 (UUID 등 동적 부분 제거)"""
        import re
        
        # UUID 패턴
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        path = re.sub(uuid_pattern, '{id}', path)
        
        # 숫자 ID
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path


# =========================================================
# 데코레이터
# =========================================================

def track_db_query(operation: str, table: str):
    """DB 쿼리 메트릭 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_queries_total.labels(operation=operation, table=table).inc()
                db_query_duration_seconds.labels(
                    operation=operation, 
                    table=table
                ).observe(duration)
        return wrapper
    return decorator


def track_cache_operation(operation: str):
    """캐시 작업 메트릭 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 히트/미스 판단 (get 작업의 경우)
            if operation == "get":
                cache_result = "hit" if result is not None else "miss"
            else:
                cache_result = "success"
            
            cache_operations_total.labels(
                operation=operation, 
                result=cache_result
            ).inc()
            cache_operation_duration_seconds.labels(operation=operation).observe(duration)
            
            return result
        return wrapper
    return decorator


def track_ai_call(model: str, operation: str):
    """AI API 호출 메트릭 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                ai_api_calls_total.labels(
                    model=model, 
                    operation=operation, 
                    status=status
                ).inc()
                ai_api_duration_seconds.labels(
                    model=model, 
                    operation=operation
                ).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                ai_api_calls_total.labels(
                    model=model, 
                    operation=operation, 
                    status=status
                ).inc()
                ai_api_duration_seconds.labels(
                    model=model, 
                    operation=operation
                ).observe(duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def track_celery_task(task_name: str):
    """Celery 태스크 메트릭 데코레이터"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                celery_tasks_total.labels(
                    task_name=task_name, 
                    status=status
                ).inc()
        return wrapper
    return decorator


# =========================================================
# FastAPI 설정
# =========================================================

def setup_prometheus(app: FastAPI):
    """Prometheus 메트릭 설정"""
    
    # 애플리케이션 정보 설정
    app_info.info({
        'version': '1.0.0',
        'name': '5늘의 일정',
        'environment': 'production'
    })
    
    # 미들웨어 추가
    app.add_middleware(PrometheusMiddleware)
    
    # 메트릭 엔드포인트
    @app.get("/metrics")
    async def metrics():
        """Prometheus 메트릭 엔드포인트"""
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    
    return app


# =========================================================
# 헬스체크
# =========================================================

async def health_check() -> dict:
    """시스템 헬스체크"""
    from app.db.database import engine
    from app.core.cache import cache_service
    
    health = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # DB 체크
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Redis 체크
    try:
        if cache_service.is_available:
            health["checks"]["redis"] = "healthy"
        else:
            health["checks"]["redis"] = "unavailable"
    except Exception as e:
        health["checks"]["redis"] = f"unhealthy: {str(e)}"
    
    return health
