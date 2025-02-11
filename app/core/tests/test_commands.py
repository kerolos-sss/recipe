from unittest.mock import patch

from django.core.management import call_command

from psycopg2 import OperationalError as Psycopg2OperationalError
from django.db.utils import OperationalError

from django.test import SimpleTestCase


@patch("core.management.commands.wait_for_db.Command.check")
class CommandTests(SimpleTestCase):

    def test_wait_for_db_ready(self, mocked_check):
        """Test waiting for db when db is available"""
        mocked_check.return_value = True
        call_command("wait_for_db")
        mocked_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(self, _mocked_sleep, mocked_check):
        """Test waiting for db when getting OperationalError 5 times then it's ready"""
        mocked_check.side_effect = (
            [Psycopg2OperationalError] * 3 + [OperationalError] * 2 + [True]
        )
        call_command("wait_for_db")
        self.assertEqual(mocked_check.call_count, 6)
        mocked_check.assert_called_with(databases=["default"])
