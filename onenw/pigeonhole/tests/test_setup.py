import unittest
from zope.component import queryUtility
from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.interfaces import IPigeonholizer
from onenw.pigeonhole.interfaces import IPigeonholeAware
from onenw.pigeonhole.tests.base import FunctionalTestCase
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter

class TestSetup(FunctionalTestCase):
    
    def afterSetUp(self):
        self.types = getToolByName(self.portal, 'portal_types')

    def test_product_installed(self):
        installer = getToolByName(self.portal, 'portal_quickinstaller')
        installed_products =  [ x['id'] for x in installer.listInstalledProducts() ]
        self.failUnless('onenw.pigeonhole' in installed_products,
                        "No PH in installed products: %s" % installed_products)

    def test_utility(self):
        utility = queryUtility(IPigeonholizer)
        self.assertNotEquals(None, utility)

    def test_view(self):
        view = self.portal.restrictedTraverse('@@phawareness_view')
        self.assertNotEquals(None, view)

    def test_atct_tool(self):
        tool = getToolByName(self.portal, 'portal_atct')
        # getIndex() will throw an error if they don't exist
        index1 = tool.getIndex('ph_field_1')
        index2 = tool.getIndex('ph_field_2')
        is_relatable = tool.getIndex('is_relatable')

        self.failUnless(index1.friendlyName=='Audience')
        self.failUnless(index1.enabled is True)
        self.failUnless(index2.friendlyName=='Program Area')
        self.failUnless(index2.enabled is True)
        self.failUnless(is_relatable.friendlyName=='Relatable')
        self.failUnless(is_relatable.enabled is True)

    def test_cssregistry(self):
        tool = getToolByName(self.portal, 'portal_css')
        id = "++resource++unconfigured-ph-content.css"
        self.failUnless(id in tool.getResourceIds())

    def test_indexes_installed(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        indices = catalog.indexes()
        for x in range(1,5):
            i = "ph_field_%s" % x
            self.failUnless(i in indices, "Index '%s' missing from portal_catalog after install" % (i))
        self.failUnless('is_relatable' in indices,
                    "Index 'is_relatable' not in portal_catalog after install")

class TestUninstall(FunctionalTestCase):
    
    def afterSetUp(self):
        # uninstall our product
        qi = getToolByName(self.portal, "portal_quickinstaller")
        qi.uninstallProducts(products=['onenw.pigeonhole',])
        
    def test_uninstall_stops_pigeonholization(self):
        # homepage should no longer be marked
        homey = getattr(self.portal, 'front-page')
        self.failIf(IPigeonholeAware.providedBy(homey))
        
        # create a new page (which is a default PH type) -- it should
        # also not be providing the interface
        self.folder.invokeFactory('Document', 'doc')
        self.failIf(IPigeonholeAware.providedBy(self.folder.doc))

    def test_uninstall_removes_cruft(self):
        """Test for the things that Generic Setup doesn't seem to take
           care of for us"""
        # indexes should be gone
        catalog = getToolByName(self.portal, 'portal_catalog')
        indices = catalog.indexes()
        for x in range(1,5):
            i = "ph_field_%s" % x
            self.failIf(i in indices, "Index '%s' still in portal_catalog after uninstall" % (i))
        self.failIf('is_relatable' in indices,
                    "Index 'is_relatable' still in portal_catalog after uninstall")

        # actionicon should be gone
        icons = getToolByName(self.portal, 'portal_actionicons')
        self.failIf('pigeonhole' in [a.getActionId() for a in icons.listActionIcons()],
                    "'pigeonhole' action icon still present after uninstall")

        # control panel configlet should be gone
        ctl = getToolByName(self.portal, 'portal_controlpanel')
        self.failIf('pigeonhole' in [a.getId() for a in ctl.listActions()],
                    'Control Panel configlet still registered after uninstall')
        
        # property sheet should be gone
        props = getToolByName(self.portal, 'portal_properties')
        self.failIf('pigeonhole' in props,
                    "Property sheet still in portal_properties after uninstall.")
        
        # indices shouldn't be in the ATCT tool
        atct = getToolByName(self.portal, 'portal_atct')
        indices = atct.getIndexes()
        for x in range(1,5):
            index = "ph_field_%s" % x
            self.failIf(index in indices, "%s in ATCT tool's list of indices")
        self.failIf('is_relatable' in indices)

        css = getToolByName(self.portal, 'portal_css')
        id = "++resource++unconfigured-ph-content.css"
        self.failIf(id in css.getResourceIds())

class TestReinstall(FunctionalTestCase):

    def testReinstallationPreservesSettings(self):
        ctl = PigeonholeCPAdapter(self.portal)
        # adding new types
        new_ph_types = ctl.get_ph_aware_types() + ['File',]
        ctl.set_ph_aware_types(new_ph_types)

        # make sure it's there
        self.failUnless("File" in ctl.ph_aware_types)

        # reinstall
        self.setRoles(['Manager'])
        qi = getToolByName(self.portal, "portal_quickinstaller")
        qi.reinstallProducts(products=['onenw.pigeonhole',])

        ctl = PigeonholeCPAdapter(self.portal)

        # make sure it's still there
        self.failUnless("File" in ctl.ph_aware_types)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSetup))
    suite.addTest(unittest.makeSuite(TestUninstall))
    suite.addTest(unittest.makeSuite(TestReinstall))
    return suite
