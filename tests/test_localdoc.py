from mock import patch

from couchapp.localdoc import LocalDoc


class TestLocalDoc(object):

    def setup(self):
        self.localdoc = LocalDoc('/mock')

    def teardown(self):
        del self.localdoc

    @patch('couchapp.localdoc.util.read', return_value='fake')
    @patch('couchapp.localdoc.os.path.exists', return_value=True)
    def test_get_id_idfile(self, exists, util):
        assert self.localdoc.get_id() == 'fake'

    @patch('couchapp.localdoc.os.path.exists', return_value=False)
    def test_get_id_no_idfile(self, exists):
        self.localdoc.is_ddoc = True
        assert self.localdoc.get_id() == '_design/mock'

        self.localdoc.is_ddoc = False
        assert self.localdoc.get_id() == 'mock'
