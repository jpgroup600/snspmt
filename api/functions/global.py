

#전역 오류 처리 
@app.errorhandler(404)
def not_found(error):
    import sys
    import traceback
    # 사용자 정보 조회 라우트는 404를 반환하지 않음
    if request.path.startswith('/api/users/'):
        # /api/users/ 이후의 모든 경로를 user_id로 추출
        user_id = request.path.replace('/api/users/', '', 1).rstrip('/')
        print(f"🔍 404 핸들러에서 사용자 정보 조회 시도 - 경로: {request.path}, user_id: {user_id}", flush=True)
        sys.stdout.flush()
        try:
            # 직접 get_user 함수 호출
            result = get_user(user_id)
            print(f"✅ 404 핸들러에서 get_user 호출 성공 - user_id: {user_id}", flush=True)
            sys.stdout.flush()
            return result
        except Exception as e:
            error_msg = f"❌ 404 핸들러에서 get_user 호출 실패: {e}"
            print(error_msg, file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            # 최소한 기본 사용자 정보라도 반환
            return jsonify({
                'user_id': user_id,
                'email': None,
                'name': None,
                'created_at': None,
                'message': '사용자 정보를 조회할 수 없습니다.'
            }), 200
    print(f"❌ 404 오류 - 경로: {request.path}, 메서드: {request.method}", flush=True)
    sys.stdout.flush()
    return jsonify({'error': 'Not Found', 'message': '요청한 리소스를 찾을 수 없습니다.'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': '서버 내부 오류가 발생했습니다.'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # 오류 로깅
    print(f"❌ 전역 오류 발생: {str(e)}")
    import traceback
    print(f"❌ 스택 트레이스: {traceback.format_exc()}")
    
    # MethodNotAllowed 오류에 대한 특별 처리
    if hasattr(e, 'code') and e.code == 405:
        print(f"❌ 405 Method Not Allowed: {request.method} {request.path}")
        return jsonify({
            'error': 'Method not allowed',
            'message': f'{request.method} method is not allowed for {request.path}',
            'type': 'MethodNotAllowed'
        }), 405
    
    # 프로덕션 환경에서는 상세 오류 정보 숨김
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Internal Server Error', 'message': '서버 오류가 발생했습니다.'}), 500
    else:
        return jsonify({'error': str(e), 'message': '개발 환경 오류'}), 500
    
    

# 필수 환경 변수 검증
def validate_environment():
    """환경 변수 검증"""
    required_vars = {
        'DATABASE_URL': DATABASE_URL,
        'SMMPANEL_API_KEY': SMMPANEL_API_KEY
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        error_msg = f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # 보안 검증
    if SMMPANEL_API_KEY == 'bc85538982fb27c6c0558be6cd669e67':
        print("⚠️ 기본 API 키를 사용하고 있습니다. 프로덕션에서는 다른 키를 사용하세요.")
    
    print("✅ 환경 변수 검증 완료")