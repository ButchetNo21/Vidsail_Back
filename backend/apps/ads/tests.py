import base64
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ads.models import AdImage, AdSlot
from apps.configs.models import SysConfig


def payload(resp):
    return json.loads(resp.content)


PNG_1PX = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')


class AdsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        self.client.force_authenticate(self.user)

    def test_slot_crud_and_soft_delete(self):
        resp = self.client.post('/api/admin/ad-slots/', {
            'name': '首页轮播', 'code': 'home_banner', 'remark': '测试',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        slot_id = payload(resp)['data']['id']

        resp = self.client.patch(f'/api/admin/ad-slots/{slot_id}/', {'status': 0}, format='json')
        self.assertEqual(payload(resp)['data']['status'], 0)

        self.client.delete(f'/api/admin/ad-slots/{slot_id}/')
        self.assertIsNone(AdSlot.objects.filter(pk=slot_id).first())

    def test_duplicate_slot_code_rejected(self):
        AdSlot.objects.create(name='a', code='dup_code')
        resp = self.client.post('/api/admin/ad-slots/', {'name': 'b', 'code': 'dup_code'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_image_upload_and_remove(self):
        slot = AdSlot.objects.create(name='首页轮播', code='home_banner')
        resp = self.client.post('/api/admin/ad-images/', {
            'slot': slot.pk, 'name': '图一', 'subtitle': '副标题', 'url': 'https://example.com',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        image_id = payload(resp)['data']['id']

        f = SimpleUploadedFile('test.png', PNG_1PX, content_type='image/png')
        resp = self.client.post(f'/api/admin/ad-images/{image_id}/upload/', {'file': f, 'position': 'image'})
        self.assertEqual(resp.status_code, 200)
        image = AdImage.objects.get(pk=image_id)
        self.assertTrue(image.image)
        self.assertTrue(image.image.name.startswith('ads/'))

        resp = self.client.post(f'/api/admin/ad-images/{image_id}/remove_image/', {'position': 'image'},
                                format='json')
        image.refresh_from_db()
        self.assertFalse(image.image)

    def test_image_requires_valid_file(self):
        slot = AdSlot.objects.create(name='s', code='c1')
        resp = self.client.post('/api/admin/ad-images/', {
            'slot': slot.pk, 'name': 'x',
        }, format='json')
        self.assertEqual(resp.status_code, 201)  # 图片字段可后补

        bad = SimpleUploadedFile('t.txt', b'hello', content_type='text/plain')
        image_id = payload(resp)['data']['id']
        resp = self.client.post(f'/api/admin/ad-images/{image_id}/upload/', {'file': bad, 'position': 'image'})
        self.assertEqual(resp.status_code, 400)


class ConfigApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        self.client.force_authenticate(self.user)

    def test_list_masks_content_detail_reveals(self):
        SysConfig.objects.create(name='TTS密钥', code='tts_ak_sk', content='super-secret-value')
        resp = self.client.get('/api/admin/configs/')
        self.assertEqual(payload(resp)['data']['items'][0]['content'], '******')

        pk = SysConfig.objects.get(code='tts_ak_sk').pk
        resp = self.client.get(f'/api/admin/configs/{pk}/')
        self.assertEqual(payload(resp)['data']['content'], 'super-secret-value')

    def test_duplicate_code_rejected(self):
        SysConfig.objects.create(name='a', code='dup')
        resp = self.client.post('/api/admin/configs/', {'name': 'b', 'code': 'dup'}, format='json')
        self.assertEqual(resp.status_code, 400)


class DashboardTests(TestCase):
    def setUp(self):
        self.super_client = APIClient()
        self.op_client = APIClient()
        User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        User.objects.create_user('op', 'op123456', role=User.ROLE_OPERATOR, permissions=['card:view'])
        self._login(self.super_client, 'boss', 'boss123456')
        self._login(self.op_client, 'op', 'op123456')

    def _login(self, client, username, password):
        resp = client.post('/api/auth/login', {'username': username, 'password': password}, format='json')
        client.credentials(HTTP_AUTHORIZATION="Bearer " + payload(resp)['data']['token'])

    def test_dashboard_requires_super(self):
        self.assertEqual(self.op_client.get('/api/admin/dashboard/stats').status_code, 403)
        resp = self.super_client.get('/api/admin/dashboard/stats')
        self.assertEqual(resp.status_code, 200)
        data = payload(resp)['data']
        self.assertIn('cards', data)
        self.assertIn('trend', data)
        self.assertEqual(len(data['trend']['days']), 7)
