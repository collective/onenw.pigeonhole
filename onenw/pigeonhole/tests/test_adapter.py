import unittest
from onenw.pigeonhole.tests.base import FunctionalTestCase


class TestAdapter(FunctionalTestCase):

    def test_schemas_changed(self):
        # our content may be marker with the marker interface
        # but does its schema have new fields?
        home = getattr(self.portal, 'front-page')
        schema = home.Schema()
        for x in range(1,5):
            self.failUnless('ph_field_%s' % x in schema,
                            'Schema just contains: %s' % schema)
        self.failUnless('relatable' in schema,
                        'Schema missing "relatable": %s' % schema)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAdapter))
    return suite
