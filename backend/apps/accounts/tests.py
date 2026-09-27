import json

from rest_framework.test import APIClient
from django.test import TestCase

from apps.accounts.models import User


def payload(resp):
    """取统一响应包装后的 body。"""
    return json.loads(resp.content)


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_user = User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        self.operator = User.objects.create_user(
            'op1', 'op123456', role=User.ROLE_OPERATOR, permissions=['card:view'])

    def login(self, username, password):
        return self.client.post('/api/auth/login', {'username': username, 'password': password}, format='json')

    def auth_client(self, user, password):
        client = APIClient()
        resp = client.post('/api/auth/login', {'username': user.username, 'password': password}, format='json')
        token = payload(resp)['data']['token']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_login_success_returns_token_and_user(self):
        resp = self.login('boss', 'boss123456')
        self.assertEqual(resp.status_code, 200)
        body = payload(resp)
        self.assertEqual(body['code'], 0)
        self.assertTrue(body['data']['token'])
        self.assertEqual(body['data']['user']['role'], 'super')

    def test_login_wrong_password(self):
        resp = self.login('boss', 'wrong-password')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('用户名或密码错误', payload(resp)['message'])

    def test_me_requires_jwt(self):
        resp = self.client.get('/api/auth/me')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(payload(resp)['code'], 401)

    def test_me_returns_permissions(self):
        client = self.auth_client(self.operator, 'op123456')
        body = payload(client.get('/api/auth/me'))
        self.assertEqual(body['data']['permissions'], ['card:view'])
        self.assertFalse(body['data']['is_super'])

    def test_operator_cannot_manage_users(self):
        client = self.auth_client(self.operator, 'op123456')
        resp = client.get('/api/admin/users/')
        self.assertEqual(resp.status_code, 403)

    def test_super_creates_operator_with_permissions(self):
        client = self.auth_client(self.super_user, 'boss123456')
        resp = client.post('/api/admin/users/', {
            'username': 'op2', 'password': 'op2123456',
            'permissions': ['card:view', 'card:edit', 'fake:code'],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(username='op2')
        self.assertEqual(user.role, User.ROLE_OPERATOR)
        # 无效权限码被过滤
        self.assertEqual(user.permissions, ['card:view', 'card:edit'])

    def test_operator_with_card_view_can_list_but_not_create(self):
        client = self.auth_client(self.operator, 'op123456')
        self.assertEqual(client.get('/api/admin/cards/').status_code, 200)
        resp = client.post('/api/admin/cards/', {'end_time': '2027-01-01 00:00:00'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_refresh_and_logout(self):
        resp = self.login('boss', 'boss123456')
        refresh = payload(resp)['data']['refresh']
        resp = self.client.post('/api/auth/refresh', {'refresh': refresh}, format='json')
        self.assertEqual(resp.status_code, 200)
        new_refresh = payload(resp)['data']['refresh']
        client = self.auth_client(self.super_user, 'boss123456')
        resp = client.post('/api/auth/logout', {'refresh': new_refresh}, format='json')
        self.assertEqual(resp.status_code, 200)
        # 已拉黑的 refresh 不能再刷新
        resp = self.client.post('/api/auth/refresh', {'refresh': new_refresh}, format='json')
        self.assertEqual(resp.status_code, 401)
