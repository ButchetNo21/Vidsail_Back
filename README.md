# VidSail 运营管理平台

前后端分离项目：

- [backend/](backend/README.md) — Django 4.2 + DRF + SimpleJWT + MySQL（虚拟环境、dev/prod 配置、38 个测试用例）
- [frontend/](frontend/README.md) — Vue3 + uniapp(H5) + Element Plus + ECharts 管理后台

## 一键启动

```bash
# 1. 后端（首次）
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python scripts\create_db.py
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py seed_admin      # 管理员 admin / admin123
venv\Scripts\python manage.py seed_demo       # 可选演示数据
venv\Scripts\python manage.py runserver       # http://127.0.0.1:8000

# 2. 前端（首次）
cd ../frontend
npm install
npm run dev:h5                                # http://localhost:5173
```

## 功能总览

1. **账号体系**：超级管理员（全部权限）+ 运营（权限按码勾选）；JWT 鉴权，过期自动跳登录页。
2. **卡密管理**：16 位加密卡密（加密时间戳+随机数+校验位），批量生成、修改（密钥不可改）、
   取消（已失效）、解绑；与设备账号绑定，绑定校验过期/重复绑定；客户端按自定义间隔轮询，
   全部客户端请求带 HMAC-SHA256 数字签名防篡改，业务错误返回 -1~-10 错误码。
3. **卡密日志**：创建/修改/取消/绑定/解绑全记录，轮询不记录。
4. **提示词管理**：多行内容（TEXT）、分类/标签各最多 3 个、关联链接、状态、创建人/修改人、软删除。
5. **广告位管理**：占位（名称/唯一编码/时间窗/状态）+ 图片管理（最多两张、上传/替换/移除）。
6. **配置管理**：ak/sk 等账号数据，列表脱敏、详情可见、时间窗控制。
7. **仪表盘**（仅超管）：卡密统计、近7天生成/绑定趋势、状态分布饼图、最近日志。
