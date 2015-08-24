# -*- coding: utf-8 -*-

import os

from couchapp import commands
from couchapp.errors import AppError, BulkSaveError
from couchapp.localdoc import document

from mock import MagicMock, Mock, NonCallableMock, patch
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

    ret_code = commands.pushapps(conf, '/mock_dir', dest, export=True, output='file')

    assert ret_code == 0
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

    ret_code = commands.pushapps(conf, '/mock_dir', dest, export=True, output='file')

    assert ret_code == 0
    discover_apps_.assert_called_with('/mock_dir')
    assert not hook.called
    assert not document_.called
    assert not write_json.called


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

    ret_code = commands.pushapps(conf, '/mock_dir', dest, export=True)

    assert ret_code == 0
    discover_apps_.assert_called_with('/mock_dir')
    hook.assert_any_call(conf, 'foo', 'pre-push',
                         dbs=conf.get_dbs(), pushapps=True)
    hook.assert_any_call(conf, 'foo', 'post-push',
                         dbs=conf.get_dbs(), pushapps=True)
    assert dumps.called


@patch('couchapp.commands.document', spec=document)
@patch('couchapp.commands.hook')
@patch('couchapp.commands.util.discover_apps', return_value=['foo'])
def test_pushapps_noatomic(discover_apps_, hook, document_):
    '''
    Test case for pushapps with ``--no-atomic``

    Algo:
    1. discover apps

    #. for each app
        1. pre-push
        2. push
        3. post-push
    '''
    conf = NonCallableMock(name='conf')
    dest = 'http://localhost:5984'
    doc = document_()
    dbs = conf.get_dbs()

    ret_code = commands.pushapps(conf, '/mock_dir', dest, no_atomic=True)
    assert ret_code == 0
    conf.get_dbs.assert_called_with(dest)
    hook.assert_any_call(conf, 'foo', 'pre-push', dbs=dbs, pushapps=True)
    hook.assert_any_call(conf, 'foo', 'post-push', dbs=dbs, pushapps=True)
    doc.push.assert_called_with(dbs, True, False)


@patch('couchapp.commands.document', spec=document)
@patch('couchapp.commands.hook')
@patch('couchapp.commands.util.discover_apps', return_value=['foo'])
def test_pushapps_default(discover_apps_, hook, document_):
    '''
    Test case for ``pushapps {path}`` with default flags

    Algo:
    1. discover apps

    #. for each app
        1. pre-push
        2. add to list apps
        3. post-push

    #. for each db
        1. db.save_docs
    '''
    conf = NonCallableMock(name='conf')
    dest = 'http://localhost:5984'
    doc = document_()
    db = Mock(name='db')
    dbs = MagicMock(name='dbs')
    dbs.__iter__.return_value = iter([db])
    conf.get_dbs.return_value = dbs

    ret_code = commands.pushapps(conf, '/mock_dir', dest)
    assert ret_code == 0
    conf.get_dbs.assert_called_with(dest)
    hook.assert_any_call(conf, 'foo', 'pre-push', dbs=dbs, pushapps=True)
    hook.assert_any_call(conf, 'foo', 'post-push', dbs=dbs, pushapps=True)
    assert db.save_docs.called


def test_version_help():
    '''
    $ couchapp version -h
    '''
    assert commands.version(Mock(), help=True) == 0


def test_help_version():
    '''
    $ couchapp -h --version
    '''
    assert commands.usage(Mock(), version=True) == 0


@patch('couchapp.commands.hook')
@patch('couchapp.commands.clone_app.clone')
def test_clone_default(clone, hook):
    '''
    $ couchapp clone {source}
    '''
    conf = NonCallableMock(name='conf')
    src = 'http://localhost:5984/test'
    dest = None

    ret_code = commands.clone(conf, src)
    assert ret_code == 0
    hook.assert_any_call(conf, dest, 'pre-clone', source=src)
    clone.assert_called_with(src, None, rev=None)
    hook.assert_any_call(conf, dest, 'post-clone', source=src)


@patch('couchapp.commands.os.getcwd', return_value='/')
@patch('couchapp.commands.generator.generate')
def test_startapp_default(generate, getcwd):
    '''
    $ couchapp startapp {name}
    '''
    conf = NonCallableMock(name='conf')
    name = 'mock'

    ret_code = commands.startapp(conf, name)
    assert ret_code == 0
    generate.assert_called_with('/mock', 'startapp', name)


@patch('couchapp.commands.os.getcwd')
@patch('couchapp.commands.generator.generate')
def test_startapp_default(generate, getcwd):
    '''
    $ couchapp startapp {dir} {name}
    '''
    conf = NonCallableMock(name='conf')
    dir_ = '/'
    name = 'mock'

    ret_code = commands.startapp(conf, dir_, name)
    assert ret_code == 0
    assert not getcwd.called
    generate.assert_called_with('/mock', 'startapp', name)


@raises(AppError)
@patch('couchapp.commands.os.getcwd', return_value='/')
@patch('couchapp.commands.generator.generate')
def test_startapp_without_name(generate, getcwd):
    '''
    $ couchapp startapp
    '''
    conf = NonCallableMock(name='conf')

    ret_code = commands.startapp(conf)
    assert not generate.called


