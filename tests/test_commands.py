# -*- coding: utf-8 -*-

import os

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

    ret_code = commands.push(conf, path, appdir, dest)

    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    mock_doc().push.assert_called_once_with(dest, False, False, False)
    assert mock_hook.call_args_list == hook_expect
    assert ret_code == 0


@patch('os.path.exists')
@patch('couchapp.commands.pushdocs', spec=commands.pushdocs)
@patch('couchapp.commands.hook')
@patch('couchapp.commands.document', spec=document)
def test_push_with_pushdocs(mock_doc, mock_hook, mock_pushdocs, mock_exists):
    '''
    if appdir/_docs exists, push will invoke pushdocs
    '''
    conf = NonCallableMock(name='conf')
    appdir = '/mock_dir'
    dest = 'http://localhost'
    docspath = os.path.join(appdir, '_docs')

    def check_docspath(docspath_):
        return docspath_ == docspath
    mock_exists.side_effect = check_docspath

    ret_code = commands.push(conf, appdir, dest)

    mock_pushdocs.assert_called_once_with(conf, docspath, dest, dest)
    assert ret_code == 0


@patch('couchapp.commands.document', spec=document)
def test_push_export_outside(mock_doc):
    '''
    $ couchapp push --export /path/to/app
    '''
    conf = NonCallableMock(name='conf')
    appdir = '/mock_dir'

    ret_code = commands.push(conf, None, appdir, export=True)

    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    assert ret_code == 0


@patch('couchapp.commands.document', spec=document)
def test_push_export_inside(mock_doc):
    '''
    In the app dir::

    $ couchapp push --export
    '''
    conf = NonCallableMock(name='conf')
    appdir = '/mock_dir'

    ret_code = commands.push(conf, appdir, export=True)

    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    assert ret_code == 0


@patch('couchapp.commands.util')
@patch('couchapp.commands.document', return_value='{"status": "ok"}',
       spec=document)
def test_push_export_to_file(mock_doc, mock_util):
    '''
    $ couchapp push --export --output /path/to/json /appdir
    '''
    conf = NonCallableMock(name='conf')
    appdir = '/mock_dir'
    output_file = '/file'

    ret_code = commands.push(conf, appdir, export=True, output=output_file)

    mock_doc.assert_called_once_with(appdir, create=False, docid=None)
    mock_util.write_json.assert_called_once_with(
        output_file,
        '{"status": "ok"}'
    )
    assert ret_code == 0


@raises(AppError)
def test_push_app_path_error():
    conf = NonCallableMock(name='conf')
    dest = 'http://localhost'

    commands.push(conf, None, dest)


@patch('couchapp.commands.util.write_json')
@patch('couchapp.commands.document', spec=document)
@patch('couchapp.commands.hook')
@patch('couchapp.commands.util.discover_apps', return_value=['foo'])
def test_pushapps_output(discover_apps_, hook, document_, write_json):
    '''
    Test case for pushapps with ``--export --output file``

    Algo:
    1. discover apps
    #. pre-push
    #. add app to a list ``apps``
    #. post-push
    #. write_json(apps)
    '''
    conf = NonCallableMock(name='conf')
    dest = None

    ret = commands.pushapps(conf, '/mock_dir', dest, export=True, output='file')

    assert ret == 0
    discover_apps_.assert_called_with('/mock_dir')
    hook.assert_any_call(conf, 'foo', 'pre-push',
                         dbs=conf.get_dbs(), pushapps=True)
    hook.assert_any_call(conf, 'foo', 'post-push',
                         dbs=conf.get_dbs(), pushapps=True)
    'file' in write_json.call_args[0]


@patch('couchapp.commands.util.write_json')
@patch('couchapp.commands.document', spec=document)
@patch('couchapp.commands.hook')
@patch('couchapp.commands.util.discover_apps', return_value=[])
def test_pushapps_output_null(discover_apps_, hook, document_, write_json):
    '''
    Test case for pushapps with ``--export --output file``,
    but no any apps discovered

    Algo: see :py:meth:`test_pushapps_output`
    '''
    conf = NonCallableMock(name='conf')
    dest = None

    ret = commands.pushapps(conf, '/mock_dir', dest, export=True, output='file')

    assert ret == 0
    discover_apps_.assert_called_with('/mock_dir')
    hook.assert_not_called()
    document_.assert_not_called()
    write_json.assert_not_called()


@patch('couchapp.commands.util.json.dumps')
@patch('couchapp.commands.document', spec=document)
@patch('couchapp.commands.hook')
@patch('couchapp.commands.util.discover_apps', return_value=['foo'])
def test_pushapps_export(discover_apps_, hook, document_, dumps):
    '''
    Test case for pushapps with ``--export``,

    Algo:
    1. discover apps
    #. pre-push
    #. add app to a list ``apps``
    #. post-push
    #. json.dumps from apps
    '''
    conf = NonCallableMock(name='conf')
    dest = None

    ret = commands.pushapps(conf, '/mock_dir', dest, export=True)

    assert ret == 0
    discover_apps_.assert_called_with('/mock_dir')
    hook.assert_any_call(conf, 'foo', 'pre-push',
                         dbs=conf.get_dbs(), pushapps=True)
    hook.assert_any_call(conf, 'foo', 'post-push',
                         dbs=conf.get_dbs(), pushapps=True)
    assert dumps.called
