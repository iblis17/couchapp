# -*- coding: utf-8 -*-

from couchapp import commands
from couchapp.errors import AppError
from couchapp.localdoc import document

from mock import Mock, NonCallableMock, patch
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


@patch('couchapp.commands.hook')
@patch('couchapp.commands.document', spec=document)
def test_push_outside(mock_doc, mock_hook):
    '''
    $ couchapp push /path/to/app dest
    '''
    conf = NonCallableMock(name='conf')
    path = None
    appdir = '/mock_dir'
    dest = 'http://localhost'
    hook_expect = [
        ((conf, appdir, 'pre-push'), {'dbs': dest}),
        ((conf, appdir, 'post-push'), {'dbs': dest}),
    ]

    conf.get_dbs.return_value = dest

    commands.push(conf, path, appdir, dest)
    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    mock_doc().push.assert_called_once_with(dest, False, False, False)
    assert mock_hook.call_args_list == hook_expect


@patch('couchapp.commands.document', return_value='{"status": "ok"}',
       spec=document)
def test_push_export_outside(mock_doc):
    '''
    $ couchapp push --export /path/to/app
    '''
    conf = NonCallableMock(name='conf')
    appdir = '/mock_dir'

    commands.push(conf, None, appdir, export=True)
    mock_doc.assert_called_once_with(appdir, create=False, docid=None)


@patch('couchapp.commands.document', return_value='{"status": "ok"}',
       spec=document)
def test_push_export_inside(mock_doc):
    '''
    In the app dir::

    $ couchapp push --export
    '''
    conf = NonCallableMock(name='conf')
    appdir = '/mock_dir'

    commands.push(conf, appdir, export=True)
    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
