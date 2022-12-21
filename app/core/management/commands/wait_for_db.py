"""
Django commnad to wait for the database to be available
"""
from django.core.management.base import BaseCommand
from time import sleep
from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for the database"""

    def handle(self, *args, **options):
        """Entrypoint for commands"""
        self.stdout.write('waiting for Database')
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write('Database Unavailable, waiting 1 sec')
                sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))
