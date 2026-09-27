from django.db.models import Q, Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins

from apps.core.exceptions import ValidationError
from apps.core.views import PermViewSet, apply_ordering, parse_date_param
from apps.prompts.models import Category, Prompt, Tag
from apps.prompts.serializers import CategorySerializer, PromptSerializer, TagSerializer


class PromptViewSet(PermViewSet):
    perm_map = {
        'list': 'prompt:view', 'retrieve': 'prompt:view',
        'create': 'prompt:edit', 'update': 'prompt:edit', 'partial_update': 'prompt:edit',
        'destroy': 'prompt:delete',
    }
    queryset = Prompt.objects.prefetch_related('categories', 'tags').all()
    serializer_class = PromptSerializer

    def filter_queryset(self, qs):
        params = self.request.query_params
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(Q(name__icontains=keyword) | Q(content__icontains=keyword))
        category_id = params.get('category_id')
        if category_id and category_id.isdigit():
            qs = qs.filter(categories__id=int(category_id))
        tag_id = params.get('tag_id')
        if tag_id and tag_id.isdigit():
            qs = qs.filter(tags__id=int(tag_id))
        status_value = params.get('status')
        if status_value in ('0', '1'):
            qs = qs.filter(status=int(status_value))
        created_from = parse_date_param(params.get('created_from'))
        created_to = parse_date_param(params.get('created_to'), end_of_day=True)
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)
        return apply_ordering(qs, self.request, {'created_at', 'name'}, ['-id'])

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()  # 软删除
        return Response({'id': instance.pk, 'deleted': True}, status=status.HTTP_200_OK)


class _TermMixin:
    """分类/标签通用逻辑。"""

    def get_queryset(self):
        return (self.queryset_model.objects
                .annotate(prompt_count=Count('prompts', distinct=True)))

    def filter_queryset(self, qs):
        params = self.request.query_params
        keyword = (params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        status_value = params.get('status')
        if status_value in ('0', '1'):
            qs = qs.filter(status=int(status_value))
        return qs

    def perform_destroy(self, instance):
        if instance.prompts.exists():
            raise ValidationError(f'{self.label}正在被提示词使用，请先解除引用')
        instance.delete()


class CategoryViewSet(_TermMixin, PermViewSet):
    perm_map = {
        'list': 'category:view', 'retrieve': 'category:view',
        'create': 'category:edit', 'update': 'category:edit', 'partial_update': 'category:edit',
        'destroy': 'category:edit',
    }
    queryset_model = Category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    label = '分类'


class TagViewSet(_TermMixin, PermViewSet):
    perm_map = {
        'list': 'category:view', 'retrieve': 'category:view',
        'create': 'tag:edit', 'update': 'tag:edit', 'partial_update': 'tag:edit',
        'destroy': 'tag:edit',
    }
    queryset_model = Tag
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    label = '标签'
