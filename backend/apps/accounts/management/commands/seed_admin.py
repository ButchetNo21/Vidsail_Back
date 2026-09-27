from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = '创建/重置超级管理员账号'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')

    def handle(self, *args, **options):
        username, password = options['username'], options['password']
        user, created = User.all_objects.get_or_create(
            username=username, defaults={'role': User.ROLE_SUPER})
        user.role = User.ROLE_SUPER
        user.is_active = True
        user.set_password(password)
        user.save()
        action = '已创建' if created else '密码已重置'
        self.stdout.write(self.style.SUCCESS(f'超级管理员 {username} {action}，密码: {password}'))
