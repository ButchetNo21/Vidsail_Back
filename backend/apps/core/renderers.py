from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """统一响应包装：成功 -> {code, message, data}；失败由异常处理器输出，不再包装。"""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get('response')
        if response is not None and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)
        if response is not None and getattr(response, 'skip_envelope', False):
            return super().render(data, accepted_media_type, renderer_context)
        if isinstance(data, dict) and 'code' in data and 'message' in data:
            return super().render(data, accepted_media_type, renderer_context)
        return super().render({'code': 0, 'message': 'ok', 'data': data}, accepted_media_type, renderer_context)
