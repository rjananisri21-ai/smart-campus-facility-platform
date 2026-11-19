import pymysql

# Configure PyMySQL as MySQL driver for Django BEFORE importing any Django MySQL backend modules
pymysql.install_as_MySQLdb()

from django.db.backends.mysql.features import DatabaseFeatures

# Enable compatibility with MySQL 8.0 (default LTS version installed with MySQL Workbench)
DatabaseFeatures.minimum_database_version = property(
    lambda self: (10, 11) if self.connection.mysql_is_mariadb else (8, 0)
)
