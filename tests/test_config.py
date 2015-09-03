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
