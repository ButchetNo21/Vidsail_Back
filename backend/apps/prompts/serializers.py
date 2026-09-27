from django.core.validators import URLValidator
from rest_framework import serializers

from apps.core.exceptions import ValidationError
from apps.prompts.models import Category, Prompt, Tag


class CategorySerializer(serializers.ModelSerializer):
    prompt_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ['id', 'name', 'sort', 'status', 'prompt_count', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    prompt_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'sort', 'status', 'prompt_count', 'created_at', 'updated_at']


class PromptSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, default='')
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all(), source='categories', required=False)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), source='tags', required=False)

    class Meta:
        model = Prompt
        fields = [
            'id', 'name', 'content', 'link', 'category_ids', 'tag_ids',
            'categories', 'tags', 'status',
            'created_by_name', 'updated_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['categories', 'tags']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category_ids'] = [c.id for c in instance.categories.all()]
        data['tag_ids'] = [t.id for t in instance.tags.all()]
        data['categories'] = [{'id': c.id, 'name': c.name} for c in instance.categories.all()]
        data['tags'] = [{'id': t.id, 'name': t.name} for t in instance.tags.all()]
        return data

    def _validate_max3(self, attrs, field, label):
        items = attrs.get(field)
        if items and len(items) > 3:
            raise ValidationError(f'{label}最多选择3个')
        return items

    def validate_link(self, value):
        if value:
            validator = URLValidator(schemes=['http', 'https'])
            validator(value)
        return value

    def validate(self, attrs):
        self._validate_max3(attrs, 'categories', '分类')
        self._validate_max3(attrs, 'tags', '标签')
        return attrs
