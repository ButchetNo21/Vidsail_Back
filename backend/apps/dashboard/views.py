from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ads.models import AdImage, AdSlot
from apps.cards.models import CardKey, CardLog, Device
from apps.cards.serializers import CardLogSerializer
from apps.configs.models import SysConfig
from apps.core.permissions import IsSuperAdmin
from apps.prompts.models import Prompt


class DashboardStatsView(APIView):
    """首页仪表盘统计（仅超级管理员）。"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        not_expired = Q(end_time__isnull=True) | Q(end_time__gte=now)

        cards = CardKey.objects.all()
        status_counts = {
            'unbound': cards.filter(status=CardKey.STATUS_UNBOUND).filter(not_expired).count(),
            'bound': cards.filter(status=CardKey.STATUS_BOUND).filter(not_expired).count(),
            'expired': cards.filter(~Q(status=CardKey.STATUS_INVALID), end_time__lt=now).count(),
            'invalid': cards.filter(status=CardKey.STATUS_INVALID).count(),
        }

        # 近7天：生成趋势 + 绑定趋势
        days, card_trend, bind_trend = [], [], []
        for offset in range(6, -1, -1):
            day_start = today - timedelta(days=offset)
            day_end = day_start + timedelta(days=1)
            label = day_start.strftime('%m-%d')
            days.append(label)
            card_trend.append(cards.filter(created_at__gte=day_start, created_at__lt=day_end).count())
            bind_trend.append(CardLog.objects.filter(
                action=CardLog.ACTION_BIND, created_at__gte=day_start, created_at__lt=day_end).count())

        recent_logs = CardLogSerializer(
            CardLog.objects.select_related('card').all()[:10], many=True).data

        return Response({
            'cards': {
                'total': cards.count(),
                'today_new': cards.filter(created_at__gte=today).count(),
                **status_counts,
            },
            'counts': {
                'devices': Device.objects.count(),
                'prompts': Prompt.objects.count(),
                'ad_slots': AdSlot.objects.count(),
                'ad_images': AdImage.objects.count(),
                'configs': SysConfig.objects.count(),
            },
            'trend': {'days': days, 'card_created': card_trend, 'card_bound': bind_trend},
            'recent_logs': recent_logs,
        })
