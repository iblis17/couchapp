# -*- coding: utf-8 -*-
#
# This file is part of couchapp released under the Apache 2 license.
# See the NOTICE for more information.

import os

from .client import Database
from .errors import AppError
from . import util


class Config(object):
    """ main object to read configuration from ~/.couchapp.conf or
    .couchapprc/couchapp.json in the couchapp folder.
    """
    DEFAULT_SERVER_URI = "http://127.0.0.1:5984"

    DEFAULTS = dict(
        env={},
        extensions=[],
        hooks={}
    )

    def __init__(self):
        self.rc_path = util.rcpath()
        self.global_conf = self.load(self.rc_path, self.DEFAULTS)
        self.local_conf = {}
        self.app_dir = util.findcouchapp(os.getcwd())
        if self.app_dir:
            self.local_conf = self.load_local(self.app_dir)

        self.conf = self.global_conf.copy()
        self.conf.update(self.local_conf)

    def load(self, path, default=None):
        """
        load config

        :type path: str or iterable
        """
        conf = default if default is not None else {}
        paths = [path] if isinstance(path, basestring) else path

        for p in paths:
            if not os.path.isfile(p):
                continue
            try:
                new_conf = util.read_json(p, use_environment=True,
                                          raise_on_error=True)
            except ValueError:
                raise AppError("Error while reading '{0}'".format(p))
            conf.update(new_conf)

        return conf

    def load_local(self, app_path):
        """
        Load local config from app/couchapp.json and app/.couchapprc.
        If both of them contain same vars, the latter one will win.
        """
        if not app_path:
            raise AppError("You aren't in a couchapp.")

        fnames = ('couchapp.json', '.couchapprc')
        paths = (os.path.join(app_path, fname) for fname in fnames)
        return self.load(paths)

    def update(self, path):
        '''
        Given a couchapp path, and load the configs from it.
        '''
        self.conf = self.global_conf.copy()
        self.local_conf.update(self.load_local(path))
        self.conf.update(self.local_conf)

    def get(self, key, default=None):
        try:
            return getattr(self, key)
        except AttributeError:
            pass
        return self.conf[key]

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            pass
        return self.conf[key]

    def __getattr__(self, key):
        try:
            getattr(super(Config, self), key)
        except AttributeError:
            if key in self.conf:
                return self.conf[key]
            raise

    def __contains__(self, key):
        return (key in self.conf)

    def __iter__(self):
        for k in list(self.conf.keys()):
            yield self[k]

    @property
    def extensions(self):
        '''
        load extensions from conf

        :return: list of extension modules
        '''
        return [util.load_py(uri, self)
                for uri in self.conf.get('extensions', tuple())]

    @property
    def hooks(self):
        return {
            hooktype: [util.hook_uri(uri, self) for uri in uris]
                      for hooktype, uris in self.conf.get('hooks', {}).items()
        }

    # TODO: add oauth management
    def get_dbs(self, db_string=None):
        db_string = db_string or ''
        if db_string.startswith("http://") or \
                db_string.startswith("https://") or \
                db_string.startswith("desktopcouch://"):
            dburls = db_string
        else:
            env = self.conf.get('env', {})
            if not db_string:
                # get default db if it exists
                if 'default' in env:
                    dburls = env['default']['db']
                else:
                    raise AppError("database isn't specified")
            else:
                dburls = "%s/%s" % (self.DEFAULT_SERVER_URI, db_string)
                if db_string in env:
                    dburls = env[db_string].get('db', dburls)

        if isinstance(dburls, basestring):
            dburls = [dburls]

        use_proxy = os.environ.get("http_proxy", "") != "" or \
            os.environ.get("https_proxy", "") != ""

        return [Database(dburl, use_proxy=use_proxy) for dburl in dburls]

    def get_app_name(self, dbstring=None, default=None):
        env = self.conf.get('env', {})
        if not dbstring.startswith("http://"):
            if dbstring in env:
                return env[dbstring].get('name', default)
            elif 'default' in env:
                return env['default'].get('name', default)
        elif not dbstring and 'default' in env:
                return env['default'].get('name', default)
        return default
