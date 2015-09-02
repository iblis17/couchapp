# -*- coding: utf-8 -*-

from couchapp.config import Config

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
