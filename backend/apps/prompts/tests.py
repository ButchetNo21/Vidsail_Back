import json

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.prompts.models import Category, Prompt, Tag


def payload(resp):
    return json.loads(resp.content)


class PromptApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('boss', 'boss123456', role=User.ROLE_SUPER)
        self.client.force_authenticate(self.user)
        self.cat1 = Category.objects.create(name='写作')
        self.cat2 = Category.objects.create(name='编程')
        self.tag1 = Tag.objects.create(name='热门')

    def _create(self, **overrides):
        data = {
            'name': '测试提示词',
            'content': '第一行\n第二行\n{换行保留}',
            'category_ids': [self.cat1.id, self.cat2.id],
            'tag_ids': [self.tag1.id],
        }
        data.update(overrides)
        return self.client.post('/api/admin/prompts/', data, format='json')

    def test_create_with_newlines_and_relations(self):
        resp = self._create()
        self.assertEqual(resp.status_code, 201)
        data = payload(resp)['data']
        prompt = Prompt.objects.get(pk=data['id'])
        self.assertIn('\n', prompt.content)
        self.assertEqual(prompt.categories.count(), 2)
        self.assertEqual(prompt.tags.count(), 1)
        self.assertEqual(prompt.created_by, self.user)

    def test_max_three_categories_and_tags(self):
        cats = [Category.objects.create(name=f'c{i}') for i in range(4)]
        resp = self._create(category_ids=[c.id for c in cats])
        self.assertEqual(resp.status_code, 400)

        tags = [Tag.objects.create(name=f't{i}') for i in range(4)]
        resp = self._create(tag_ids=[t.id for t in tags])
        self.assertEqual(resp.status_code, 400)

    def test_link_must_be_url(self):
        resp = self._create(link='not-a-url')
        self.assertEqual(resp.status_code, 400)
        resp = self._create(link='https://example.com/doc')
        self.assertEqual(resp.status_code, 201)

    def test_update_sets_updated_by(self):
        resp = self._create()
        pk = payload(resp)['data']['id']
        resp = self.client.patch(f'/api/admin/prompts/{pk}/', {'name': '改名了'}, format='json')
        prompt = Prompt.objects.get(pk=pk)
        self.assertEqual(prompt.name, '改名了')
        self.assertEqual(prompt.updated_by, self.user)

    def test_soft_delete_hides_from_list(self):
        resp = self._create()
        pk = payload(resp)['data']['id']
        resp = self.client.delete(f'/api/admin/prompts/{pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(Prompt.objects.filter(pk=pk).first())
        self.assertIsNotNone(Prompt.all_objects.get(pk=pk).deleted_at)
        resp = self.client.get('/api/admin/prompts/')
        self.assertEqual(payload(resp)['data']['total'], 0)

    def test_filter_by_keyword_and_category(self):
        self._create(name='小红书文案')
        self._create(name='完全不同')
        resp = self.client.get('/api/admin/prompts/?keyword=小红书')
        self.assertEqual(payload(resp)['data']['total'], 1)
        resp = self.client.get(f'/api/admin/prompts/?category_id={self.cat1.id}')
        self.assertEqual(payload(resp)['data']['total'], 2)

    def test_category_delete_blocked_when_in_use(self):
        resp = self._create()
        resp = self.client.delete(f"/api/admin/categories/{self.cat1.id}/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn('正在被提示词使用', payload(resp)['message'])
