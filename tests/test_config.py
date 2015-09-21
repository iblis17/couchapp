# -*- coding: utf-8 -*-

from couchapp.config import Config
from couchapp.errors import AppError

from mock import Mock, patch
from nose.tools import raises, with_setup


@patch('couchapp.config.util.findcouchapp', return_value=None)
@patch('couchapp.config.util.rcpath', return_value=['/mock/couchapp.conf'])
def test_config_init(rcpath, getcwd):
    '''
    Test case for Config.__init__()

    Check following vars:
    - self.rc_path
    - self.global_conf
    - self.local_conf
    - self.app_dir
    - self.conf
    '''
    config = Config()

    assert config.rc_path == ['/mock/couchapp.conf'], config.rc_path
    assert config.global_conf == Config.DEFAULTS, config.global_conf
    assert config.local_conf == {}, config.local_conf
    assert config.app_dir is None, config.app_dir
    assert config.conf == Config.DEFAULTS


@patch('couchapp.config.Config.load_local', return_value={'mock': True})
@patch('couchapp.config.util.findcouchapp', return_value='/mockapp')
@patch('couchapp.config.util.rcpath', return_value=['/mock/couchapp.conf'])
def test_config_init_local(rcpath, getcwd, local_conf):
    '''
    Test case for Config.__init__() in a CouchApp
    '''
    config = Config()

    local_conf.assert_called_with('/mockapp')
    assert config.local_conf == {'mock': True}, config.local_conf


