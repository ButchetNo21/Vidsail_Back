"""系统权限码定义：超级管理员拥有全部，运营账号按勾选授权。"""

PERMISSION_GROUPS = [
    {
        'group': '卡密管理',
        'items': [
            {'code': 'card:view', 'label': '查看卡密'},
            {'code': 'card:edit', 'label': '新增/编辑卡密'},
            {'code': 'card:cancel', 'label': '取消卡密'},
        ],
    },
    {
        'group': '卡密日志',
        'items': [
            {'code': 'cardlog:view', 'label': '查看卡密日志'},
        ],
    },
    {
        'group': '提示词管理',
        'items': [
            {'code': 'prompt:view', 'label': '查看提示词'},
            {'code': 'prompt:edit', 'label': '编辑提示词'},
            {'code': 'prompt:delete', 'label': '删除提示词'},
        ],
    },
    {
        'group': '分类与标签',
        'items': [
            {'code': 'category:view', 'label': '查看分类标签'},
            {'code': 'category:edit', 'label': '编辑分类'},
            {'code': 'tag:edit', 'label': '编辑标签'},
        ],
    },
    {
        'group': '广告管理',
        'items': [
            {'code': 'ad:view', 'label': '查看广告'},
            {'code': 'ad:edit', 'label': '编辑广告'},
        ],
    },
    {
        'group': '配置管理',
        'items': [
            {'code': 'config:view', 'label': '查看配置'},
            {'code': 'config:edit', 'label': '编辑配置'},
        ],
    },
]

ALL_CODES = [item['code'] for group in PERMISSION_GROUPS for item in group['items']]
_ALL_SET = set(ALL_CODES)


def filter_valid_codes(codes):
    return [c for c in (codes or []) if c in _ALL_SET]
