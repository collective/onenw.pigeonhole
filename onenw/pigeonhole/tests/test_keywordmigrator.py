import unittest
from zope.component import getUtility
from zope.interface import providedBy

from onenw.pigeonhole.tests.base import FunctionalTestCase
from onenw.pigeonhole.browser.keywordmigrator import KeywordMigrator
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter

from onenw.pigeonhole.config import PH_DEFAULT_TYPES

class TestKeywordMigrator(FunctionalTestCase):

    def createContent(self, type_name, prefix):
        for x in range(1,4):
            id = '%s%s' % (prefix, x)
            self.portal.invokeFactory(type_name, id)
            
        for x in range(1,4):
            id = '%s%s' % (prefix, x)
            obj = getattr(self.portal, id)
            obj.Schema().get('ph_field_1').getMutator(obj)(('Fishermen',))
            obj.reindexObject()

        for x in range(1,3):
            id = '%s%s' % (prefix, x)
            obj = getattr(self.portal, id)
            obj.Schema().get('ph_field_2').getMutator(obj)(('Fish',))
            obj.reindexObject()
    
    def afterSetUp(self):
        self.setRoles(('Manager',))
        # configure PH
        ctl_panel = PigeonholeCPAdapter(self.portal)
        ctl_panel.set_ph_field_values_1(['Fishermen', 'Fisherwomen',])
        ctl_panel.set_ph_field_values_2(['Fish',])
        self.createContent('Document', 'd')
    
    def test_getKeywords(self):
        expected = [{'field_id': 'ph_field_1',
                     'field_name': 'Audience',
                     'options': ('Fishermen', 'Fisherwomen')},
                    {'field_id': 'ph_field_2',
                     'field_name': 'Program Area',
                     'options': ('Fish',)},]
        view = self.portal.restrictedTraverse('keywordmigrator')
        kws = view.getKeywords()
        self.failUnless(expected==kws,
                        "Got: %s; expected: %s" % (kws, expected))

    def test_migrateKeywords(self):
        mapping = ({'field_id': 'ph_field_1', 'old_option': 'Fishermen', 'new_option': 'Fisherpeople',},
                   {'field_id': 'ph_field_2', 'old_option': 'Fish', 'new_option': 'Fishes',},)
        catalog = self.portal.portal_catalog
        # check things before we migrate 
        self.failUnless(len(catalog(ph_field_1='Fishermen'))==3)
        self.failUnless(len(catalog(ph_field_2='Fish'))==2)

        view = self.portal.restrictedTraverse('keywordmigrator')
        view.migrateKeywords(mapping=mapping)
        
        # prove that our content objects have changed
        self.failUnless(len(catalog(ph_field_1='Fishermen'))==0, "Wanted 0, got %s" % len(catalog(ph_field_1='Fishermen')))
        self.failUnless(len(catalog(ph_field_2='Fish'))==0)
        self.failUnless(len(catalog(ph_field_1='Fisherpeople'))==3)
        self.failUnless(len(catalog(ph_field_2='Fishes'))==2)
        
        # prove that our options have changed in the PH settings.  Order should be preserved.
        ctl_panel = PigeonholeCPAdapter(self.portal)
        options1 = ctl_panel.get_ph_field_values_1()
        options2 = ctl_panel.get_ph_field_values_2()
        self.failUnless(options1==('Fisherpeople', 'Fisherwomen'))
        self.failUnless(options2==('Fishes',))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestKeywordMigrator))
    return suite