class TestConfig():
    @patch('couchapp.config.util.findcouchapp', return_value=None)
    @patch('couchapp.config.util.rcpath', return_value=['/mock/couchapp.conf'])
    def setup(self, rcpath, getcwd):
        self.config = Config()

    def teardown(self):
        del self.config

    @raises(AttributeError)
    def test_getattr(self):
        '''
        Test case for Config.__getattr__()
        '''
        assert self.config.conf == Config.DEFAULTS
        assert self.config.env == {}
        self.config.mock  # raise AttributeError

    @raises(KeyError)
    def test_getitem(self):
        '''
        Test case for Config.__getitem__()
        '''
        assert self.config['conf'] == Config.DEFAULTS
        assert self.config['env'] == {}
        assert self.config['mock']  # raise KeyError

    def test_contains(self):
        '''
        Test case for Config.__contains__()
        '''
        assert 'env' in self.config
        assert 'hooks' in self.config
        assert 'extensions' in self.config

    @patch('couchapp.config.util.read_json', return_value={'mock': True})
    @patch('couchapp.config.os.path.isfile', return_value=True)
    def test_load_from_list(self, isfile, read_json):
        '''
        Test case for Config.load(list, default)
        '''
        default = {'foo': 'bar'}

        conf = self.config.load(['/mock/couchapp.conf'], default)

        assert conf == {'foo': 'bar', 'mock': True}
        isfile.assert_called_with('/mock/couchapp.conf')
        read_json.assert_called_with('/mock/couchapp.conf',
                                     use_environment=True,
                                     raise_on_error=True)

    @patch('couchapp.config.util.read_json', return_value={'mock': True})
    @patch('couchapp.config.os.path.isfile', return_value=True)
    def test_load_from_str(self, isfile, read_json):
        '''
        Test case for Config.load(str)
        '''
        conf = self.config.load('/mock/couchapp.conf')

        assert conf == {'mock': True}
        isfile.assert_called_with('/mock/couchapp.conf')
        read_json.assert_called_with('/mock/couchapp.conf',
                                     use_environment=True,
                                     raise_on_error=True)

    @patch('couchapp.config.util.read_json', return_value={'mock': True})
    @patch('couchapp.config.os.path.isfile', return_value=False)
    def test_load_notfile(self, isfile, read_json):
        '''
        Test case for Config.load(['/not_a_file'], default)
        '''
        default = {'foo': 'bar'}

        conf = self.config.load(['/not_a_file'], default)

        assert conf == {'foo': 'bar'}
        isfile.assert_called_with('/not_a_file')
        assert not read_json.called

    @raises(AppError)
    @patch('couchapp.config.util.read_json', side_effect=ValueError)
    @patch('couchapp.config.os.path.isfile', return_value=True)
    def test_load_apperror(self, isfile, read_json):
        '''
        Test case for Config.load() reading a invalid file
        '''
        self.config.load('/mock/couchapp.conf')
        isfile.assert_called_with('/mock/couchapp.conf')

    @patch('couchapp.config.Config.load', return_value='mock')
    def test_load_local(self, load):
        '''
        Test case for Config.load_local()
        '''
        assert self.config.load_local('/mock') == 'mock'

        paths = tuple(load.call_args[0][0])
        assert paths == ('/mock/couchapp.json', '/mock/.couchapprc'), paths

    @raises(AppError)
    @patch('couchapp.config.Config.load')
    def test_load_local_apperror(self, load):
        '''
        Test case for Config.load_local() with empty `app_dir`
        '''
        self.config.load_local(None)
        assert not load.called

    @patch('couchapp.config.Config.load_local', return_value={'mock': True})
    def test_update(self, load_local):
        '''
        Test case for Config.update()
        '''
        self.config.update('/mock')

        assert self.config.conf.get('mock') == True
        load_local.assert_called_with('/mock')

    @patch('couchapp.config.util.load_py')
    def test_extensions_empty(self, load_py):
        '''
        Test case for empty Config.extensions
        '''
        assert self.config.extensions == []
        assert not load_py.called

    @patch('couchapp.config.util.load_py', return_value='mock')
    def test_extensions_mock(self, load_py):
        '''
        Test case for Config.extensions
        '''
        self.config.conf['extensions'] = ['mock_path']
        extensions = self.config.extensions

        assert extensions == ['mock'], extensions
        load_py.assert_called_with('mock_path', self.config)

    @patch('couchapp.config.util.hook_uri')
    def test_hook_empty(self, hook_uri):
        '''
        Test case for empty Config.hooks
        '''
        assert self.config.hooks == {}
        assert not hook_uri.called

    @patch('couchapp.config.util.hook_uri', return_value='mock_module')
    def test_hook_mock(self, hook_uri):
        '''
        Test case for Config.hooks
        '''
        self.config.conf['hooks'] = {'pre-push': ['mock_path']}
        hooks = self.config.hooks

        assert hooks == {'pre-push': ['mock_module']}, hooks
        hook_uri.assert_called_with('mock_path', self.config)

    @patch('couchapp.config.Database', return_value='mockdb')
    def test_get_dbs_full_uri(self, Database):
        '''
        Test case for Config.get_dbs() with full uri
        '''
        db_string = 'https://foo.bar'

        assert self.config.get_dbs(db_string) == ['mockdb']
        Database.assert_called_with(db_string, use_proxy=False)

    @patch('couchapp.config.Database', return_value='mockdb')
    def test_get_dbs_short_uri(self, Database):
        '''
        Test case for Config.get_dbs() with short uri
        '''
        full_uri = 'http://127.0.0.1:5984/foo'

        assert self.config.get_dbs('foo') == ['mockdb']
        Database.assert_called_with(full_uri, use_proxy=False)

    @patch('couchapp.config.Database', return_value='mockdb')
    def test_get_dbs_env(self, Database):
        '''
        Test case for Config.get_dbs() with env set
        '''
        db_string = 'http://foo.bar'
        self.config.conf['env'] = {'default': {'db': db_string}}

        assert self.config.get_dbs() == ['mockdb']
        Database.assert_called_with(db_string, use_proxy=False)

    @raises(AppError)
    @patch('couchapp.config.Database')
    def test_get_dbs_empty_env(self, Database):
        '''
        Test case for Config.get_dbs() without env set
        '''
        self.config.get_dbs()
        assert not Database.called

    @patch('couchapp.config.Database', return_value='mockdb')
    def test_get_dbs_short_env(self, Database):
        '''
        Test case for Config.get_dbs() with a short name in env
        '''
        self.config.conf['env'] = {'foo': {'db': 'http://foo.bar'}}

        assert self.config.get_dbs('foo') == ['mockdb']
        Database.assert_called_with('http://foo.bar', use_proxy=False)

    @patch('couchapp.config.Database', return_value='mockdb')
    def test_get_dbs_env_fake(self, Database):
        '''
        Test case for Config.get_dbs() with an useless env

        Assume .couchapprc is (no `db` field in `foo`)
        ```
        {
            'foo':{
                'notdb': 'mock'
            }
        }
        ```

        Expect behavior: fall back to DEFAULT_SERVER_URI/foo
        '''
        self.config.conf['env'] = {'foo': {'notdb': 'mock'}}
        default_uri = 'http://127.0.0.1:5984/foo'

        assert self.config.get_dbs('foo') == ['mockdb']
        Database.assert_called_with(default_uri, use_proxy=False)


    @patch('couchapp.config.Database', return_value='mockdb')
    def test_get_dbs_proxy(self, Database):
        '''
        Test case for Config.get_dbs() with https_proxy env
        '''
        with patch.dict('couchapp.config.os.environ', {'https_proxy': 'foo'}):
            assert self.config.get_dbs('https://bar') == ['mockdb']

        Database.assert_called_with('https://bar', use_proxy=True)

    def test_get_app_name_default(self):
        '''
        Test case for Config.get_app_name() without args and env
        '''
        assert self.config.get_app_name() == None

    def test_get_app_name_default_env(self):
        '''
        Test case for Config.get_app_name() without args but env

        env: {
            'default': {
                'name': 'MockApp'
            }
        }
        and
        env: {
            'mockname': {
                'name': 'MockApp2'
            }
        }
        '''
        self.config.conf['env'] = {'default': {'name': 'MockApp'}}
        assert self.config.get_app_name() == 'MockApp'

        self.config.conf['env'] = {'mockname': {'name': 'MockApp2'}}
        assert self.config.get_app_name('mockname') == 'MockApp2'

    def test_get_app_name_http_uri(self):
        '''
        Test case for Config.get_app_name('http://foo.bar', default)

        if the dbstring is full uri, return ``default``
        '''
        ret = self.config.get_app_name('http://foo.bar', 'mockapp')
        assert ret == 'mockapp'
