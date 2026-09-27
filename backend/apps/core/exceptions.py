import logging

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger('api')


class ClientApiError(Exception):
    """客户端接口业务错误：HTTP 200 + 负数错误码。"""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def _first_error(detail):
    """从 DRF 校验错误里提取可读文本。"""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, (list, tuple)):
        for item in detail:
            msg = _first_error(item)
            if msg:
                return msg
        return ''
    if isinstance(detail, dict):
        for key, value in detail.items():
            msg = _first_error(value)
            if msg:
                return msg if key in ('detail', 'non_field_errors') else f'{key}: {msg}'
    return ''


_STATUS_MESSAGES = {
    400: '请求参数错误',
    401: '登录已过期，请重新登录',
    403: '没有操作权限',
    404: '资源不存在',
    405: '请求方法不允许',
    429: '请求过于频繁，请稍后再试',
}


def custom_exception_handler(exc, context):
    # 客户端接口业务错误：HTTP 200 + 业务码
    if isinstance(exc, ClientApiError):
        return Response({'code': exc.code, 'message': exc.message, 'data': None}, status=200)

    response = drf_exception_handler(exc, context)
    if response is None:
        # 这里返回 500 响应会把异常"吞掉"，django.request 看不到；
        # 必须在此处记录，否则线上无从排查
        request = context.get('request')
        logger.exception(
            '未处理异常 %s %s user=%s',
            getattr(request, 'method', '-'),
            getattr(request, 'path', '-'),
            getattr(getattr(request, 'user', None), 'pk', None),
        )
        return Response({'code': 500, 'message': '服务器内部错误', 'data': None}, status=500)

    status = response.status_code
    if status == 400:
        message = _first_error(response.data) or '请求参数错误'
        data = response.data
    else:
        message = _STATUS_MESSAGES.get(status, '请求失败')
        if isinstance(response.data, dict):
            message = _first_error(response.data.get('detail')) or message
        data = None
    return Response({'code': status, 'message': message, 'data': data}, status=status)


# exceptions 导出，便于其他模块使用
ValidationError = exceptions.ValidationError
