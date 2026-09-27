# VidSail 后端（Django 4.2 + DRF + MySQL）

## 技术栈

- Django 4.2.10 / djangorestframework 3.14.0 / djangorestframework-simplejwt 5.3.0
- MySQL 8（PyMySQL 驱动），数据库名 `vidsail`（utf8mb4）
- 虚拟环境：`venv/`
- 配置分离：`config/settings/dev.py`（开发）/ `config/settings/prod.py`（生产，密钥等全部走环境变量）

## 快速开始

```bash
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt     # Git Bash: venv/Scripts/pip
venv\Scripts\python scripts\create_db.py         # 建库（root/root，可被环境变量覆盖）
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py seed_admin         # 超级管理员 admin / admin123
venv\Scripts\python manage.py seed_demo          # 可选：演示数据
venv\Scripts\python manage.py runserver          # 默认 dev 配置，127.0.0.1:8000
```

## 测试

```bash
venv\Scripts\python manage.py test     # 38 个用例：鉴权/权限/卡密/签名/绑定/轮询/提示词/广告/配置/仪表盘
```

## 目录结构

```
config/            settings(base/dev/prod)、urls、wsgi(asgi 用 prod)
apps/core/         统一响应包装、异常处理、软删除基类、权限类、分页
apps/accounts/     用户(超管/运营)、JWT 登录/刷新/登出、权限码、seed_admin/seed_demo
apps/cards/        卡密(生成算法/绑定/轮询)、设备、卡密日志、客户端接口、client_demo.py
apps/prompts/      提示词(软删)、分类、标签
apps/ads/          广告位、广告图片(最多两张、上传/移除)
apps/configs/      系统配置(ak/sk，列表脱敏)
apps/dashboard/    仪表盘统计(仅超管)
scripts/           create_db.py、client_demo.py（客户端流程模拟）
```

## 统一响应与鉴权

- 后台接口统一返回 `{code, message, data}`；`code=0` 成功。
- 除 `/api/auth/login`、`/api/auth/refresh`、`/api/client/*` 外全部要求 JWT：
  `Authorization: Bearer <access>`。鉴权失败返回 HTTP 401 + `{code:401}`，前端收到后
  立即跳转登录页且不执行本次请求。
- access 12h / refresh 7d，refresh 轮换并拉黑（token_blacklist）。

## 角色与权限

- 超级管理员：全部权限 + 首页仪表盘 + 账号管理。
- 运营：由超管创建，权限按码勾选（`card:view`、`card:edit`、`card:cancel`、`cardlog:view`、
  `prompt:*`、`category:*`、`tag:edit`、`ad:*`、`config:*`），见 `apps/accounts/permissions.py`。

## 卡密

- 16 位大写字母数字：`9 位加密时间戳 + 6 位随机 + 1 位校验位`，时间戳与
  HMAC(密钥, 随机数) 异或，无法从卡密反推生成时间或批量伪造；校验位可离线识别输错。
- 状态：0 未绑定 / 1 已绑定 / 2 已过期(按结束时间实时计算) / 3 已失效(取消)。
- 修改可改开始/结束时间、金额、备注，**卡密本身不可改**；「取消」即置为已失效；
  支持解绑。所有创建/修改/取消/绑定/解绑都写 `card_log`，**轮询不记录**。

## 客户端接口（无 JWT，需数字签名）

签名算法：`sign = HMAC-SHA256(CLIENT_API_SECRET, "字段1|字段2|...|timestamp毫秒")` 的小写 hex，
timestamp 与服务器偏差超过 `CLIENT_TS_TOLERANCE`(默认300秒) 拒绝。

| 接口 | 签名字段 | 说明 |
|---|---|---|
| POST `/api/client/register-device` | device_code | 客户端首次运行注册设备账号 |
| POST `/api/client/bind-card` | card_key, device_code | 绑定校验：过期/失效/未生效/被其他设备绑定 |
| POST `/api/client/poll` | card_key, device_code | 客户端自定义间隔轮询，返回剩余秒数，不记日志 |
| GET `/api/client/prompts` | device_code | 拉取启用中的提示词（keyword/category_id/tag_id 可选） |
| GET `/api/client/ads?slot_code=` | device_code | 拉取广告位当前有效图片 |
| GET `/api/client/config?code=` | device_code | 拉取启用中的配置（ak/sk 等） |

业务错误 HTTP 200 + 负数错误码：

| 码 | 含义 | 码 | 含义 |
|---|---|---|---|
| -1 | 签名错误/参数缺失 | -6 | 卡密已失效 |
| -2 | 时间戳过期 | -7 | 卡密未到生效时间 |
| -3 | 卡密不存在 | -8 | 设备被禁用 |
| -4 | 卡密已过期 | -9 | 卡密格式错误 |
| -5 | 卡密已绑定其他设备 | -10 | 卡密未绑定设备 |

模拟客户端：`venv\Scripts\python scripts\client_demo.py --key <卡密> --rounds 3`

## 生产部署（prod）

```bash
set DJANGO_SETTINGS_MODULE=config.settings.prod   # wsgi.py 已默认 prod
set DJANGO_SECRET_KEY=<随机长字符串>
set DJANGO_ALLOWED_HOSTS=api.example.com
set CLIENT_API_SECRET=<与客户端约定的新密钥>
set CORS_ALLOWED_ORIGINS=https://admin.example.com
venv\Scripts\pip install gunicorn                 # 或使用 waitress(genicor 等 Windows 方案)
gunicorn config.wsgi -b 0.0.0.0:8000
```

生产必须：更换 `DJANGO_SECRET_KEY` 与 `CLIENT_API_SECRET`；media/静态文件由 Nginx 托管；
MySQL 使用独立账号而非 root；`.env.example` 列出全部环境变量。
