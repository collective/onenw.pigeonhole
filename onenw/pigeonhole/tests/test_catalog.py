import unittest

from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.tests.base import FunctionalTestCase
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter
from onenw.pigeonhole.catalog import ph_field_1, ph_field_2,\
                                     ph_field_3, ph_field_4
from onenw.pigeonhole.catalog import is_ph_configured

class TestCatalog(FunctionalTestCase):
    
    def testIndicesInCatalog(self):
        """We add 6 indices to the catalog"""
        catalog = getToolByName(self.portal, 'portal_catalog')
        indices = catalog.indexes()
        # 4 indices for the keyword fields
        for x in range(1,5):
            i = "ph_field_%s" % x
            self.failUnless(i in indices, "Index '%s' not in portal_catalog (%s)" % (i, indices))
        # 2 boolean fields
        for index in ('is_relatable', 'is_ph_configured'):
            self.failUnless(index in indices,
                            "Index '%s' not in portal_catalog (%s)" % (index, indices))

class TestIndices(FunctionalTestCase):
    
    def afterSetUp(self):
        # configure our site
        self.catalog = getToolByName(self.portal, 'portal_catalog')
        self.homey   = getattr(self.portal, 'front-page')
        # map one of [a-d] to each PH field (field 1:'a', etc) 
        schema = self.homey.Schema()
        for f,v in ((1,'a'),(2,'b',),(3,'c'),(4,'d'),):
            field_name = 'ph_field_%s' % f
            field = schema.get(field_name).getMutator(self.homey)
            field(v)
        self.homey.reindexObject()


    def testIndexMethods(self):
        self.failUnless(ph_field_1(self.homey, self.portal) == ('a',))
        self.failUnless(ph_field_2(self.homey, self.portal) == ('b',))
        # these fields aren't enabled (by default) so they should return None
        self.failUnless(ph_field_3(self.homey, self.portal) == ())
        self.failUnless(ph_field_4(self.homey, self.portal) == ())

    def testEnabledIndices(self):
        for f,v in ((1,'a'),(2,'b',),):
            field_name = 'ph_field_%s' % f
            self.failUnless('front-page' in [brain.id for brain in self.catalog({field_name: v})],
                            "Search failed for value '%s' in index '%s'" % (v,field_name))

    def testDisabledIndices(self):
        # home page shouldn't be in the search results yet since these fields aren't enabled yet
        for f,v in ((3,'c'),(4,'d'),):
            field_name = 'ph_field_%s' % f
            self.failUnless('front-page' not in [brain.id for brain in self.catalog({field_name: v})])

        # now enable these fields
        ctl_panel = PigeonholeCPAdapter(self.portal)
        ctl_panel.set_ph_field_visible_3(True)
        ctl_panel.set_ph_field_visible_4(True)
        # don't forget to reindex the object!
        self.homey.reindexObject()

        # now they should be available
        for f,v in ((3,'c'),(4,'d'),):
            field_name = 'ph_field_%s' % f
            self.failUnless('front-page' in [brain.id for brain in self.catalog({field_name: v})],
                            "Search failed for value '%s' in index '%s'" % (v,field_name))

    def testIsPHConfigured(self):
        """This is more just a test for the indexing method is_ph_configured()"""
        # should return False for brand-new content
        self.folder.invokeFactory('Document', 'newby')
        newby = self.folder.newby
        self.failUnless(not is_ph_configured(newby, self.portal))

        # homey has kws set, so it should return True
        self.failUnless(is_ph_configured(self.homey, self.portal))

        # if we uncheck relatable for newby, we should get True as well
        # (no kws have been added)
        newby.Schema().get('relatable').getMutator(newby)(False)
        self.failUnless(is_ph_configured(newby, self.portal))
        
        # should return True for Folders (which are not PH Aware)
        self.failUnless(is_ph_configured(self.folder, self.portal))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCatalog))
    suite.addTest(unittest.makeSuite(TestIndices))
    return suite
