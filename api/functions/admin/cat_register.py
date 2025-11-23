import os
import json
import re
import sys
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "psycopg2 is required. Install it with `uv pip install -r requirements.txt` "
        "or `pip install psycopg2-binary` before running the server."
    ) from exc
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta 
import requests
import tempfile
import sqlite3
import threading
import time
from werkzeug.utils import secure_filename
from flask import send_from_directory
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote
from flasgger.utils import swag_from
from services import (
    get_parameter_value,
    get_current_user,
    monitor_performance,
    require_admin_auth,
    verify_supabase_jwt,
)

@require_admin_auth
def admin_import_smm_services():
    """
    ---
    SMM Panel 서비스 목록을 불러와 categories/products/product_variants에 일괄 등록"""
    # CORS preflight 요청 처리
    if request.method == 'OPTIONS':
        return '', 200
    
    conn = None
    cursor = None
    try:
        print("🔍 SMM 서비스 동기화 시작")
        
        # 1) SMM 서비스 목록 가져오기
        smm = get_smm_panel_services()
        if not smm or smm.get('status') != 'success':
            error_msg = 'SMM 서비스 목록을 불러오지 못했습니다.'
            print(f"❌ {error_msg}: {smm}")
            return jsonify({'error': error_msg, 'details': smm}), 502
        services = smm.get('services', [])
        if not services:
            error_msg = 'SMM 서비스가 비어있습니다.'
            print(f"❌ {error_msg}")
            return jsonify({'error': error_msg}), 404
        
        print(f"✅ SMM 서비스 {len(services)}개 불러옴")
        
        # 2) DB 연결
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 3) 카테고리/상품 준비 (없으면 생성)
        category_name = 'SMM 패널'
        product_name = 'SMM 기본 서비스'
        
        cursor.execute("SELECT category_id FROM categories WHERE name = %s LIMIT 1", (category_name,))
        cat = cursor.fetchone()
        if not cat:
            cursor.execute("""
                INSERT INTO categories (name, description, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
                RETURNING category_id
            """, (category_name, 'SMM Panel에서 자동 동기화된 카테고리'))
            cat = cursor.fetchone()
            print(f"➕ 카테고리 생성: {category_name} (ID: {cat['category_id']})")
        category_id = cat['category_id']
        
        cursor.execute("""
            SELECT product_id FROM products 
            WHERE name = %s AND category_id = %s
            LIMIT 1
        """, (product_name, category_id))
        prod = cursor.fetchone()
        if not prod:
            cursor.execute("""
                INSERT INTO products (category_id, name, description, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, TRUE, NOW(), NOW())
                RETURNING product_id
            """, (category_id, product_name, 'SMM Panel 서비스 묶음'))
            prod = cursor.fetchone()
            print(f"➕ 상품 생성: {product_name} (ID: {prod['product_id']})")
        product_id = prod['product_id']
        
        # 4) 서비스별로 variant upsert
        import json as json_module
        inserted, updated = 0, 0
        for s in services:
            svc_id = s.get('service') or s.get('id') or s.get('service_id')
            name = s.get('name') or f"Service {svc_id}"
            price = None
            # rate, pricePer1000 등 가능한 필드에서 가격 추출
            for key in ['rate', 'price', 'pricePer1000', 'cost']:
                if s.get(key) not in (None, '', 0):
                    try:
                        price = float(s.get(key))
                        break
                    except:
                        pass
            if price is None:
                price = 0.0
            min_q = int(s.get('min') or s.get('min_quantity') or 1)
            max_q = int(s.get('max') or s.get('max_quantity') or max(1, min_q))
            delivery = s.get('dripfeed') or s.get('delivery_time_days') or None
            
            # 기존 variant 존재 여부 확인 (product_id + meta_json.service_id 기준)
            cursor.execute("""
                SELECT variant_id FROM product_variants 
                WHERE product_id = %s 
                  AND (meta_json->>'service_id') = %s
                LIMIT 1
            """, (product_id, str(svc_id)))
            existing = cursor.fetchone()
            
            meta_json = json_module.dumps({
                'service_id': str(svc_id),
                'raw': s
            }, ensure_ascii=False)
            
            if existing:
                cursor.execute("""
                    UPDATE product_variants
                    SET name = %s,
                        price = %s,
                        min_quantity = %s,
                        max_quantity = %s,
                        delivery_time_days = %s,
                        meta_json = %s::jsonb,
                        is_active = TRUE,
                        updated_at = NOW()
                    WHERE variant_id = %s
                """, (name, price, min_q, max_q, delivery, meta_json, existing['variant_id']))
                updated += 1
            else:
                cursor.execute("""
                    INSERT INTO product_variants (
                        product_id, name, price, min_quantity, max_quantity,
                        delivery_time_days, is_active, meta_json, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s::jsonb, NOW(), NOW())
                    RETURNING variant_id
                """, (product_id, name, price, min_q, max_q, delivery, meta_json))
                _ = cursor.fetchone()
                inserted += 1
        
        conn.commit()
        print(f"✅ SMM 동기화 완료: 추가 {inserted}건, 갱신 {updated}건")
        return jsonify({
            'success': True,
            'inserted': inserted,
            'updated': updated,
            'message': f'동기화 완료: 추가 {inserted}건, 갱신 {updated}건'
        }), 200
    except Exception as e:
        if conn:
            conn.rollback()
        import traceback
        error_msg = f'SMM 동기화 실패: {str(e)}'
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
            
