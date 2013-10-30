from zope.component import getUtility

from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.interfaces import IPigeonholizer
from onenw.pigeonhole.config import PH_DEFAULT_TYPES
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter



def install(self, reinstall=False):

    portal_quickinstaller = getToolByName(self, 'portal_quickinstaller')
    portal_setup = getToolByName(self, 'portal_setup')

    # run our profile first.  among other things, it sets up our local utility:
    # the Pigeonholizer!!!
    portal_setup.runAllImportStepsFromProfile('profile-onenw.pigeonhole:default', purge_old=False)
    portal_quickinstaller.notifyInstalled("Pigeonhole")

    # now that we have the utility, use it to retrofit our existing instances of our
    # core PH content types
    # XXX: should this be contingent on not reinstalling?  it's an expensive op...
    util = getUtility(IPigeonholizer)
    for ctype in PH_DEFAULT_TYPES:
        util.pigeonholize(ctype)

    if not reinstall:
        # make our indices available to Collections
        # (Note: These names should be what we're using in propertiestool.xml)
        ctl_panel = PigeonholeCPAdapter(self)
        ctl_panel.set_ph_field_name_1('Audience')
        ctl_panel.set_ph_field_visible_1(True)

        ctl_panel.set_ph_field_name_2('Program Area')
        ctl_panel.set_ph_field_visible_2(True)
        
        atct_tool = getToolByName(self, 'portal_atct')
        atct_tool.addIndex('is_relatable',
                           friendlyName="Relatable",
                           description="""Pages who have the 'candidate to be related' checkbox checked.""",
                           enabled=True,
                           criteria=('ATBooleanCriterion',),
                           ) 


def uninstall(self, reinstall=False):
    """If we're not reinstalling:
        - unmark all the content objects as ph-aware
        - remove cruft from portal
        
        At this point we're not removing (or testing for the removal of):
        - portlet registration (3 of them)
        - local component registration (a local adapter and a local utility)
    """

    if not reinstall:
        # remove marker interface from all relevant content objects
        # (the PH data in the content objects will probably persist,
        #  but it's lightweight and unobtrusive)
        util = getUtility(IPigeonholizer)
        for typ in util.ph_aware_types:
            util.unpigeonholize(typ)
        
        # remove indexes from portal_catalog
        catalog = getToolByName(self, 'portal_catalog')
        indices = catalog.indexes()
        for x in range(1,5):
            i = "ph_field_%s" % x
            if i in indices:
                catalog.delIndex(i)
        if "is_relatable" in indices:
            catalog.delIndex("is_relatable")
        
        # remove icon from portal_actionicons
        icons = getToolByName(self, 'portal_actionicons')
        if 'pigeonhole' in [a.getActionId().lower() for a in icons.listActionIcons()]:
            icons.removeActionIcon(category='controlpanel', action_id='pigeonhole')

        # remove control panel registration
        ctl = getToolByName(self, 'portal_controlpanel')
        if 'pigeonhole' in [a.getId() for a in ctl.listActions()]:
            ctl.unregisterConfiglet('pigeonhole')

        # remove property sheet
        props = getToolByName(self, 'portal_properties')
        if 'pigeonhole' in props:
            props._delObject('pigeonhole')
        
        # remove indices from atct_tool
        atct_tool = getToolByName(self, 'portal_atct')
        indices = atct_tool.getIndexes()
        if 'is_relatable' in indices:
            atct_tool.removeIndex('is_relatable')
        for x in range(1,5):
            index = "ph_field_%s" % x
            if index in indices:
                atct_tool.removeIndex(index)
        