@raises(AppError)
@patch('couchapp.commands.util.iscouchapp', return_value=True)
@patch('couchapp.commands.os.getcwd', return_value='/')
@patch('couchapp.commands.generator.generate')
def test_startapp_exists(generate, getcwd, iscouchapp):
    '''
    $ couchapp startapp {already exists app}
    '''
    conf = NonCallableMock(name='conf')

    ret_code = commands.startapp(conf)
    assert not generate.called


@raises(AppError)
@patch('couchapp.commands.util.iscouchapp', return_value=True)
@patch('couchapp.commands.os.getcwd', return_value='/')
@patch('couchapp.commands.generator.generate')
def test_startapp_exists(generate, getcwd, iscouchapp):
    '''
    $ couchapp startapp {already exists app}
    '''
    conf = NonCallableMock(name='conf')
    name = 'mock'

    ret_code = commands.startapp(conf, name)
    assert iscouchapp.assert_called_with('/mock')
    assert not generate.called


@raises(AppError)
@patch('couchapp.commands.util.findcouchapp', return_value=True)
@patch('couchapp.commands.util.iscouchapp', return_value=False)
@patch('couchapp.commands.os.getcwd', return_value='/')
@patch('couchapp.commands.generator.generate')
def test_startapp_inside_app(generate, getcwd, iscouchapp, findcouchapp):
    '''
    $ couchapp startapp {path in another app}

    e.g. Assume there is a couchapp ``app1``

    ::
        app1/
            .couchapprc
            ...

    We try to ``couchapp startapp app1/app2``,
    and this should raise `AppError`.
    '''
    conf = NonCallableMock(name='conf')
    name = 'mock'

    ret_code = commands.startapp(conf, name)
    assert findcouchapp.assert_called_with('/mock')
    assert not generate.called


@patch('couchapp.commands.util.iscouchapp', return_value=True)
@patch('couchapp.commands.document')
def test_browse_default(document, iscouchapp):
    '''
    $ couchapp browse {app} {db url}
    '''
    conf = NonCallableMock(name='conf')
    app = '/mock_dir'
    dest = 'http://localhost:5984'
    doc = document()

    ret_code = commands.browse(conf, app, dest)
    iscouchapp.assert_called_with('/mock_dir')
    assert doc.browse.called


@patch('os.getcwd', return_value='/mock_dir/app')
@patch('couchapp.commands.util.iscouchapp', return_value=True)
@patch('couchapp.commands.document')
def test_browse_dest_only(document, iscouchapp, getcwd):
    '''
    $ couchapp browse {db url}
    '''
    conf = NonCallableMock(name='conf')
    dest = 'http://localhost:5984'
    doc = document()

    ret_code = commands.browse(conf, dest)
    iscouchapp.assert_called_with('/mock_dir/app')
    assert doc.browse.called


@raises(AppError)
@patch('couchapp.commands.util.iscouchapp', return_value=False)
@patch('couchapp.commands.document')
def test_browse_exist(document, iscouchapp):
    '''
    $ couchapp browse {not app dir} {db url}
    '''
    conf = NonCallableMock(name='conf')
    app = '/mock_dir/notapp'
    dest = 'http://localhost:5984'
    doc = document()

    ret_code = commands.browse(conf, app, dest)
    iscouchapp.assert_called_with('/mock_dir/notapp')
    assert not doc.browse.called


@raises(AppError)
def test_generate_inside():
    '''
    $ couchapp generate app {path inside another app}

    This should raise AppError.
    '''
    conf = NonCallableMock(name='conf')
    app = '/mock/app'

    commands.generate(conf, app, 'app', 'mockapp')


@raises(AppError)
def test_generate_miss_name():
    '''
    $ couchapp generate

    This should raise AppError.
    '''
    conf = NonCallableMock(name='conf')
    app = '/mock/app'

    commands.generate(conf, app)


@raises(AppError)
def test_generate_view_without_app():
    '''
    $ couchapp generate view myview

    But outside app dir.
    This should raise AppError.
    '''
    conf = NonCallableMock(name='conf')

    commands.generate(conf, None, 'view', 'myview')


@patch('couchapp.commands.os.getcwd', return_value='/mock')
@patch('couchapp.commands.generator.generate')
@patch('couchapp.commands.hook')
def test_generate_app(hook, generate, getcwd):
    '''
    $ couchapp generate myapp
    '''
    conf = NonCallableMock(name='conf')
    kind = 'app'
    name = 'myapp'

    ret_code = commands.generate(conf, None, name)
    assert ret_code == 0
    generate.assert_called_with('/mock/myapp', kind, name, create=True)
    hook.assert_any_call(conf, '/mock/myapp', 'pre-generate')
    hook.assert_any_call(conf, '/mock/myapp', 'post-generate')


@patch('couchapp.commands.os.getcwd', return_value='/mock')
@patch('couchapp.commands.generator.generate')
@patch('couchapp.commands.hook')
def test_generate_view_outside_app(hook, generate, getcwd):
    '''
    $ couchapp generate view myapp myview
    '''
    conf = NonCallableMock(name='conf')
    kind = 'view'
    dest = 'myapp'
    name = 'myview'

    ret_code = commands.generate(conf, None, kind, dest, name)
    assert ret_code == 0
    generate.assert_called_with(dest, kind, name)
    hook.assert_any_call(conf, dest, 'pre-generate')
    hook.assert_any_call(conf, dest, 'post-generate')
