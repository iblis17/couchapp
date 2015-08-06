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
def test_init_dest_none(mock_doc, mock_cwd):
    commands.init(None, None)


def test_push_outside():
    '''
    $ couchapp push /path/to/app
    '''
    pass


@patch('couchapp.commands.document', return_value='{"status": "ok"}')
def test_push_export_outside(mock_doc):
    '''
    $ couchapp push --export /path/to/app
    '''
    conf = Mock(name='conf')
    appdir = '/mock_dir'

    commands.push(conf, None, appdir, export=True)
    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    conf.update.assert_called_once_with(appdir)


@patch('couchapp.commands.document', return_value='{"status": "ok"}')
def test_push_export_inside(mock_doc):
    '''
    In the app dir::

    $ couchapp push --export
    '''
    conf = Mock(name='conf')
    appdir = '/mock_dir'

    commands.push(conf, appdir, export=True)
    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    conf.update.assert_called_once_with(appdir)
