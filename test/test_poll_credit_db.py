import os
import tomllib
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import mysql.connector

from gdo.poll.method.create import create


@unittest.skipUnless(os.environ.get('PYGDO_POLL_DB_TEST') == '1', 'requires isolated MySQL test config')
class PollCreditDatabaseTest(unittest.IsolatedAsyncioTestCase):
    async def test_debit_is_rolled_back_if_poll_insert_fails(self):
        config_path = Path(__file__).resolve().parents[3] / 'protected' / 'config_test.toml'
        config = tomllib.loads(config_path.read_text())['db']
        if config['name'] != 'pygdo_test':
            self.fail('Unexpected test database')
        connection = mysql.connector.connect(host=config['host'], port=int(config['port']),
                                             user=config['user'], password=config['pass'], database=config['name'])
        self.addCleanup(connection.close)
        cursor = connection.cursor(buffered=True)
        self.addCleanup(cursor.close)
        cursor.execute('CREATE TEMPORARY TABLE gdo_module (module_id INT PRIMARY KEY, module_name VARCHAR(32)) ENGINE=InnoDB')
        cursor.execute('CREATE TEMPORARY TABLE gdo_usersetting (uset_user INT, uset_key VARCHAR(32), uset_val VARCHAR(32), PRIMARY KEY (uset_user, uset_key)) ENGINE=InnoDB')
        cursor.execute("INSERT INTO gdo_module VALUES (1, 'poll')")
        cursor.execute("INSERT INTO gdo_usersetting VALUES (42, 'credits', '100')")
        connection.commit()

        class DB:
            def select(self, sql):
                cursor.execute(sql)
                return type('Result', (), {'fetch_row': lambda self: cursor.fetchone()})()

            def query(self, sql):
                cursor.execute(sql)
                return cursor

        method = create.__new__(create)
        method._env_user = MagicMock()
        method._env_user.get_id.return_value = '42'
        method._env_user._vals = {'credits': '100'}
        method.param_value = MagicMock(side_effect=lambda key: {
            'choices': ['One', 'Two'], 'min_answers': 1, 'max_answers': 1, 'duration_days': 3,
        }[key])
        method.param_val = MagicMock(side_effect=lambda key: {
            'title': 'Paid', 'question': '', 'min_answers': '1', 'max_answers': '1',
        }[key])
        with patch('gdo.poll.method.create.GDO_Poll') as poll, \
             patch('gdo.poll.method.create.module_poll') as module, \
             patch('gdo.poll.method.create.Application.db', return_value=DB()), \
             patch('gdo.poll.method.create.module_enabled', return_value=True), \
             patch('gdo.core.GDO_UserSetting.GDO_UserSetting.quote', return_value="'42'"):
            query = poll.table.return_value.select.return_value.where.return_value
            query.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            query.order.return_value.first.return_value.nocache.return_value.exec.return_value.fetch_object.return_value = None
            module.instance.return_value.get_config_value.return_value = 5
            poll.blank.return_value.insert.side_effect = RuntimeError('simulated insert failure')
            connection.start_transaction()
            with self.assertRaisesRegex(RuntimeError, 'simulated insert failure'):
                await method.form_submitted()
            cursor.execute("SELECT uset_val FROM gdo_usersetting WHERE uset_user=42 AND uset_key='credits'")
            self.assertEqual('85', cursor.fetchone()[0])
            connection.rollback()
            cursor.execute("SELECT uset_val FROM gdo_usersetting WHERE uset_user=42 AND uset_key='credits'")
            self.assertEqual('100', cursor.fetchone()[0])
