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
