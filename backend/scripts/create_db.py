"""创建 MySQL 数据库（utf8mb4）。用法：venv/Scripts/python scripts/create_db.py"""
import os
import sys
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_NAME = os.environ.get('DJANGO_DB_NAME', 'vidsail')
DB_USER = os.environ.get('DJANGO_DB_USER', 'root')
DB_PASSWORD = os.environ.get('DJANGO_DB_PASSWORD', 'root')
DB_HOST = os.environ.get('DJANGO_DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DJANGO_DB_PORT', '3306'))

conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, charset='utf8mb4')
try:
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 "
            f"COLLATE utf8mb4_unicode_ci")
        cur.execute('SELECT VERSION()')
        version = cur.fetchone()[0]
    conn.commit()
    print(f'数据库 {DB_NAME} 已就绪，MySQL 版本 {version}')
finally:
    conn.close()
