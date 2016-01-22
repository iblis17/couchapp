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
