"""
客户端模拟器：演示设备注册 -> 卡密绑定 -> 轮询 的完整流程与签名算法。

用法：
    venv/Scripts/python scripts/client_demo.py                # 默认轮询 3 次
    venv/Scripts/python scripts/client_demo.py --key XXXX     # 指定卡密
"""
import argparse
import hashlib
import hmac
import secrets
import time

import requests

BASE_URL = 'http://127.0.0.1:8000'
CLIENT_API_SECRET = 'vidsail-dev-client-secret'  # 与后端 settings.CLIENT_API_SECRET 一致


def sign(*parts):
    message = '|'.join(str(p) for p in parts)
    return hmac.new(CLIENT_API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()


def post(path, payload):
    resp = requests.post(BASE_URL + path, json=payload, timeout=10)
    body = resp.json()
    print(f'[{path}] code={body.get("code")} message={body.get("message")} data={body.get("data")}')
    return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', help='卡密（不填则用环境演示卡密）')
    parser.add_argument('--rounds', type=int, default=3, help='轮询次数')
    args = parser.parse_args()

    card_key = args.key
    device_code = f'DEV-DEMO-{secrets.token_hex(4).upper()}-PC'
    ts = int(time.time() * 1000)

    # 1. 注册设备
    post('/api/client/register-device', {
        'device_code': device_code, 'timestamp': ts, 'sign': sign(device_code, ts)})

    if not card_key:
        print('提示：未指定卡密。请先在后台「卡密管理」生成一个卡密，用 --key 传入。演示结束。')
        return

    # 2. 绑定卡密
    ts = int(time.time() * 1000)
    body = post('/api/client/bind-card', {
        'card_key': card_key, 'device_code': device_code,
        'timestamp': ts, 'sign': sign(card_key, device_code, ts)})
    if body.get('code') != 0:
        return

    # 3. 轮询
    for i in range(args.rounds):
        time.sleep(2)
        ts = int(time.time() * 1000)
        body = post('/api/client/poll', {
            'card_key': card_key, 'device_code': device_code,
            'timestamp': ts, 'sign': sign(card_key, device_code, ts)})
        if body.get('code') != 0:
            break
        print(f'  轮询 #{i + 1} 剩余秒数: {body["data"]["remaining_seconds"]}')


if __name__ == '__main__':
    main()
