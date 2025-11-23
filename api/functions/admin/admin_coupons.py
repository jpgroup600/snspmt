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
from flasgger import Swagger
from services import (
    get_parameter_value,
    get_current_user,
    monitor_performance,
    require_admin_auth,
    verify_supabase_jwt,
)

@require_admin_auth
def admin_get_coupons():
    """쿠폰 목록 조회(간단 버전)"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("""
                SELECT 
                    c.coupon_id,
                    c.coupon_code,
                    c.coupon_name,
                    c.discount_type,
                    c.discount_value,
                    c.product_variant_id,
                    c.min_order_amount,
                    c.valid_from,
                    c.valid_until,
                    c.created_at
                FROM coupons c
                ORDER BY c.coupon_id DESC
                LIMIT 200
            """)
        else:
            cursor.execute("""
                SELECT 
                    coupon_id,
                    coupon_code,
                    coupon_name,
                    discount_type,
                    discount_value,
                    product_variant_id,
                    min_order_amount,
                    valid_from,
                    valid_until,
                    created_at
                FROM coupons
                ORDER BY coupon_id DESC
                LIMIT 200
            """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            result.append({
                'coupon_id': r.get('coupon_id'),
                'coupon_code': r.get('coupon_code'),
                'coupon_name': r.get('coupon_name'),
                'discount_type': r.get('discount_type'),
                'discount_value': float(r.get('discount_value') or 0),
                'product_variant_id': r.get('product_variant_id'),
                'min_order_amount': float(r.get('min_order_amount') or 0) if r.get('min_order_amount') else None,
                'valid_from': r.get('valid_from').isoformat() if r.get('valid_from') and hasattr(r.get('valid_from'), 'isoformat') else (str(r.get('valid_from')) if r.get('valid_from') else None),
                'valid_until': r.get('valid_until').isoformat() if r.get('valid_until') and hasattr(r.get('valid_until'), 'isoformat') else (str(r.get('valid_until')) if r.get('valid_until') else None),
                'created_at': r.get('created_at').isoformat() if r.get('created_at') and hasattr(r.get('created_at'), 'isoformat') else (str(r.get('created_at')) if r.get('created_at') else None),
            })
        return jsonify({'coupons': result, 'count': len(result)}), 200
    except Exception as e:
        print(f"❌ 쿠폰 목록 조회 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 조회 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
            
@require_admin_auth
def admin_create_coupon():
    """쿠폰 생성"""
    # OPTIONS 요청 처리 (CORS preflight)
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    cursor = None
    try:
        data = request.get_json()
        coupon_code = data.get('coupon_code')
        coupon_name = data.get('coupon_name')
        discount_type = data.get('discount_type', 'percentage')
        discount_value = data.get('discount_value')
        product_variant_id = data.get('product_variant_id')
        min_order_amount = data.get('min_order_amount')
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')

        if not coupon_code or not coupon_name or not discount_value:
            return jsonify({'error': '쿠폰 코드, 이름, 할인 값은 필수입니다.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("""
                INSERT INTO coupons (
                    coupon_code, coupon_name, discount_type, discount_value,
                    product_variant_id, min_order_amount, valid_from, valid_until
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING coupon_id
            """, (
                coupon_code, coupon_name, discount_type, float(discount_value),
                product_variant_id if product_variant_id else None,
                float(min_order_amount) if min_order_amount else None,
                valid_from if valid_from else None,
                valid_until if valid_until else None
            ))
            coupon_id = cursor.fetchone()['coupon_id']
        else:
            cursor.execute("""
                INSERT INTO coupons (
                    coupon_code, coupon_name, discount_type, discount_value,
                    product_variant_id, min_order_amount, valid_from, valid_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                coupon_code, coupon_name, discount_type, float(discount_value),
                product_variant_id if product_variant_id else None,
                float(min_order_amount) if min_order_amount else None,
                valid_from if valid_from else None,
                valid_until if valid_until else None
            ))
            coupon_id = cursor.lastrowid

        conn.commit()
        return jsonify({'success': True, 'coupon_id': coupon_id, 'message': '쿠폰이 생성되었습니다.'}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 쿠폰 생성 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 생성 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@require_admin_auth
def admin_create_coupon():
    """쿠폰 생성"""
    # OPTIONS 요청 처리 (CORS preflight)
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    cursor = None
    try:
        data = request.get_json()
        coupon_code = data.get('coupon_code')
        coupon_name = data.get('coupon_name')
        discount_type = data.get('discount_type', 'percentage')
        discount_value = data.get('discount_value')
        product_variant_id = data.get('product_variant_id')
        min_order_amount = data.get('min_order_amount')
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')

        if not coupon_code or not coupon_name or not discount_value:
            return jsonify({'error': '쿠폰 코드, 이름, 할인 값은 필수입니다.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("""
                INSERT INTO coupons (
                    coupon_code, coupon_name, discount_type, discount_value,
                    product_variant_id, min_order_amount, valid_from, valid_until
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING coupon_id
            """, (
                coupon_code, coupon_name, discount_type, float(discount_value),
                product_variant_id if product_variant_id else None,
                float(min_order_amount) if min_order_amount else None,
                valid_from if valid_from else None,
                valid_until if valid_until else None
            ))
            coupon_id = cursor.fetchone()['coupon_id']
        else:
            cursor.execute("""
                INSERT INTO coupons (
                    coupon_code, coupon_name, discount_type, discount_value,
                    product_variant_id, min_order_amount, valid_from, valid_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                coupon_code, coupon_name, discount_type, float(discount_value),
                product_variant_id if product_variant_id else None,
                float(min_order_amount) if min_order_amount else None,
                valid_from if valid_from else None,
                valid_until if valid_until else None
            ))
            coupon_id = cursor.lastrowid

        conn.commit()
        return jsonify({'success': True, 'coupon_id': coupon_id, 'message': '쿠폰이 생성되었습니다.'}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 쿠폰 생성 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 생성 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            

@require_admin_auth
def admin_update_coupon(coupon_id):
    """쿠폰 수정"""
    conn = None
    cursor = None
    try:
        data = request.get_json()
        coupon_code = data.get('coupon_code')
        coupon_name = data.get('coupon_name')
        discount_type = data.get('discount_type')
        discount_value = data.get('discount_value')
        product_variant_id = data.get('product_variant_id')
        min_order_amount = data.get('min_order_amount')
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 업데이트할 필드만 동적으로 구성
        update_fields = []
        update_values = []

        if coupon_code is not None:
            update_fields.append("coupon_code = %s" if DATABASE_URL.startswith('postgresql://') else "coupon_code = ?")
            update_values.append(coupon_code)
        if coupon_name is not None:
            update_fields.append("coupon_name = %s" if DATABASE_URL.startswith('postgresql://') else "coupon_name = ?")
            update_values.append(coupon_name)
        if discount_type is not None:
            update_fields.append("discount_type = %s" if DATABASE_URL.startswith('postgresql://') else "discount_type = ?")
            update_values.append(discount_type)
        if discount_value is not None:
            update_fields.append("discount_value = %s" if DATABASE_URL.startswith('postgresql://') else "discount_value = ?")
            update_values.append(float(discount_value))
        if product_variant_id is not None:
            update_fields.append("product_variant_id = %s" if DATABASE_URL.startswith('postgresql://') else "product_variant_id = ?")
            update_values.append(product_variant_id if product_variant_id else None)
        if min_order_amount is not None:
            update_fields.append("min_order_amount = %s" if DATABASE_URL.startswith('postgresql://') else "min_order_amount = ?")
            update_values.append(float(min_order_amount) if min_order_amount else None)
        if valid_from is not None:
            update_fields.append("valid_from = %s" if DATABASE_URL.startswith('postgresql://') else "valid_from = ?")
            update_values.append(valid_from if valid_from else None)
        if valid_until is not None:
            update_fields.append("valid_until = %s" if DATABASE_URL.startswith('postgresql://') else "valid_until = ?")
            update_values.append(valid_until if valid_until else None)

        if not update_fields:
            return jsonify({'error': '수정할 필드가 없습니다.'}), 400

        update_values.append(coupon_id)
        query = f"""
            UPDATE coupons 
            SET {', '.join(update_fields)}
            WHERE coupon_id = {'%s' if DATABASE_URL.startswith('postgresql://') else '?'}
        """
        cursor.execute(query, update_values)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': '쿠폰을 찾을 수 없습니다.'}), 404

        return jsonify({'success': True, 'message': '쿠폰이 수정되었습니다.'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 쿠폰 수정 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 수정 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@require_admin_auth
def admin_delete_coupon(coupon_id):
    """쿠폰 삭제"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("DELETE FROM coupons WHERE coupon_id = %s", (coupon_id,))
        else:
            cursor.execute("DELETE FROM coupons WHERE coupon_id = ?", (coupon_id,))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': '쿠폰을 찾을 수 없습니다.'}), 404

        return jsonify({'success': True, 'message': '쿠폰이 삭제되었습니다.'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 쿠폰 삭제 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 삭제 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@require_admin_auth
def admin_update_coupon(coupon_id):
    """쿠폰 수정"""
    conn = None
    cursor = None
    try:
        data = request.get_json()
        coupon_code = data.get('coupon_code')
        coupon_name = data.get('coupon_name')
        discount_type = data.get('discount_type')
        discount_value = data.get('discount_value')
        product_variant_id = data.get('product_variant_id')
        min_order_amount = data.get('min_order_amount')
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 업데이트할 필드만 동적으로 구성
        update_fields = []
        update_values = []

        if coupon_code is not None:
            update_fields.append("coupon_code = %s" if DATABASE_URL.startswith('postgresql://') else "coupon_code = ?")
            update_values.append(coupon_code)
        if coupon_name is not None:
            update_fields.append("coupon_name = %s" if DATABASE_URL.startswith('postgresql://') else "coupon_name = ?")
            update_values.append(coupon_name)
        if discount_type is not None:
            update_fields.append("discount_type = %s" if DATABASE_URL.startswith('postgresql://') else "discount_type = ?")
            update_values.append(discount_type)
        if discount_value is not None:
            update_fields.append("discount_value = %s" if DATABASE_URL.startswith('postgresql://') else "discount_value = ?")
            update_values.append(float(discount_value))
        if product_variant_id is not None:
            update_fields.append("product_variant_id = %s" if DATABASE_URL.startswith('postgresql://') else "product_variant_id = ?")
            update_values.append(product_variant_id if product_variant_id else None)
        if min_order_amount is not None:
            update_fields.append("min_order_amount = %s" if DATABASE_URL.startswith('postgresql://') else "min_order_amount = ?")
            update_values.append(float(min_order_amount) if min_order_amount else None)
        if valid_from is not None:
            update_fields.append("valid_from = %s" if DATABASE_URL.startswith('postgresql://') else "valid_from = ?")
            update_values.append(valid_from if valid_from else None)
        if valid_until is not None:
            update_fields.append("valid_until = %s" if DATABASE_URL.startswith('postgresql://') else "valid_until = ?")
            update_values.append(valid_until if valid_until else None)

        if not update_fields:
            return jsonify({'error': '수정할 필드가 없습니다.'}), 400

        update_values.append(coupon_id)
        query = f"""
            UPDATE coupons 
            SET {', '.join(update_fields)}
            WHERE coupon_id = {'%s' if DATABASE_URL.startswith('postgresql://') else '?'}
        """
        cursor.execute(query, update_values)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': '쿠폰을 찾을 수 없습니다.'}), 404

        return jsonify({'success': True, 'message': '쿠폰이 수정되었습니다.'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 쿠폰 수정 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 수정 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
            
@require_admin_auth
def admin_delete_coupon(coupon_id):
    """쿠폰 삭제"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if DATABASE_URL.startswith('postgresql://'):
            cursor.execute("DELETE FROM coupons WHERE coupon_id = %s", (coupon_id,))
        else:
            cursor.execute("DELETE FROM coupons WHERE coupon_id = ?", (coupon_id,))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': '쿠폰을 찾을 수 없습니다.'}), 404

        return jsonify({'success': True, 'message': '쿠폰이 삭제되었습니다.'}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 쿠폰 삭제 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'쿠폰 삭제 실패: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()