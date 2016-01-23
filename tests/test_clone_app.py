# -*- coding: utf-8 -*-

from couchapp.clone_app import clone
from couchapp.errors import AppError, MissingContent

from mock import patch
from nose.tools import  raises


@raises(AppError)
def test_invalid_source():
    '''
    Test case for clone(invalid_source)

    If a source uri do not contain ``_design/``, it's invalid.
    '''
    clone('http://foo.bar')


class TestCloneMethod():
    '''
    Test cases for the internal-used method of ``clone``
    '''

    def setup(self):
        self.clone = object.__new__(clone)

    def teardown(self):
        del self.clone

    @patch('couchapp.clone_app.os.makedirs')
    def test_setup_dir(self, makedirs):
        assert self.clone.setup_dir('/tmp/mock')

    @patch('couchapp.clone_app.os.makedirs', side_effect=OSError)
    def test_setup_dir_failed(self, makedirs):
        assert self.clone.setup_dir('/tmp/mock') is False

    @patch('couchapp.clone_app.os.path.exists', return_value=True)
    @patch('couchapp.clone_app.os.makedirs')
    def test_setup_dir_exists(self, makedirs, exists):
        assert self.clone.setup_dir('/tmp/mock') is False
        assert makedirs.called is False

    @patch('couchapp.clone_app.os.path.exists')
    @patch('couchapp.clone_app.os.makedirs')
    def test_setup_dir_empty(self, makedirs, exists):
        assert self.clone.setup_dir('') is False
        assert exists.called is False
        assert makedirs.called is False

    @patch('couchapp.clone_app.os.getcwd', return_value='/mock')
    @patch('couchapp.clone_app.clone.setup_dir')
    def test_setup_path_cwd(self, setup_dir, getcwd):
        '''
        Test case for ``DEST`` not given

        We will use the current working dir.
        '''
        self.clone.dest = None

        self.clone.init_path()

        assert getcwd.called
        assert self.clone.path == '/mock'
        setup_dir.assert_called_with('/mock')

    @patch('couchapp.clone_app.os.getcwd', return_value='/tmp')
    @patch('couchapp.clone_app.clone.setup_dir')
    def test_setup_path_dest(self, setup_dir, getcwd):
        '''
        Test case for ``DEST`` given
        '''
        self.clone.dest = 'mock'

        self.clone.init_path()

        assert getcwd.called
        assert self.clone.path == '/tmp/mock'
        setup_dir.assert_called_with('/tmp/mock')

    def test_init_metadata(self):
        '''
        Test case for extract metadata from a ddoc
        '''
        self.clone.doc = {
            'couchapp': {
                'manifest': ['views/'],
                'signatures': {'mock': 'strange_value'},
                'objects': {'obj_hash': 'obj'}
            }
        }

        self.clone.init_metadata()

        assert 'views/' in self.clone.manifest
        assert 'mock' in self.clone.signatures
        assert 'obj_hash' in self.clone.objects

    def test_init_metadata_default(self):
        '''
        Test case for extract metadata from an empty ddoc

        Check the default contain correct type
        '''
        self.clone.doc = {
            'couchapp': {}
        }

        self.clone.init_metadata()

        assert self.clone.manifest == []
        assert self.clone.signatures == {}
        assert self.clone.objects == {}

    def test_pop_doc_str(self):
        '''
        Test case for pop str from ``clone.doc``
        '''
        path = ['mock.json']
        doc = {
            'mock': 'fake_data',
            'other': None
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == 'fake_data'
        assert doc == {'other': None}

    def test_pop_doc_unicode(self):
        '''
        Test case for pop unicode from ``clone.doc``
        '''
        path = ['mock.json']
        doc = {
            u'mock': u'fake_data'
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == u'fake_data'
        assert doc == {}

        path = [u'mock.json']
        doc = {
            u'mock': u'fake_data'
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == u'fake_data'
        assert doc == {}

        path = [u'mock.json']
        doc = {
            'mock': u'fake_data'
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == u'fake_data'
        assert doc == {}

    def test_pop_doc_int(self):
        '''
        Test case for pop int from ``clone.doc``
        '''
        path = ['truth.json']
        doc = {
            'truth': 42
        }
        ret = self.clone.pop_doc(path, doc)
        assert isinstance(ret, int)
        assert ret == 42
        assert doc == {}

    def test_pop_doc_float(self):
        '''
        Test case for pop float from ``clone.doc``
        '''
        path = ['truth.json']
        doc = {
            'truth': 42.0
        }
        ret = self.clone.pop_doc(path, doc)
        assert isinstance(ret, float)
        assert ret == 42.0
        assert doc == {}

    def test_pop_doc_list(self):
        '''
        Test case for pop list from ``clone.doc``
        '''
        path = ['mock.json']
        doc = {
            'mock': ['foo', 'bar']
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == ['foo', 'bar']
        assert doc == {}

    def test_pop_doc_none(self):
        '''
        Test case for pop ``None`` from ``clone.doc``

        Note that the None come from ``null`` value in json.
        '''
        path = ['mock.json']
        doc = {
            'mock': None
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret is None
        assert doc == {}

    def test_pop_doc_bool(self):
        '''
        Test case for pop boolean from ``clone.doc``
        '''
        path = ['mock.json']
        doc = {
            'mock': True
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret is True
        assert doc == {}

    def test_pop_doc_deep(self):
        '''
        Test case for pop data from deeper prop of ``clone.doc``
        '''
        path = ['shows', 'mock.js']
        doc = {
            'shows': {
                'mock': u'fake_script'
            }
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == u'fake_script'
        assert doc == {}

        path = ['shows.lol', 'mock.bak.js']
        doc = {
            'shows.lol': {
                'mock.bak': u'fake_script'
            }
        }
        ret = self.clone.pop_doc(path, doc)
        assert ret == u'fake_script'
        assert doc == {}

    @raises(MissingContent)
    def test_pop_doc_miss(self):
        '''
        Test case for pop a missing prop
        '''
        path = ['fake.json']
        doc = {
            'mock': 'mock_data'
        }

        self.clone.pop_doc(path, doc)
        assert doc == {'mock': 'mock_data'}

    @raises(MissingContent)
    def test_pop_doc_wrong_prop(self):
        '''
        Test case for pop a wrong prop
        '''
        path = ['mock', 'fake.json']
        doc = {
            'mock': ['fake']
        }

        self.clone.pop_doc(path, doc)

    @raises(MissingContent)
    def test_pop_doc_empty_args(self):
        '''
        Test case for ``clone.pop_doc`` with empty args
        '''
        doc = {
            'mock': 'fake'
        }
        self.clone.pop_doc([], doc)

    def test_extract_property_empty_args(self):
        '''
        Test case for ``extract_property`` with empty args
        '''
        self.clone.doc = {
            'mock': 'no_effect'
        }

        assert self.clone.extract_property('') is None
        assert self.clone.doc == {'mock': 'no_effect'}

    @patch('couchapp.clone_app.clone.pop_doc', return_value='mock_content')
    def test_extract_property(self, pop_doc):
        '''
        Test case for extract prop successfully
        '''
        self.clone.doc = {}

        ret = self.clone.extract_property('mock')

        assert ret == ('mock', 'mock_content')
        assert pop_doc.called

    @patch('couchapp.clone_app.clone.pop_doc', side_effect=MissingContent)
    def test_extract_property_fail(self, pop_doc):
        '''
        Test case for extract prop failed
        '''
        self.clone.doc = {}
        assert self.clone.extract_property('mock') is None

    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.util.write')
    def test_dump_file_empty_args(self, util_write, setup_dir):
        '''
        Test case for dump_file with empty ``path``
        '''
        self.clone.objects = {}

        assert self.clone.dump_file('', 'mock') is None
        assert not util_write.called
        assert not setup_dir.called

    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.util.write')
    def test_dump_file_json_str(self, util_write, setup_dir):
        '''
        Test case for dump_file to json file with normal str
        '''
        self.clone.objects = {}

        ret = self.clone.dump_file('/mock/fake.json', 'foobar\n')

        assert setup_dir.called
        assert util_write.call_args_list[0][0] == ('/mock/fake.json',
                                                   '"foobar\\n"')

    def test_decode_content_str(self):
        '''
        Test case for decode_content with normal str
        '''
        self.clone.objects = {}

        assert self.clone.decode_content('foobar\n') == 'foobar\n'

    def test_decode_content_base64(self):
        '''
        Test case for decode_content with base64 str
        '''
        self.clone.objects = {}
        b64_content = 'base64-encoded;Zm9vYmFyCg=='  # foobar\n

        assert self.clone.decode_content(b64_content) == 'foobar\n'

    def test_decode_content_objects(self):
        '''
        Test case for decode_content with content refered to ``objects``
        '''
        self.clone.objects = {
            '17404a596cbd0d1e6c7d23fcd845ab82': 'mock_data'
        }

        assert self.clone.decode_content('mock') == 'mock_data'

    def test_decode_content_non_str(self):
        '''
        Test case for decode_content with non-str
        '''
        assert self.clone.decode_content(42) == 42
        assert self.clone.decode_content(1.1) == 1.1
        assert self.clone.decode_content(['foo']) == ['foo']
        assert self.clone.decode_content(None) is None
        assert self.clone.decode_content(True) is True

    @patch('couchapp.clone_app.clone.dump_file')
    def test_setup_manifest_empty(self, dump_file):
        '''
        Test case for setup_manifest with empty ``manifest``
        '''
        self.clone.manifest = []
        self.clone.setup_manifest()
        assert not dump_file.called

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.dump_file')
    @patch('couchapp.clone_app.clone.extract_property')
    @patch('couchapp.clone_app.clone.setup_dir')
    def test_setup_manifest_dirs(self, setup_dir, extract_property,
                                 dump_file, decode_content):
        '''
        Test case for setup_manifest with dirs
        '''
        self.clone.path = '/mock'
        self.clone.manifest = ['views/', 'views/mockview/',
                               'shows/', '_attachments/']

        self.clone.setup_manifest()
        assert setup_dir.call_count == 4
        assert not extract_property.called
        assert not decode_content.called
        assert not dump_file.called

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.extract_property')
    @patch('couchapp.clone_app.clone.dump_file')
    @patch('couchapp.clone_app.clone.setup_dir')
    def test_setup_manifest_couchapp_json(self, setup_dir, dump_file,
                                          extract_property, decode_content):
        '''
        Test case for setup_manifest with ``couchapp.json``
        '''
        self.clone.path = '/mock'
        self.clone.manifest = ['couchapp.json']

        self.clone.setup_manifest()
        assert not setup_dir.called
        assert not extract_property.called
        assert not decode_content.called
        assert not dump_file.called

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.extract_property')
    @patch('couchapp.clone_app.clone.dump_file')
    @patch('couchapp.clone_app.clone.setup_dir')
    def test_setup_manifest_create_files_fail(self, setup_dir, dump_file,
                                              extract_property, decode_content):
        '''
        Test case for setup_manifest create files failed
        '''
        self.clone.path = '/mock'
        self.clone.manifest = ['mock.json', 'fake.txt']
        extract_property.return_value = None

        self.clone.setup_manifest()
        assert not setup_dir.called
        assert extract_property.call_count == 2
        assert not decode_content.called
        assert not dump_file.called

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.extract_property')
    @patch('couchapp.clone_app.clone.dump_file')
    @patch('couchapp.clone_app.clone.setup_dir')
    def test_setup_manifest_create_files(self, setup_dir, dump_file,
                                         extract_property, decode_content):
        '''
        Test case for setup_manifest create files
        '''

        self.clone.path = '/mock'
        self.clone.manifest = ['mock.json', 'fake.txt']
        extract_property.return_value = ('mock', 'joke')

        self.clone.setup_manifest()
        assert not setup_dir.called
        assert extract_property.call_count == 2
        assert dump_file.called
        assert decode_content.called

    @patch('couchapp.clone_app.util.write_json')
    def test_setup_couchapp_json_miss(self, write_json):
        '''
        Test case for setup_couchapp_json with missing ``self.doc['couchapp']``
        '''
        self.clone.doc = {}
        self.clone.setup_couchapp_json()
        assert not write_json.called

    @patch('couchapp.clone_app.util.write_json')
    def test_setup_couchapp_json_empty(self, write_json):
        '''
        Test case for setup_couchapp_json with empty json writted finally
        '''
        self.clone.doc = {
            'couchapp': {
                'signatures': {},
                'objects': {},
                'manifest': [],
                'length': 42
            }
        }
        self.clone.path = '/mock'

        self.clone.setup_couchapp_json()

        assert '/mock/couchapp.json' in write_json.call_args_list[0][0]
        assert {} in write_json.call_args_list[0][0]

    @patch('couchapp.clone_app.util.write_json')
    def test_setup_couchapp_json(self, write_json):
        '''
        Test case for setup_couchapp_json
        '''
        self.clone.doc = {
            'couchapp': {
                'name': 'foo',
                'signatures': {},
                'objects': {},
                'manifest': [],
                'length': 42,
                'truth': 42,
            },
        }
        self.clone.path = '/mock'

        self.clone.setup_couchapp_json()

        assert '/mock/couchapp.json' in write_json.call_args_list[0][0]
        assert {'name': 'foo', 'truth': 42} in write_json.call_args_list[0][0]

    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.util.write')
    def test_setup_views_empty(self, util_write, setup_dir):
        '''
        Test case for ``setup_views`` with empty ``views`` prop
        '''
        self.clone.doc = {
            'views': {}
        }
        self.clone.path = '/mock'

        self.clone.setup_views()

        assert not util_write.called
        assert setup_dir.called

    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.util.write')
    def test_setup_views(self, util_write, setup_dir):
        '''
        Test case for ``setup_views`` with ``mockview`` written
        '''
        self.clone.doc = {
            'views': {
                'mockview': {
                    'map': 'function(){}',
                    'redurce': 'function(){}',
                }
            }
        }
        self.clone.path = '/mock'

        self.clone.setup_views()

        assert util_write.call_count == 2
        assert setup_dir.called

    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.util.write')
    def test_setup_func_empty(self, util_write, setup_dir):
        '''
        Test case for ``setup_func`` with empty func prop
        '''
        self.clone.doc = {
            'shows': {}
        }
        self.clone.path = '/mock'

        self.clone.setup_func('shows')

        assert setup_dir.called
        assert not util_write.called

    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.util.write')
    def test_setup_func_shows(self, util_write, setup_dir):
        '''
        Test case for ``setup_func`` have ``shows`` written
        '''
        self.clone.doc = {
            'shows': {
                'mock': 'function(){}',
                'fake': 'function(){}'
            }
        }
        self.clone.path = '/mock'

        self.clone.setup_func('shows')

        assert setup_dir.called
        assert util_write.call_count == 2

    def test_flatten_doc(self):
        '''
        Test case for ``flatten_doc``
        '''
        doc = {
            'views': {
                'mock': {
                    'map': 'map_func',
                    'reduce': 'reduce_func',
                }
            },
            'truth': 42
        }
        expect = {
            'views/mock/map': 'map_func',
            'views/mock/reduce': 'reduce_func',
            'truth': 42
        }
        assert self.clone.flatten_doc(doc) == expect

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.clone.dump_file')
    def test_setup_prop_nonexist(self, dump_file, setup_dir, decode_content):
        '''
        Test case for ``clone.setup_prop`` with nonexist prop
        '''
        self.clone.doc = {}
        self.clone.setup_prop('nonexist')
        assert not decode_content.called
        assert not setup_dir.called
        assert not dump_file.called

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.clone.dump_file')
    def test_setup_prop_dict(self, dump_file, setup_dir, decode_content):
        '''
        Test case for ``clone.setup_prop`` with dict
        '''
        self.clone.path = '/mockapp'
        self.clone.doc = {
            'mock': {
                'foo': {
                    'bar': 42,
                    'baz': None,
                }
            },
            'fake': {
                'fun': 'data',
            }
        }
        decode_content.side_effect = lambda x: x

        self.clone.setup_prop('mock')
        assert setup_dir.call_count == 1
        assert decode_content.called
        assert '/mockapp/mock/foo.json' in dump_file.call_args_list[0][0]
        assert {'bar': 42, 'baz': None} in dump_file.call_args_list[0][0]

        setup_dir.reset_mock()
        dump_file.reset_mock()

        self.clone.setup_prop('fake')
        assert setup_dir.called == 1
        assert decode_content.called
        assert '/mockapp/fake/fun' in dump_file.call_args_list[0][0]
        assert 'data' in dump_file.call_args_list[0][0]

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.clone.dump_file')
    def test_setup_prop_str(self, dump_file, setup_dir, decode_content):
        '''
        Test case for ``clone.setup_prop`` with str value
        '''
        self.clone.path = '/mockapp'
        self.clone.doc = {
            'foo': 'bar',
        }
        decode_content.side_effect = lambda x: x
        self.clone.setup_prop('foo')

        assert not setup_dir.called
        assert decode_content.called
        assert '/mockapp/foo' in dump_file.call_args_list[0][0]
        assert 'bar' in dump_file.call_args_list[0][0]

    @patch('couchapp.clone_app.clone.decode_content')
    @patch('couchapp.clone_app.clone.setup_dir')
    @patch('couchapp.clone_app.clone.dump_file')
    def test_setup_prop_non_str(self, dump_file, setup_dir, decode_content):
        '''
        Test case for ``clone.setup_prop`` with non-str value
        '''
        self.clone.path = '/mockapp'
        self.clone.doc = {
            'foo': 42,
            'bar': None,
            'baz': True,
            'qux': [1, 2, 3],
        }
        decode_content.side_effect = lambda x: x
        self.clone.setup_prop('foo')

        assert not setup_dir.called
        assert not decode_content.called
        assert '/mockapp/foo.json' in dump_file.call_args_list[0][0]
        assert 42 in dump_file.call_args_list[0][0]

        dump_file.reset_mock()
        self.clone.setup_prop('bar')
        assert '/mockapp/bar.json' in dump_file.call_args_list[0][0]
        assert None in dump_file.call_args_list[0][0]

        dump_file.reset_mock()
        self.clone.setup_prop('baz')
        assert '/mockapp/baz.json' in dump_file.call_args_list[0][0]
        assert True in dump_file.call_args_list[0][0]

        dump_file.reset_mock()
        self.clone.setup_prop('qux')
        assert '/mockapp/qux.json' in dump_file.call_args_list[0][0]
        assert [1, 2, 3] in dump_file.call_args_list[0][0]

    @patch('couchapp.clone_app.clone.setup_prop')
    @patch('couchapp.clone_app.clone.setup_func')
    @patch('couchapp.clone_app.clone.setup_views')
    def test_setup_missing_underlinekey(self, setup_views, setup_func, setup_prop):
        '''
        Test case for ``clone.setup_missing`` handle ``_key``
        '''
        self.clone.doc = {
            '_id': 'foo',
            '_rev': 'bar',
        }
        self.clone.setup_missing()

        assert not setup_views.called
        assert not setup_func.called
        assert not setup_prop.called

    @patch('couchapp.clone_app.clone.setup_prop')
    @patch('couchapp.clone_app.clone.setup_func')
    @patch('couchapp.clone_app.clone.setup_views')
    def test_setup_missing_couchapp_json(self, setup_views, setup_func, setup_prop):
        '''
        Test case for ``clone.setup_missing`` encounter key ``couchapp``
        '''
        self.clone.doc = {
            'couchapp': {}
        }
        self.clone.setup_missing()

        assert not setup_views.called
        assert not setup_func.called
        assert not setup_prop.called

    @patch('couchapp.clone_app.clone.setup_prop')
    @patch('couchapp.clone_app.clone.setup_func')
    @patch('couchapp.clone_app.clone.setup_views')
    def test_setup_missing_views(self, setup_views, setup_func, setup_prop):
        '''
        Test case for ``clone.setup_missing`` handle views
        '''
        self.clone.doc = {
            'views': {
                'mock': {
                    'map': 'func',
                    'reduce': 'func',
                }
            }
        }
        self.clone.setup_missing()

        assert setup_views.called
        assert not setup_func.called
        assert not setup_prop.called

    @patch('couchapp.clone_app.clone.setup_prop')
    @patch('couchapp.clone_app.clone.setup_func')
    @patch('couchapp.clone_app.clone.setup_views')
    def test_setup_missing_func(self, setup_views, setup_func, setup_prop):
        '''
        Test case for ``clone.setup_missing`` handle func like ``shows``
        '''
        self.clone.doc = {
            'shows': {},
            'updates': {},
            'filters': {},
            'lists': {},
        }
        self.clone.setup_missing()

        assert not setup_views.called
        assert setup_func.call_count == 4
        assert not setup_prop.called

    @patch('couchapp.clone_app.clone.setup_prop')
    @patch('couchapp.clone_app.clone.setup_func')
    @patch('couchapp.clone_app.clone.setup_views')
    def test_setup_missing_prop(self, setup_views, setup_func, setup_prop):
        '''
        Test case for ``clone.setup_missing`` handle prop
        '''
        self.clone.doc = {
            'mock': 'fake',
            'foo': 'bar',
            'baz': 'qux',
        }
        self.clone.setup_missing()

        assert not setup_views.called
        assert not setup_func.called
        assert setup_prop.call_count == 3

    @patch('couchapp.clone_app.util.write')
    def test_setup_id(self, write):
        '''
        Test case for ``clone.setup_id``
        '''
        self.clone.path = '/mock'
        self.clone.doc = {
            '_id': '_design/mock',
        }

        self.clone.setup_id()
        assert '/mock/_id' in write.call_args_list[0][0]
        assert '_design/mock' in write.call_args_list[0][0]
