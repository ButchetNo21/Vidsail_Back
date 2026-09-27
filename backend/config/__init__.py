"""
项目配置包。
在此处安装 PyMySQL 并伪装成 MySQLdb，保证 Django 能用 MySQL。
"""
import pymysql

pymysql.install_as_MySQLdb()
