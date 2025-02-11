"""
Django command to wait for database to be available.
"""

import time
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def handle(self, *args, **options):
        """Entry point for the command"""
        self.stdout.write("Waiting for database...")
        db_up = False   
        while not db_up:
            try:
                self.check(databases=["default"])
                db_up = True
            except (OperationalError, Psycopg2OperationalError) as e:
                print(e)
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)
        
        self.stdout.write(self.style.SUCCESS("Database available!"))
        