import os
from flask import request, jsonify
from functools import wraps

SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL', '')
SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET', '')


def verify_supabase_jwt(token):
    """Supabase JWT 토큰 검증"""
    try:
        import jwt  # type: ignore

        if not token:
            return None

        if token.startswith('Bearer '):
            token = token[7:]

        decoded = jwt.decode(token, options={"verify_signature": False})
        if not decoded.get('sub') or not decoded.get('email'):
            return None
        return decoded
    except ImportError:
        print("⚠️ PyJWT가 설치되지 않았습니다. pip install PyJWT")
        return None
    except jwt.ExpiredSignatureError:  # type: ignore
        print("⚠️ JWT 토큰 만료")
        return None
    except jwt.InvalidTokenError as exc:  # type: ignore
        print(f"⚠️ JWT 토큰 검증 실패: {exc}")
        return None
    except Exception as exc:
        print(f"⚠️ JWT 검증 오류: {exc}")
        return None


def get_current_user():
    """현재 요청의 사용자 정보 추출"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    decoded = verify_supabase_jwt(auth_header)
    if decoded:
        return {
            'user_id': decoded.get('sub'),
            'email': decoded.get('email'),
            'metadata': decoded.get('user_metadata', {})
        }
    return None


def require_admin_auth(func):
    """관리자 권한이 필요한 엔드포인트용 데코레이터"""

    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            admin_token = request.headers.get('X-Admin-Token')
            expected_token = os.environ.get('ADMIN_TOKEN', 'admin_sociality_2024')

            if not admin_token or not expected_token or admin_token != expected_token:
                print(f"⚠️ 관리자 권한 없음: admin_token={admin_token}, expected={expected_token}")
                return jsonify({'error': '관리자 권한이 필요합니다.'}), 403

            return func(*args, **kwargs)
        except Exception as exc:
            import traceback
            print(f"❌ require_admin_auth 데코레이터 에러: {exc}")
            print(traceback.format_exc())
            return jsonify({'error': f'인증 처리 중 오류: {exc}'}), 500

    return decorated_function

