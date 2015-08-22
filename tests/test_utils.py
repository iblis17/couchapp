# -*- coding: utf-8 -*-

from couchapp.util import discover_apps, iscouchapp

from mock import patch


@patch('couchapp.util.os.path.isfile', return_value=True)
def test_iscouchapp(isfile):
    assert iscouchapp('/mock_dir') == True
    isfile.assert_called_with('/mock_dir/.couchapprc')


@patch('couchapp.util.os.listdir', return_value=['foo'])
@patch('couchapp.util.os.path.isdir', return_value=True)
@patch('couchapp.util.iscouchapp', return_value=True)
def test_discover_apps(iscouchapp_, isdir, listdir):
    assert discover_apps('/mock_dir') == ['/mock_dir/foo']
    isdir.assert_called_with('/mock_dir/foo')
    listdir.assert_called_with('/mock_dir')


@patch('couchapp.util.os.listdir', return_value=['foo'])
@patch('couchapp.util.os.path.isdir', return_value=True)
@patch('couchapp.util.iscouchapp', return_value=True)
def test_discover_apps_relative_path(iscouchapp_, isdir, listdir):
    assert discover_apps('mock_dir') == ['mock_dir/foo']
    isdir.assert_called_with('mock_dir/foo')
    listdir.assert_called_with('mock_dir')


@patch('couchapp.util.os.listdir', return_value=['.git', 'foo'])
@patch('couchapp.util.os.path.isdir', return_value=True)
@patch('couchapp.util.iscouchapp', return_value=True)
def test_discover_apps_hidden_file(iscouchapp_, isdir, listdir):
    '''
    Test case for a dir including hidden file
    '''
    assert discover_apps('mock_dir') == ['mock_dir/foo']
    isdir.assert_called_with('mock_dir/foo')
    listdir.assert_called_with('mock_dir')
