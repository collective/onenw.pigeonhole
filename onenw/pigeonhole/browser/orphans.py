from zope.interface import implements
from Acquisition import aq_inner

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.interfaces import IOrphans
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter

class Orphans(BrowserView):
    """A browser class rescuing orphaned Pigeonhole metadata.
       ("Orphaned" means data tagged with values that, for whatever reason, are no longer options.)
    """
    implements(IOrphans)

    def findOrphans(self):
        """Print a list of keywords for each Pigeonhole index (whether it's enabled or not) that don't correspond with the
        current list of options, and a count for the number of content items that are so tagged.
        """
        context = aq_inner(self.context)
        portal_url = getToolByName(context, 'portal_url')
        portal = portal_url.getPortalObject()
        portal_catalog = getToolByName(context, 'portal_catalog')
        results = {}
        ctl = PigeonholeCPAdapter(portal)
        for x in range(1,5):
            getValues     = getattr(ctl, 'get_ph_field_values_%s' % x)
            valid_options = set(getValues())
            field_name    = 'ph_field_%s' % x
            existing_vals = set([v for v in portal_catalog.uniqueValuesFor(name=field_name) if v is not None])
            orphans       = existing_vals - valid_options
            if orphans:
                results[field_name] = list(orphans)
        return results

    def saveOrphans(self, mapping):
        """Takes a mapping like IKeywordMigrator.migrateKeywords to remap content.  The differences are:
           - it doesn't touch the settings
           - you can map to None, which removes the tag without reassigning to anything

           Typically called from temporary scripts where the mapping is set up manually.
           """
        context = aq_inner(self.context)
        catalog = getToolByName(context, 'portal_catalog')
        portal_url = getToolByName(context, 'portal_url')
        portal = portal_url.getPortalObject()        
        changed_objects = 0
        for value in mapping:
            new_option = value['new_option']
            old_option = value['old_option']
            ph_field = index = value['field_id']
            query = {index:old_option}
            for brain in catalog(**query):
                obj = brain.getObject()
                field = obj.Schema().get(ph_field)
                vals = list(field.getAccessor(obj)())
                vals.remove(old_option)
                if new_option is not None:
                    vals.append(new_option)
                field.getMutator(obj)(vals)
                obj.reindexObject()
                changed_objects += 1
                
        return "Changed keywords, touching, at the very most, %s pieces of content" % (changed_objects)
         