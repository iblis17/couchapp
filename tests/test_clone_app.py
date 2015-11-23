# -*- coding: utf-8 -*-

from couchapp.clone_app import clone
from couchapp.errors import AppError

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
