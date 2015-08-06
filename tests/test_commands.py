# -*- coding: utf-8 -*-

from couchapp import commands
from couchapp.errors import AppError

from mock import Mock, patch
from nose.tools import raises


@patch('couchapp.commands.document')
def test_init_dest(mock_doc):
    commands.init(None, None, '/tmp/mk')
    mock_doc.assert_called_once_with('/tmp/mk', create=True)


@patch('os.getcwd', return_value='/mock_dir')
@patch('couchapp.commands.document')
def test_init_dest_auto(mock_doc, mock_cwd):
    commands.init(None, None)
    mock_doc.assert_called_once_with('/mock_dir', create=True)


@raises(AppError)
@patch('os.getcwd', return_value=None)
@patch('couchapp.commands.document')
def test_init_dest_auto(mock_doc, mock_cwd):
    commands.init(None, None)
