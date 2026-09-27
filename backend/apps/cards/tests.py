import json
import time
from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.cards.keys import generate_card_key, is_valid_key_format
from apps.cards.models import CardKey, CardLog, Device
from apps.cards.services import make_sign


def payload(resp):
    return json.loads(resp.content)


def now_ms():
    return int(time.time() * 1000)


class CardKeyGenerationTests(TestCase):
    def test_key_format_and_checksum(self):
        for _ in range(50):
            key = generate_card_key()
            self.assertEqual(len(key), 16)
            self.assertTrue(is_valid_key_format(key))

    def test_invalid_keys_rejected(self):
        key = generate_card_key()
        self.assertFalse(is_valid_key_format(key[:-1] + ('0' if key[-1] != '0' else '1')))  # 校验位错
        self.assertFalse(is_valid_key_format(key[:15]))  # 长度错
        self.assertFalse(is_valid_key_format('IIIIIIIIIIIIIIII'))  # 非法字符

    def test_keys_unique(self):
        keys = {generate_card_key() for _ in range(200)}
        self.assertEqual(len(keys), 200)


class CardAdminApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_user = User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        self.client.force_authenticate(self.super_user)

    def test_create_card_returns_generated_key(self):
        resp = self.client.post('/api/admin/cards/', {
            'count': 2, 'amount': '19.90', 'remark': '测试',
            'start_time': '2026-01-01 00:00:00', 'end_time': '2027-01-01 00:00:00',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        items = payload(resp)['data']
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertTrue(is_valid_key_format(item['key']))
            self.assertEqual(item['effective_status'], 0)
            self.assertEqual(item['status_label'], '未绑定')
            self.assertTrue(CardLog.objects.filter(card__key=item['key'], action='create').exists())

    def test_update_cannot_change_key(self):
        card = CardKey.objects.create(key=generate_card_key())
        resp = self.client.patch(f'/api/admin/cards/{card.pk}/', {'key': 'HACKEDHACKEDHACK', 'remark': '改备注'},
                                 format='json')
        self.assertEqual(resp.status_code, 200)
        card.refresh_from_db()
        self.assertNotEqual(card.key, 'HACKEDHACKEDHACK')
        self.assertEqual(card.remark, '改备注')
        self.assertTrue(CardLog.objects.filter(card=card, action='update').exists())

    def test_cancel_marks_invalid_and_logs(self):
        card = CardKey.objects.create(key=generate_card_key())
        resp = self.client.post(f'/api/admin/cards/{card.pk}/cancel/')
        self.assertEqual(resp.status_code, 200)
        card.refresh_from_db()
        self.assertEqual(card.status, CardKey.STATUS_INVALID)
        self.assertTrue(CardLog.objects.filter(card=card, action='cancel', source='admin').exists())

    def test_status_filter_by_effective_status(self):
        past = timezone.now() - timedelta(days=1)
        CardKey.objects.create(key=generate_card_key())  # 未绑定
        bound = CardKey.objects.create(key=generate_card_key(), status=CardKey.STATUS_BOUND)
        CardKey.objects.create(key=generate_card_key(), status=CardKey.STATUS_INVALID)  # 已失效
        expired = CardKey.objects.create(key=generate_card_key(), end_time=past)  # 未绑定但已过期
        resp = self.client.get('/api/admin/cards/?status=2')
        self.assertEqual(payload(resp)['data']['total'], 1)
        resp = self.client.get('/api/admin/cards/?status=3')
        self.assertEqual(payload(resp)['data']['total'], 1)
        resp = self.client.get('/api/admin/cards/?status=0')
        keys = [i['key'] for i in payload(resp)['data']['items']]
        self.assertNotIn(expired.key, keys)
        self.assertEqual(bound.status, CardKey.STATUS_BOUND)

    def test_keyword_search_by_key_and_device(self):
        card = CardKey.objects.create(key=generate_card_key())
        device = Device.objects.create(code='DEV-ABC-12345678')
        CardKey.objects.create(key=generate_card_key(), device=device, status=CardKey.STATUS_BOUND)
        resp = self.client.get(f"/api/admin/cards/?keyword={card.key[:10]}")
        self.assertEqual(payload(resp)['data']['total'], 1)
        resp = self.client.get('/api/admin/cards/?keyword=DEV-ABC')
        self.assertEqual(payload(resp)['data']['total'], 1)


class ClientApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_user = User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        self.device_code = 'DEV-TEST-0001-ABCD'
        self.card = CardKey.objects.create(
            key=generate_card_key(), start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(days=30))

    def _sign(self, card_key=None, device_code=None, ts=None):
        return make_sign(card_key or '', device_code or '', ts)

    def _bind(self, card_key=None, device_code=None, sign=None, ts=None):
        ts = ts or now_ms()
        return self.client.post('/api/client/bind-card', {
            'card_key': card_key or self.card.key, 'device_code': device_code or self.device_code,
            'timestamp': ts, 'sign': sign if sign is not None else self._sign(card_key or self.card.key,
                                                                             device_code or self.device_code, ts),
        }, format='json')

    def test_bind_success_and_idempotent(self):
        resp = self._bind()
        self.assertEqual(resp.status_code, 200)
        body = payload(resp)
        self.assertEqual(body['code'], 0)
        self.assertTrue(body['data']['is_new_bind'])
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, CardKey.STATUS_BOUND)
        self.assertEqual(self.card.device.code, self.device_code)
        self.assertTrue(CardLog.objects.filter(card=self.card, action='bind', source='client').exists())

        # 同设备重复绑定 -> 幂等，不再记日志
        log_count = CardLog.objects.filter(card=self.card, action='bind').count()
        resp = self._bind()
        self.assertEqual(payload(resp)['data']['is_new_bind'], False)
        self.assertEqual(CardLog.objects.filter(card=self.card, action='bind').count(), log_count)

    def test_bind_other_device_rejected(self):
        self._bind()
        resp = self._bind(device_code='DEV-TEST-0002-EFGH')
        self.assertEqual(payload(resp)['code'], -5)

    def test_bind_wrong_signature_and_stale_timestamp(self):
        resp = self._bind(sign='bad-signature')
        self.assertEqual(payload(resp)['code'], -1)
        stale = now_ms() - 4000 * 1000
        resp = self._bind(ts=stale, sign=self._sign(self.card.key, self.device_code, stale))
        self.assertEqual(payload(resp)['code'], -2)

    def test_bind_expired_future_and_invalid_cards(self):
        now = timezone.now()
        expired = CardKey.objects.create(key=generate_card_key(), end_time=now - timedelta(days=1))
        resp = self._bind(card_key=expired.key)
        self.assertEqual(payload(resp)['code'], -4)

        future = CardKey.objects.create(key=generate_card_key(), start_time=now + timedelta(days=1))
        resp = self._bind(card_key=future.key)
        self.assertEqual(payload(resp)['code'], -7)

        invalid = CardKey.objects.create(key=generate_card_key(), status=CardKey.STATUS_INVALID)
        resp = self._bind(card_key=invalid.key)
        self.assertEqual(payload(resp)['code'], -6)

        resp = self._bind(card_key=generate_card_key())  # 格式合法但不存在
        self.assertEqual(payload(resp)['code'], -3)

    def test_poll_success(self):
        self._bind()
        ts = now_ms()
        resp = self.client.post('/api/client/poll', {
            'card_key': self.card.key, 'device_code': self.device_code,
            'timestamp': ts, 'sign': self._sign(self.card.key, self.device_code, ts),
        }, format='json')
        body = payload(resp)
        self.assertEqual(body['code'], 0)
        self.assertEqual(body['data']['status'], 1)
        self.assertGreater(body['data']['remaining_seconds'], 0)
        # 轮询不记录日志
        self.assertFalse(CardLog.objects.filter(card=self.card, action='poll').exists())

    def test_poll_before_bind(self):
        ts = now_ms()
        resp = self.client.post('/api/client/poll', {
            'card_key': self.card.key, 'device_code': self.device_code,
            'timestamp': ts, 'sign': self._sign(self.card.key, self.device_code, ts),
        }, format='json')
        self.assertEqual(payload(resp)['code'], -10)

    def test_register_device(self):
        ts = now_ms()
        sign = make_sign(self.device_code, ts)
        resp = self.client.post('/api/client/register-device', {
            'device_code': self.device_code, 'timestamp': ts, 'sign': sign,
        }, format='json')
        body = payload(resp)
        self.assertEqual(body['code'], 0)
        self.assertTrue(body['data']['is_new'])
        self.assertTrue(Device.objects.filter(code=self.device_code).exists())

    def test_admin_card_log_list(self):
        self._bind()
        self.client.force_authenticate(self.super_user)
        resp = self.client.get(f"/api/admin/card-logs/?keyword={self.card.key[:8]}")
        items = payload(resp)['data']['items']
        self.assertTrue(any(i['action'] == 'bind' for i in items))
