import unittest
from zope.component import getUtility

from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.tests.base import FunctionalTestCase
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter
from onenw.pigeonhole.config import PH_DEFAULT_TYPES
from onenw.pigeonhole.interfaces import IPigeonholizer

class TestConfiguration(FunctionalTestCase):
    """Test the adapter that's used to configure PH settings"""

    def testTypesSetting(self):
        ctl = PigeonholeCPAdapter(self.portal)
        # adding new types
        new_ph_types = PH_DEFAULT_TYPES + ['Folder',]
        ctl.set_ph_aware_types(new_ph_types)
        util = getUtility(IPigeonholizer)
        self.failUnless(set(new_ph_types)==set(util.ph_aware_types))
        # removing types
        ctl.set_ph_aware_types(PH_DEFAULT_TYPES)
        self.failUnless(set(PH_DEFAULT_TYPES)==set(util.ph_aware_types))

    def testBlobTypes(self):
        # Plone 4 uses ATBlob subtypes for Files and Images; make sure they
        # still work. When using blobs in Plone 3, this is trickier.
        portal_setup = getToolByName(self.portal, "portal_setup")
        try:
            portal_setup.runAllImportStepsFromProfile('profile-plone.app.blob:default', purge_old=False)
            portal_setup.runAllImportStepsFromProfile('profile-plone.app.blob:image-replacement', purge_old=False)
        except:
            print "plone.app.blob not installed; test might be incomplete"
        ctl = PigeonholeCPAdapter(self.portal)
        for typ in ('File', 'Image'):
            ctl.set_ph_aware_types([typ])
            util = getUtility(IPigeonholizer)
            self.failUnless(typ in util.ph_aware_types)
            id = "t-%s" % (typ)
            self.folder.invokeFactory(typ, id)
            item = getattr(self.folder, id)
            schema = item.Schema()
            for x in range(1,5):
                self.failUnless('ph_field_%s' % x in schema,
                                'Schema just contains: %s' % schema.fields())
            # remove PH-awareness now, to not contaminate the next test
            ctl.set_ph_aware_types([])

    def testVocabularies(self):
        """Test that changing the options for each field changes the Vocabulary for an object"""
        # we'll look at the homepage, since Document is enabled by default
        homey = getattr(self.portal, 'front-page')
        schema = homey.Schema()
        # enable all 4 fields and set their vocabs to all be ('a', 'b')
        ctl = PigeonholeCPAdapter(self.portal)
        VOCAB = ('a', 'b')
        for x in range(1,5):
            enabler = getattr(ctl, "set_ph_field_visible_%s" % x)
            enabler(True)
            field_values = getattr(ctl, 'set_ph_field_values_%s' % x)
            field_values(VOCAB)
            vocab = schema.getField('ph_field_%s' % x).Vocabulary(homey).values()
            
            # test adapter's getter methods (as manifested in a property)
            prop = getattr(ctl, 'ph_field_values_%s' % x)
            self.failUnless(prop==VOCAB)
            # test that the changes propagated all the way down to the Archetypes level
            self.failUnless(tuple(vocab)==tuple(VOCAB),
                            "Vocabulary for ph_field_%s was %s instead of %s" % (x, vocab, VOCAB))

    def testNameAndVisibilityChanges(self):
        """Test that we can change the friendly names and visibiliy
           for the fields, and that that changes the Collections indices"""
        atct_tool = getToolByName(self.portal, 'portal_atct')
        names = ("", "john", "paul", "george", "ringo")
        # enable all 4 fields and name them after the beatles
        ctl = PigeonholeCPAdapter(self.portal)
        for x in range(1,5):
            enabler = getattr(ctl, "set_ph_field_visible_%s" % x)
            enabler(True)
            field_name = getattr(ctl, 'set_ph_field_name_%s' % x)
            field_name(names[x])
            # test adapter's getter methods (as manifested in a property)
            prop = getattr(ctl, 'ph_field_name_%s' % x)
            self.failUnless(prop==names[x])
            # test that the ATCT settings are right for this index
            index = atct_tool.getIndex('ph_field_%s' % x)
            self.failUnless(index.friendlyName==names[x],
                            "Index in portal_atct was named %s instead of %s" % (index.friendlyName, names[x]))
            self.failUnless(index.enabled is True,
                            "Index %s in portal_atct wasn't enabled" % (index.index))
            # make sure disabling works too
            enabler(False)
            index = atct_tool.getIndex('ph_field_%s' % x)
            self.failUnless(index.enabled is not True,
                            "Index %s in portal_atct was enabled (and it shouldn't have been)" % (index.index))

    def testConfigurationWarning(self):
        """Test that turning off warnings hides the warning stylesheet"""
        css = getToolByName(self.portal, 'portal_css')
        ctl = PigeonholeCPAdapter(self.portal)
        id = "++resource++unconfigured-ph-content.css"
        # by default the css is enabled
        self.failUnless(css.getResource(id).getEnabled())
        
        # but no longer
        ctl.set_show_warning(False)
        self.failUnless(not css.getResource(id).getEnabled())

    def testDeletingKWsUpdatesContent(self):
        ctl = PigeonholeCPAdapter(self.portal)
        # enable the last two fields, since we'll test each one
        ctl.set_ph_field_visible_3(True)
        ctl.set_ph_field_visible_4(True)

        self.folder.invokeFactory('Document', 'p1')
        page = self.folder.p1
        schema = page.Schema()
        # loop through and create some options
        for x in range(1,5):
            vocab_setter = getattr(ctl, "set_ph_field_values_%s" % x)
            vocab_setter(('foo%s' % x, 'bar%s' % x))
            schema.get('ph_field_%s' % x).getMutator(page)(('foo%s' % x, 'bar%s' % x))
            page.reindexObject()
            data = schema.get('ph_field_%s' % x).getAccessor(page)()
            self.failUnless(set(data)==set(('foo%s' % x, 'bar%s' % x)))
        
            # now change the options
            vocab_setter(('foo%s' % x,))
            # page should only be assigned foo now
            data = schema.get('ph_field_%s' % x).getAccessor(page)()
            self.failUnless(set(data)==set(('foo%s' % x,)),
                            "Values should be ('foo%s',), but instead they're: " % x+ str(data))

        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestConfiguration))
    return suite
