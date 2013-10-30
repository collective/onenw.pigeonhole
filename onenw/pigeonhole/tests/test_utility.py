import unittest
from zope.component import getUtility

from onenw.pigeonhole.tests.base import FunctionalTestCase
from onenw.pigeonhole.interfaces import IPigeonholizer
from onenw.pigeonhole.interfaces import IPigeonholeAware

from onenw.pigeonhole.config import PH_DEFAULT_TYPES

class TestUtility(FunctionalTestCase):
    
    def afterSetUp(self):
        # state seems to be preserved in btw tests -- let's reset
        # it so that only def types are pigeonholized
        util = getUtility(IPigeonholizer)
        for portal_type in util.ph_aware_types:
            util.unpigeonholize(portal_type)
        for portal_type in PH_DEFAULT_TYPES:
            util.pigeonholize(portal_type)
        
    def test_utility_retrofits_existing_types(self):
        """Once we designate a type as PH Aware, it should touch
        all pre-existing instances of that type."""

        # create a folder
        self.folder.invokeFactory("Folder", "test_folder")
        foldy = self.folder.test_folder
        
        self.failUnless(not IPigeonholeAware.providedBy(foldy))
        
        # now make Folders PH Aware
        util = getUtility(IPigeonholizer)
        util.pigeonholize("Folder")
        
        self.failUnless(IPigeonholeAware.providedBy(foldy))

    def test_folders_can_be_aware(self):
        util = getUtility(IPigeonholizer)
        util.pigeonholize("Folder")
        self.folder.invokeFactory("Folder", "test_folder2")
        foldy = self.folder.test_folder2
        schema = foldy.Schema()
        for x in range(1,5):
            self.failUnless('ph_field_%s' % x in schema,
                            'Schema just contains: %s' % schema)
        self.failUnless('relatable' in schema,
                        'Schema missing "relatable": %s' % schema)
        

    def test_default_types_aware(self):
        # show that the utility is storing the default types
        util = getUtility(IPigeonholizer)
        ph_aware_types = util.ph_aware_types
        for ctype in PH_DEFAULT_TYPES:
            self.failUnless(ctype in ph_aware_types,
                            "%s not in %s" % (ctype, ph_aware_types))

        # now show that a new type is in there too
        ctype = "Folder"
        util.pigeonholize(ctype)
        ph_aware_types = util.ph_aware_types
        self.failUnless(ctype in ph_aware_types,
                        "%s not in %s" % (ctype, ph_aware_types))

    def test_unpigeonholize(self):
        self.folder.invokeFactory("Folder", "test_folder")
        foldy = self.folder.test_folder
        util = getUtility(IPigeonholizer)
        util.pigeonholize("Folder")
        util.unpigeonholize("Folder")        
        self.failUnless(not IPigeonholeAware.providedBy(foldy))
        self.failUnless('Folder' not in util.ph_aware_types)

class TestEventSubscribers(FunctionalTestCase):
    
    def testNewContentMarked(self):
        """Newly-created content should be marked as IPigeonholeAware"""
        self.folder.invokeFactory("Document", "doc")
        doc = self.folder.doc
        self.failUnless(IPigeonholeAware.providedBy(doc))
    
    def testCopiedFTIsAreAwareWhenTheyShouldBe(self):
        """This is a bug David caught.  Object created events precede
         the portal_type assignment"""
        self.setRoles(('Manager',))
        util = getUtility(IPigeonholizer)

        if 'News Item' in util.ph_aware_types:
            util.unpigeonholize('News Item')

        # copy a portal_types FTI, call it a Pigeon
        portal_types = self.portal.portal_types
        cb_copy_data = portal_types.manage_copyObjects(['News Item'])
        paste_data = portal_types.manage_pasteObjects(cb_copy_data)
        temp_id = paste_data[0]['new_id']
        portal_types.manage_renameObject(temp_id, 'Pigeon')
        
        # make the Pigeon aware
        util.pigeonholize("Pigeon")
        
        # create a new one
        self.folder.invokeFactory('Pigeon', 'le_pigeon')
        
        # is it Aware?
        self.failUnless(IPigeonholeAware.providedBy(self.folder.le_pigeon), 'Known issue on Plone 3.')
        
    def testCopiedFTIsAreNotAwareWhenTheyShouldntBe(self):
        """Corollary to the above bug -- copied FTIs should
        not automatically inherit their parents settings """
        self.setRoles(('Manager',))
        util = getUtility(IPigeonholizer)

        if 'News Item' not in util.ph_aware_types:
            util.pigeonholize('News Item')

        # copy a portal_types FTI, call it a Stool
        portal_types = self.portal.portal_types
        cb_copy_data = portal_types.manage_copyObjects(['News Item'])
        paste_data = portal_types.manage_pasteObjects(cb_copy_data)
        temp_id = paste_data[0]['new_id']
        portal_types.manage_renameObject(temp_id, 'Stool')
                
        # create a new one
        self.folder.invokeFactory('Stool', 'Pigeon')
        
        # should NOT be Aware
        self.failIf(IPigeonholeAware.providedBy(self.folder.Pigeon), 'Known issue on Plone 3.')
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtility))
    suite.addTest(unittest.makeSuite(TestEventSubscribers))
    return suite