# 멈춰있는 패키지 주문 재처리
@require_admin_auth
def reprocess_package_orders():
    """멈춰있는 패키지 주문들을 재처리"""
    conn = None
    cursor = None
    
    try:
        print("🔄 관리자 요청: 멈춰있는 패키지 주문 재처리")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # package_processing 상태인 주문들을 pending으로 변경
        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("""
                UPDATE orders SET status = 'pending' 
                WHERE status = 'package_processing' AND package_steps IS NOT NULL
            """)
        else:
            cursor.execute("""
                UPDATE orders SET status = 'pending' 
                WHERE status = 'package_processing' AND package_steps IS NOT NULL
            """)
        
        updated_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ {updated_count}개의 패키지 주문 상태를 pending으로 변경")
        
        return jsonify({
            'success': True,
            'message': f'{updated_count}개의 패키지 주문 상태를 pending으로 변경했습니다.'
        }), 200
        
    except Exception as e:
        print(f"❌ 패키지 주문 재처리 오류: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            'error': f'패키지 주문 재처리 실패: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
            
# 예약 발송 주문 처리
def create_scheduled_order():
    """예약 발송 주문 생성"""
    conn = None
    cursor = None
    
    try:
        data = request.get_json()
        print(f"=== 예약 발송 주문 생성 요청 ===")
        print(f"요청 데이터: {data}")
        
        user_id = data.get('user_id')
        service_id = data.get('service_id')
        link = data.get('link')
        quantity = data.get('quantity')
        price = data.get('price') or data.get('total_price')
        scheduled_datetime = data.get('scheduled_datetime')
        
        # 필수 필드 검증
        if not all([user_id, service_id, link, quantity, price, scheduled_datetime]):
            return jsonify({'error': '필수 필드가 누락되었습니다.'}), 400
        
        # 예약 시간 검증
        try:
            scheduled_dt = datetime.strptime(scheduled_datetime, '%Y-%m-%d %H:%M')
            now = datetime.now()
            time_diff_minutes = (scheduled_dt - now).total_seconds() / 60
            
            print(f"🔍 예약 시간 검증: 예약시간={scheduled_datetime}, 현재시간={now.strftime('%Y-%m-%d %H:%M')}, 차이={time_diff_minutes:.1f}분")
            
            if scheduled_dt <= now:
                print(f"❌ 예약 시간이 현재 시간보다 이전입니다.")
                return jsonify({'error': '예약 시간은 현재 시간보다 늦어야 합니다.'}), 400
                
            # 5분 ~ 7일 이내
            if time_diff_minutes < 5 or time_diff_minutes > 10080:  # 7일 = 7 * 24 * 60 = 10080분
                print(f"❌ 예약 시간이 범위를 벗어났습니다. (5분~7일)")
                return jsonify({'error': '예약 시간은 5분 후부터 7일 이내여야 합니다.'}), 400
                
            print(f"✅ 예약 시간 검증 통과: {time_diff_minutes:.1f}분 후")
                
        except ValueError as e:
            print(f"❌ 예약 시간 형식 오류: {e}")
            return jsonify({'error': '예약 시간 형식이 올바르지 않습니다.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 예약 주문 저장
        package_steps = data.get('package_steps', [])
        runs = data.get('runs', 1)  # Drip-feed: 기본값 1
        interval = data.get('interval', 0)  # Drip-feed: 기본값 0
        print(f"🔍 예약 주문 저장: 사용자={user_id}, 서비스={service_id}, 예약시간={scheduled_datetime}, 패키지단계={len(package_steps)}개, runs={runs}, interval={interval}")
        
        # order_id 생성
        import time
        order_id = f"ORDER_{int(time.time())}_{user_id[:8]}"
        
        # orders 테이블에 예약 주문 저장
        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("""
                INSERT INTO orders 
                (order_id, user_id, service_id, link, quantity, price, status, is_scheduled, scheduled_datetime, package_steps, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending', TRUE, %s, %s, NOW(), NOW())
            """, (
                order_id, user_id, service_id, link, quantity, price, scheduled_datetime,
                json.dumps(package_steps) if package_steps else None
            ))
            
            # package_steps가 있으면 execution_progress에 예약 정보 저장
            if package_steps and len(package_steps) > 0:
                for idx, step in enumerate(package_steps):
                    step_delay = step.get('delay', 0)
                    scheduled_time = scheduled_datetime
                    if idx > 0:
                        # 누적 delay 계산
                        from datetime import datetime, timedelta
                        if isinstance(scheduled_datetime, str):
                            scheduled_time = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
                        scheduled_time = scheduled_time + timedelta(minutes=step_delay)
                    
                    cursor.execute("""
                        INSERT INTO execution_progress 
                        (order_id, exec_type, step_number, step_name, service_id, quantity, scheduled_datetime, status, created_at)
                        VALUES (%s, 'package', %s, %s, %s, %s, %s, 'pending', NOW())
                        ON CONFLICT (order_id, exec_type, step_number) DO NOTHING
                    """, (
                        order_id, idx + 1, step.get('name', f'단계 {idx + 1}'),
                        step.get('id'), step.get('quantity', 0), scheduled_time
                    ))
        else:
            cursor.execute("""
                INSERT INTO orders 
                (order_id, user_id, service_id, link, quantity, price, status, is_scheduled, scheduled_datetime, package_steps, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', 1, ?, ?, datetime('now'), datetime('now'))
            """, (
                order_id, user_id, service_id, link, quantity, price, scheduled_datetime,
                json.dumps(package_steps) if package_steps else None
            ))
            
            # package_steps가 있으면 execution_progress에 예약 정보 저장
            if package_steps and len(package_steps) > 0:
                for idx, step in enumerate(package_steps):
                    step_delay = step.get('delay', 0)
                    scheduled_time = scheduled_datetime
                    if idx > 0:
                        from datetime import datetime, timedelta
                        if isinstance(scheduled_datetime, str):
                            scheduled_time = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
                        scheduled_time = scheduled_time + timedelta(minutes=step_delay)
                    
                    cursor.execute("""
                        INSERT INTO execution_progress 
                        (order_id, exec_type, step_number, step_name, service_id, quantity, scheduled_datetime, status, created_at)
                        VALUES (?, 'package', ?, ?, ?, ?, ?, 'pending', datetime('now'))
                    """, (
                        order_id, idx + 1, step.get('name', f'단계 {idx + 1}'),
                        step.get('id'), step.get('quantity', 0), scheduled_time
                    ))
        
        conn.commit()
        
        print(f"✅ 예약 발송 주문 생성 완료: {scheduled_datetime}")
        print(f"✅ 예약 주문이 {time_diff_minutes:.1f}분 후에 처리됩니다.")
        
        return jsonify({
            'success': True,
            'message': f'예약 발송이 설정되었습니다. ({scheduled_datetime}에 처리됩니다)',
            'scheduled_datetime': scheduled_datetime,
            'order_id': order_id
        }), 200
        
    except Exception as e:
        print(f"❌ 예약 발송 주문 생성 오류: {str(e)}")
        return jsonify({'error': f'예약 발송 주문 생성 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()