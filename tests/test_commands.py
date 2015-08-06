# -*- coding: utf-8 -*-

import unittest2 as unittest

from couchapp import commands
from mock import Mock, patch


class CommandsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('couchapp.commands.document')
    def test_init_dest(self, mock_doc):
        commands.init(None, None, '/tmp/mk')
        mock_doc.assert_called_once_with('/tmp/mk', create=True)

    @patch('os.getcwd', return_value='/mock_dir')
    @patch('couchapp.commands.document')
    def test_init_dest_auto(self, mock_doc, mock_cwd):
        commands.init(None, None)
        mock_doc.assert_called_once_with('/mock_dir', create=True)


if __name__ == '__main__':
    unittest.main()
