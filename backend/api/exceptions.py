"""
タスク管理API - カスタム例外ハンドラー
OpenAPI仕様書に基づくエラーレスポンス形式
"""
import uuid
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework import status


def custom_exception_handler(exc, context):
    """カスタム例外ハンドラー"""
    response = exception_handler(exc, context)
    
    if response is not None:
        error_code = get_error_code(response.status_code, exc)
        error_message = get_error_message(response.status_code, exc)
        details = get_error_details(exc) if isinstance(exc, ValidationError) else []
        
        response.data = {
            'error': {
                'code': error_code,
                'message': error_message,
                'details': details,
                'requestId': str(uuid.uuid4()),
            }
        }
    
    return response


def get_error_code(status_code, exc):
    """ステータスコードからエラーコードを取得"""
    error_codes = {
        status.HTTP_400_BAD_REQUEST: 'BAD_REQUEST',
        status.HTTP_401_UNAUTHORIZED: 'AUTH_001',
        status.HTTP_403_FORBIDDEN: 'AUTHZ_001',
        status.HTTP_404_NOT_FOUND: 'RES_001',
        status.HTTP_409_CONFLICT: 'RES_002',
        status.HTTP_422_UNPROCESSABLE_ENTITY: 'VAL_001',
    }
    
    if isinstance(exc, ValidationError):
        return 'VAL_001'
    
    return error_codes.get(status_code, 'INTERNAL_ERROR')


def get_error_message(status_code, exc):
    """ステータスコードからエラーメッセージを取得"""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail
        elif isinstance(exc.detail, dict):
            return '入力値に誤りがあります'
        elif isinstance(exc.detail, list):
            return exc.detail[0] if exc.detail else 'エラーが発生しました'
    
    error_messages = {
        status.HTTP_400_BAD_REQUEST: 'リクエストの形式が正しくありません',
        status.HTTP_401_UNAUTHORIZED: '認証に失敗しました',
        status.HTTP_403_FORBIDDEN: 'このリソースへのアクセス権限がありません',
        status.HTTP_404_NOT_FOUND: 'リソースが見つかりません',
        status.HTTP_409_CONFLICT: 'リソースが既に存在するか、競合が発生しました',
        status.HTTP_422_UNPROCESSABLE_ENTITY: '入力値に誤りがあります',
    }
    
    return error_messages.get(status_code, 'エラーが発生しました')


def get_error_details(exc):
    """バリデーションエラーの詳細を取得"""
    details = []
    
    if isinstance(exc, ValidationError) and isinstance(exc.detail, dict):
        for field, errors in exc.detail.items():
            if isinstance(errors, list):
                for error in errors:
                    details.append({
                        'field': field,
                        'reason': get_error_reason(error),
                        'message': str(error),
                    })
            else:
                details.append({
                    'field': field,
                    'reason': 'invalid',
                    'message': str(errors),
                })
    
    return details


def get_error_reason(error):
    """エラーの理由コードを取得"""
    error_str = str(error).lower()
    
    if 'required' in error_str or '必須' in error_str:
        return 'required'
    elif 'format' in error_str or '形式' in error_str:
        return 'format'
    elif 'min' in error_str or '最小' in error_str:
        return 'min_length'
    elif 'max' in error_str or '最大' in error_str:
        return 'max_length'
    elif 'unique' in error_str or '一意' in error_str or '既に存在' in error_str:
        return 'unique'
    
    return 'invalid'
