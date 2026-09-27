"""演示数据：分类/标签/提示词/卡密/广告位/配置，方便首次运行验收页面。"""
import base64
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.ads.models import AdImage, AdSlot
from apps.cards.models import CardKey, Device
from apps.cards.keys import generate_card_key
from apps.configs.models import SysConfig
from apps.prompts.models import Category, Prompt, Tag

# 1x1 灰色 PNG 占位图
PNG_1PX = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')


class Command(BaseCommand):
    help = '写入演示数据（可重复执行，按唯一键去重）'

    def handle(self, *args, **options):
        now = timezone.now()

        cats = []
        for name in ['写作助手', '编程助手', '营销文案']:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'sort': 0})
            cats.append(cat)
        tags = []
        for name in ['效率', '创意', '热门', '长文']:
            tag, _ = Tag.objects.get_or_create(name=name, defaults={'sort': 0})
            tags.append(tag)

        demo_prompts = [
            ('小红书爆款文案', '你是一个资深小红书运营。\n请根据主题生成一篇爆款笔记：\n1. 标题带emoji\n2. 正文300字左右\n3. 结尾带3个话题标签', '#'),
            ('代码评审助手', '你是资深代码评审员。\n收到代码后请输出：\n- 潜在缺陷\n- 性能问题\n- 命名与可读性建议', ''),
            ('周报生成器', '根据我提供的工作要点，生成一份结构化周报：\n本周完成 / 数据表现 / 下周计划', ''),
        ]
        for i, (name, content, link) in enumerate(demo_prompts):
            prompt, created = Prompt.objects.get_or_create(
                name=name, defaults={'content': content, 'link': link, 'status': 1})
            if created:
                prompt.categories.set(random.sample(cats, k=min(2, len(cats))))
                prompt.tags.set(random.sample(tags, k=min(2, len(tags))))

        # 设备 + 卡密
        devices = []
        for i in range(3):
            device, _ = Device.objects.get_or_create(code=f'DEV-DEMO-{i:04d}-CLIENT')
            devices.append(device)

        created_cards = 0
        for i in range(24):
            key = generate_card_key()
            card = CardKey.objects.create(
                key=key,
                start_time=now - timedelta(days=1),
                end_time=now + timedelta(days=random.choice([7, 30, 90])),
                amount=random.choice([9.9, 19.9, 49.9, 99]),
                remark=f'演示卡密 #{i + 1}',
            )
            created_cards += 1
            if i < 8:  # 绑定
                card.device = devices[i % len(devices)]
                card.status = CardKey.STATUS_BOUND
                card.bound_at = now
                card.save()
            elif i == 8:  # 已过期
                card.end_time = now - timedelta(days=1)
                card.save()
            elif i == 9:  # 已失效
                card.status = CardKey.STATUS_INVALID
                card.save()

        # 广告位 + 图片
        slot, _ = AdSlot.objects.get_or_create(
            name='首页轮播', code='home_banner',
            defaults={'remark': '客户端首页轮播广告位', 'start_time': now, 'end_time': now + timedelta(days=365)})
        if slot.images.count() == 0:
            for i, name in enumerate(['新品推广', '会员优惠']):
                img = AdImage.objects.create(
                    slot=slot, name=name, subtitle=f'副标题 {i + 1}', remark='演示图片（1px占位图，请上传替换）',
                    url='https://example.com', start_time=now, end_time=now + timedelta(days=30))
                img.image.save(f'demo_{i}.png', ContentFile(PNG_1PX), save=True)

        SysConfig.objects.get_or_create(
            code='tts_ak_sk',
            defaults={'name': 'TTS服务密钥', 'content': '{"ak": "demo-ak-xxxx", "sk": "demo-sk-xxxx"}',
                      'remark': '演示配置，请替换为真实密钥'})
        SysConfig.objects.get_or_create(
            code='cdn_domain',
            defaults={'name': 'CDN加速域名', 'content': 'https://cdn.example.com', 'remark': '演示配置'})

        self.stdout.write(self.style.SUCCESS(
            f'演示数据完成：分类{Category.objects.count()} 标签{Tag.objects.count()} '
            f'提示词{Prompt.objects.count()} 新增卡密{created_cards} 设备{Device.objects.count()}'))
