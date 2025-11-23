import os
import time
from functools import wraps


def get_parameter_value(key: str, default: str = "") -> str:
    """AWS SSM 유틸을 흉내 내는 환경 변수 조회."""
    try:
        return os.getenv(key, default)
    except Exception:
        return default


def monitor_performance(func):
    """함수 실행 시간을 로깅하는 데코레이터."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            if duration > 1.0:
                print(f"🐌 느린 함수 감지: {func.__name__} - {duration:.3f}s")
            return result
        except Exception as exc:
            duration = time.time() - start_time
            print(f"❌ 함수 실행 실패: {func.__name__} - {duration:.3f}s - {exc}")
            raise

    return wrapper

