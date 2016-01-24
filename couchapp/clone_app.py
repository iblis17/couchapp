# -*- coding: utf-8 -*-
#
# This file is part of couchapp released under the Apache 2 license.
# See the NOTICE for more information.

import base64
import copy
import logging
import os

from hashlib import md5

from couchapp import client, util
from couchapp.errors import AppError, MissingContent


logger = logging.getLogger(__name__)


class clone(object):
    """
    Clone an application from a design_doc given.

    :param source: the http/https uri of design document
    """

    def __init__(self, source, dest=None, rev=None):
        self.source = source
        self.dest = dest
        self.rev = rev

        # init self.docid & self.dburl
        try:
            self.dburl, self.docid = self.source.split('_design/')
        except ValueError:
            raise AppError("{0} isn't a valid source".format(self.source))

        if not self.dest:
            self.dest = self.docid

        # init self.path
        self.init_path()

        # init self.db
        self.db = client.Database(self.dburl[:-1], create=False)
        if not self.rev:
            self.doc = self.db.open_doc('_design/{0}'.format(self.docid))
        else:
            self.doc = self.db.open_doc('_design/{0}'.format(self.docid), rev=self.rev)
        self.docid = self.doc['_id']

        # init metadata
        self.init_metadata()

        # create files from manifest
        self.setup_manifest()

        # second pass for missing key or in case
        # manifest isn't in app
        self.setup_missing()

        # create couchapp.json
        self.setup_couchapp_json()

        # save id
        self.setup_id()

        # setup empty .couchapprc
        util.write_json(os.path.join(self.path, '.couchapprc'), {})

        # process attachments
        self.setup_attachments()

        logger.info("{src} cloned in {dest}".format(src=self.source,
                                                    dest=self.dest))

    def __new__(cls, *args, **kwargs):
        obj = super(clone, cls).__new__(cls)

        logger.debug('clone obj created: {0}'.format(obj))
        obj.__init__(*args, **kwargs)

        return None

    def init_path(self):
        self.path = os.path.normpath(os.path.join(os.getcwd(),
                                                  self.dest or ''))
        self.setup_dir(self.path)

    def init_metadata(self):
        '''
        Setup
            - self.manifest
            - self.signatures
            - self.objects: objects refs
        '''
        metadata = self.doc.get('couchapp', {})

        self.manifest = metadata.get('manifest', [])
        self.signatures = metadata.get('signatures', {})
        self.objects = metadata.get('objects', {})

    def setup_manifest(self):
        '''
        create files/dirs from manifest

        manifest has following format in json:
        ```
            "manifest": [
                "some_dir/",
                "file_foo",
                "bar.json"
            ]
        ```

        Once we create a file successfully, we will remove the record from
        ``self.doc``.
        '''
        if not self.manifest:
            return

        for filename in self.manifest:
            logger.debug('clone property: "{0}"'.format(filename))

            filepath = os.path.join(self.path, filename)
            if filename.endswith('/'):  # create dir
                self.setup_dir(filepath)
                continue
            elif filename == 'couchapp.json':
                continue  # we will setup it later in ``self.__init__``

            # create file
            item_pair = self.extract_property(filename)
            if item_pair is None:
                continue
            _, content = item_pair

            self.dump_file(filepath, self.decode_content(content))

    def extract_property(self, path):
        '''
        Extract the content from ``self.doc``.
        Given a listed path in ``self.manifest``, we travel the ``self.doc``.

        Assume we have ``views/some_func/map.js`` in our ``self.manifest``
        Then, there should exist following struct in ``self.doc``
        {
            ...
            "views": {
                "some_func": {
                    "map": "..."
                }
            }
            ...
        }

        :side effect: Remove key from ``self.doc`` if extract sucessfully.

        :return: The ``(path, content)`` pair. Note that
                 if we get path ``a`` and ``{'a': null}``,
                 then the return will be ``('a', None)``.

                 If the extraction failed, return ``None``
        '''
        if not path:
            return None

        try:
            content = self.pop_doc(util.split_path(path), self.doc)
        except MissingContent:
            logger.warning(
                'file {0} listed in mastfest missed content'.format(path))
            return None
        return (path, content)

    def pop_doc(self, path, doc):
        '''
        do doc recursive traversal, and pop the value

        :param path: the list from ``util.split_path``
        :side effect: Remove key from ``self.doc`` if extract sucessfully.
        :return: the value. If we pop failed,
                 raise ``couchapp.errors.MissingContent``.
        '''
        try:
            head, tail = path[0], path[1:]
        except IndexError:  # path is empty
            raise MissingContent()

        if not tail:  # the leaf node of path
            prop, _ = os.path.splitext(head)
            if prop in doc:
                return doc.pop(prop)
            else:
                raise MissingContent()

        subdoc = doc.get(head, None)
        if not isinstance(subdoc, dict):
            raise MissingContent()

        ret = self.pop_doc(tail, subdoc)

        if not subdoc:  # after subdoc.pop(), if the subdoc is empty
            del doc[head]

        return ret

    def decode_content(self, content):
        '''
        Decode for base64 string, or get the content refered via objects
        '''
        if not isinstance(content, basestring):
            return content

        _ref = md5(util.to_bytestring(content)).hexdigest()
        if self.objects and _ref in self.objects:
            content = self.objects[_ref]

        if content.startswith('base64-encoded;'):
            content = base64.b64decode(content[15:])

        return content

    def dump_file(self, path, content):
        '''
        Dump the content of doc to file
        '''
        if not path:
            return

        if path.endswith('.json'):
            content = util.json.dumps(content).encode('utf-8')

        # make sure file dir have been created
        filedir = os.path.dirname(path)
        if not os.path.isdir(filedir):
            self.setup_dir(filedir)

        util.write(path, content)

    def setup_missing(self):
        '''
        second pass for missing key or in case manifest isn't in app.
        '''
        for key in self.doc:
            if key.startswith('_'):
                continue
            elif key in ('couchapp',):
                continue  # we will setup it later in ``self.__init__``
            elif key in ('views',):
                self.setup_views()
            elif key in ('shows', 'lists', 'filters', 'updates'):
                self.setup_func(key)
            else:
                self.setup_prop(key)

    def setup_prop(self, prop):
        '''
        Create file for arbitrary property.

        Policy:
        - If the property is a list/int/float/bool/null,
          we will save it as json file.

        - If the property is a dict, we will create a dir for it and
          handle its contents recursively.

        - If the property starts with ``base64-encoded;``,
          we decode it and save as binary file.

        - If the property is simple plane text, we just save it.
        '''
        if prop not in self.doc:
            return

        filepath = os.path.join(self.path, prop)

        if os.path.exists(filepath):
            return

        logger.warning('clone property not in manifest: "{0}"'.format(prop))

        value = self.doc[prop]
        if isinstance(value, (list, tuple, int, float, bool)) or value is None:
            self.dump_file('{0}.json'.format(filepath), value)
        elif isinstance(value, dict):
            if not os.path.isdir(filepath):
                self.setup_dir(filepath)

            for field, content in value.iteritems():
                fieldpath = os.path.join(filepath, field)
                content = self.decode_content(content)

                if not isinstance(content, basestring):
                    fieldpath = '{0}.json'.format(fieldpath)

                self.dump_file(fieldpath, content)
        else:  # in case of content is ``string``
            self.dump_file(filepath, self.decode_content(value))

    def setup_couchapp_json(self):
        '''
        Create ``couchapp.json`` from ``self.doc['couchapp']``.

        We will exclude the following properties:
            - ``signatures``
            - ``manifest``
            - ``objects``
            - ``length``
        '''
        if 'couchapp' not in self.doc:
            logger.warning('missing `couchapp` property in document')
            return

        app_meta = copy.deepcopy(self.doc['couchapp'])

        if 'signatures' in app_meta:
            del app_meta['signatures']
        if 'manifest' in app_meta:
            del app_meta['manifest']
        if 'objects' in app_meta:
            del app_meta['objects']
        if 'length' in app_meta:
            del app_meta['length']

        couchapp_file = os.path.join(self.path, 'couchapp.json')
        util.write_json(couchapp_file, app_meta)

    def setup_views(self):
        '''
        Create ``views/``

        ``views`` dir will have following structure::

            views/
                view_name/
                    map.js
                    reduce.js (optional)
                view_name2/
                    ...

        '''
        vs_dir = os.path.join(self.path, 'views')

        if not os.path.isdir(vs_dir):
            self.setup_dir(vs_dir)

        for vsname, vs_item in self.doc['views'].iteritems():
            vs_item_dir = os.path.join(vs_dir, vsname)
            if not os.path.isdir(vs_item_dir):
                self.setup_dir(vs_item_dir)

            for func_name, func in vs_item.iteritems():
                filename = os.path.join(vs_item_dir,
                                        '{0}.js'.format(func_name))
                util.write(filename, func)
                logger.warning(
                    'clone view not in manifest: "{0}"'.format(filename))

    def setup_func(self, func):
        '''
        Create dir for function:
            - ``shows``
            - ``lists
            - ``filters``
            - ``updates``
        '''
        func_dir = os.path.join(self.path, func)

        if not os.path.isdir(func_dir):
            self.setup_dir(func_dir)

        for func_name, func in self.doc[func].iteritems():
            filename = os.path.join(func_dir, '{0}.js'.format(func_name))
            util.write(filename, func)
            logger.warning(
                'clone function "{0}" not in manifest: {1}'.format(
                func, filename))

    def setup_id(self):
        '''
        Create ``_id`` file
        '''
        idfile = os.path.join(self.path, '_id')
        util.write(idfile, self.doc['_id'])

    def setup_attachments(self):
        '''
        Create ``_attachments`` dir
        '''
        if '_attachments' not in self.doc:
            return

        attachdir = os.path.join(self.path, '_attachments')

        if not os.path.isdir(attachdir):
            os.makedirs(attachdir)

        for filename in self.doc['_attachments'].iterkeys():
            if filename.startswith('vendor'):
                attach_parts = util.split_path(filename)
                vendor_attachdir = os.path.join(self.path, attach_parts.pop(0),
                                                attach_parts.pop(0),
                                                '_attachments')
                filepath = os.path.join(vendor_attachdir, *attach_parts)
            else:
                filepath = os.path.join(attachdir, filename)

            filepath = os.path.normpath(filepath)
            currentdir = os.path.dirname(filepath)
            if not os.path.isdir(currentdir):
                os.makedirs(currentdir)

            if self.signatures.get(filename) != util.sign(filepath):
                resp = self.db.fetch_attachment(self.docid, filename)
                with open(filepath, 'wb') as f:
                    for chunk in resp.body_stream():
                        f.write(chunk)
                logger.debug('clone attachment: {0}'.format(filename))

    def vendor_attach_dir(self, path):
        '''
        Map the vendor attachments to filesystem path

        Assume that we have ``vendor/couchapp/index.html``
        in ``_attachments`` section. It should be stored in
        ``/path/to/app/vendor/couchapp/_attachments/index.html``

        :return: the path string,
                 if the ``path`` not starts with ``vendor``,
                 return the original path.
        '''
        if not path.startswith('vendor'):
            return path

        path = util.split_path(path)
        path.insert(2, '_attachments')
        return os.path.join(self.path, *path)

    def dump_attachment(self, url, path):
        '''
        dump the attachment to filesystem.

        :param url: the relative url in document
        :param path: the filesystem path
        '''
        if not url or not path:
            return

        resp = self.db.fetch_attachment(self.docid, url)
        with open(path, 'wb') as f:
            for chunk in resp.body_stream():
                f.write(chunk)

    def setup_dir(self, path):
        '''
        Create dir recursively.

        :return: True, if create success.
                 Else, false.
        '''
        if not path:
            return False
        if os.path.exists(path):
            logger.warning('file exists: "{0}"'.format(path))
            return False

        try:
            os.makedirs(path)
        except OSError as e:
            logger.debug(e)
            return False
        return True

    def flatten_doc(self, doc):
        '''
        flatten a nested doc with filesystem map

        :param doc: {
            'foo': {
                'bar': 'fake'
            }
        }

        :return: {
            'foo/bar': 'fake'
        }
        '''
        ret = {}
        for key, val in doc.iteritems():
            if not isinstance(val, dict):
                ret[key] = val
                continue

            for subkey, subval in self.flatten_doc(val).iteritems():
                ret['{0}/{1}'.format(key, subkey)] = subval
        return ret
