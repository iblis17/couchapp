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
from couchapp.errors import AppError


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
        for key in self.doc.iterkeys():
            if key.startswith('_'):
                continue
            elif key in ('couchapp'):
                app_meta = copy.deepcopy(self.doc['couchapp'])
                if 'signatures' in app_meta:
                    del app_meta['signatures']
                if 'manifest' in app_meta:
                    del app_meta['manifest']
                if 'objects' in app_meta:
                    del app_meta['objects']
                if 'length' in app_meta:
                    del app_meta['length']
                if app_meta:
                    couchapp_file = os.path.join(self.path, 'couchapp.json')
                    util.write_json(couchapp_file, app_meta)
            elif key in ('views'):
                vs_dir = os.path.join(self.path, key)
                if not os.path.isdir(vs_dir):
                    os.makedirs(vs_dir)
                for vsname, vs_item in self.doc[key].iteritems():
                    vs_item_dir = os.path.join(vs_dir, vsname)
                    if not os.path.isdir(vs_item_dir):
                        os.makedirs(vs_item_dir)
                    for func_name, func in vs_item.iteritems():
                        filename = os.path.join(vs_item_dir, '%s.js' % func_name)
                        util.write(filename, func)
                        logger.warning("clone view not in manifest: %s" % filename)
            elif key in ('shows', 'lists', 'filter', 'updates'):
                showpath = os.path.join(self.path, key)
                if not os.path.isdir(showpath):
                    os.makedirs(showpath)
                for func_name, func in self.doc[key].iteritems():
                    filename = os.path.join(showpath, '%s.js' % func_name)
                    util.write(filename, func)
                    logger.warning(
                        "clone show or list not in manifest: %s" % filename)
            else:
                filedir = os.path.join(self.path, key)
                if os.path.exists(filedir):
                    continue
                else:
                    logger.warning("clone property not in manifest: %s" % key)
                    if isinstance(self.doc[key], (list, tuple,)):
                        util.write_json(filedir + ".json", self.doc[key])
                    elif isinstance(self.doc[key], dict):
                        if not os.path.isdir(filedir):
                            os.makedirs(filedir)
                        for field, value in self.doc[key].iteritems():
                            fieldpath = os.path.join(filedir, field)
                            if isinstance(value, basestring):
                                if value.startswith('base64-encoded;'):
                                    value = base64.b64decode(content[15:])
                                util.write(fieldpath, value)
                            else:
                                util.write_json(fieldpath + '.json', value)
                    else:
                        value = self.doc[key]
                        if not isinstance(value, basestring):
                            value = str(value)
                        util.write(filedir, value)

        # save id
        idfile = os.path.join(self.path, '_id')
        util.write(idfile, self.doc['_id'])

        util.write_json(os.path.join(self.path, '.couchapprc'), {})

        if '_attachments' in self.doc:  # process attachments
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
                    logger.debug("clone attachment: %s" % filename)

        logger.info("%s cloned in %s" % (self.source, self.dest))

    def __new__(cls, *args, **kwargs):
        obj = super(clone, cls).__new__(cls)

        logger.debug('clone obj created: {0}'.format(obj))
        obj.__init__(*args, **kwargs)

        return None

    def init_path(self):
        self.path = os.path.normpath(os.path.join(os.getcwd(), self.dest))

        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def init_metadata(self):
        '''
        Setup
            - self.manifest
            - self.signatures
            - self.objects: objects refs
        '''
        metadata = self.doc.get('couchapp', {})

        self.manifest = metadata.get('manifest', {})
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
        '''
        if not self.manifest:
            return

        for filename in self.manifest:
            logger.debug('clone property: "{0}"'.format(filename))

            filepath = os.path.join(self.path, filename)
            if filename.endswith('/'):  # create dir
                if not os.path.isdir(filepath):
                    os.makedirs(filepath)
                continue
            elif filename == 'couchapp.json':  # we will handle it later
                continue

            # create file
            parts = util.split_path(filename)
            fname = parts.pop()
            v = self.doc
            while 1:
                try:
                    for key in parts:
                        v = v[key]
                except KeyError:
                    break

                # remove extension
                last_key, ext = os.path.splitext(fname)

                # make sure key exist
                try:
                    content = v[last_key]
                except KeyError:
                    break

                if isinstance(content, basestring):
                    _ref = md5(util.to_bytestring(content)).hexdigest()
                    if self.objects and _ref in self.objects:
                        content = self.objects[_ref]

                    if content.startswith('base64-encoded;'):
                        content = base64.b64decode(content[15:])

                if fname.endswith('.json'):
                    content = util.json.dumps(content).encode('utf-8')

                del v[last_key]

                # make sure file dir have been created
                filedir = os.path.dirname(filepath)
                if not os.path.isdir(filedir):
                    os.makedirs(filedir)

                util.write(filepath, content)

                # remove the key from design doc
                temp = self.doc
                for key2 in parts:
                    if key2 == key:
                        if not temp[key2]:
                            del temp[key2]
                        break
                    temp = temp[key2]
