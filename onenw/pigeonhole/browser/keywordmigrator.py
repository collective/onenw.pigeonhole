from zope.interface import implements
from Acquisition import aq_inner

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

from onenw.pigeonhole.interfaces import IKeywordMigrator
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter


class KeywordMigrator(BrowserView):
    """Provides view methods for migrating PH keywords -- both settings
    and existing content"""

    implements(IKeywordMigrator)

    def getKeywords(self):
        """Returns a list of dicts of PH field names and options for all PH fields
        that are *active* and *actually have options*.
        """
        context = aq_inner(self.context)
        portal_url = getToolByName(context, 'portal_url')
        portal = portal_url.getPortalObject()
        ctl = PigeonholeCPAdapter(portal)
        results = []
        for x in range(1, 5):
            is_visible = getattr(ctl, 'get_ph_field_visible_%s' % x)
            if is_visible():
                getField_name = getattr(ctl, 'get_ph_field_name_%s' % x)
                getValues = getattr(ctl, 'get_ph_field_values_%s' % x)
                options = getValues()
                if options:
                    results.append({'field_id': 'ph_field_%s' % x,
                                    'field_name': getField_name(),
                                    'options': options},)
        return results

    def migrateKeywords(self, mapping=None):
        """Parses the Request to map field ids & old option values to new values.

           Does two things:
            - grabs each item that has that value assigned and remaps
            - changes the options in the PH settings from the old option
              to the new one.

           mapping, or request form var 'keywords' should look something like this:
           ({'field_id': 'ph_field_1', 'old_option': 'NASCAR Dads', 'new_option': 'NASCAR Parents',},
            {'field_id': 'ph_field_1', 'old_option': 'Soccer Moms', 'new_option': 'Soccer Parents',},
            {'field_id': 'ph_field_2', 'old_option': 'Willamette Valley', 'new_option': 'Western Oregon',},)

            XXX: Note that at the moment, we're assuming that for any single PH field,
            there won't be more than 26 keyword options available.  More than that would
            require using a different pick widget in the edit form as well as some
            refactoring here.  More than 26 is pretty silly, though, no?
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, 'portal_catalog')
        portal_url = getToolByName(context, 'portal_url')
        portal = portal_url.getPortalObject()
        ctl = PigeonholeCPAdapter(portal)
        if mapping is None:
            mapping = getattr(self.request, 'keywords', None)
            if mapping is None:
                return

        changed_objects = 0
        changed_options = 0
        for value in mapping:
            new_option = value['new_option']
            new_option.strip()
            if new_option != '' and new_option != value['old_option']:
                old_option = value['old_option']
                # so now we have non-empty fields that differ
                # migration time

                # Step 1: migrate content objects
                ph_field = index = value['field_id']
                field_number = ph_field[-1]
                query = {index: old_option}
                for brain in catalog(**query):
                    obj = brain.getObject()
                    field = obj.Schema().get(ph_field)
                    vals = list(field.getAccessor(obj)())
                    vals.remove(old_option)
                    vals.append(new_option)
                    field.getMutator(obj)(vals)
                    obj.reindexObject()
                    changed_objects += 1

                # Step 2: reset options, but preserve the order
                options = getattr(ctl, 'get_ph_field_values_%s' % field_number)()
                if isinstance(options, str):
                    options = [options, ]
                else:
                    options = list(options)
                if new_option not in options:
                    # Put the new option in place of the old
                    options[options.index(old_option)] = new_option
                else:
                    # Just remove any and all occurrences of the old option
                    options = [o for o in options if o != old_option]
                getattr(ctl, 'set_ph_field_values_%s' % field_number)(options)
                changed_options += 1
        feedback = "Changed %s keywords, touching, at the very most, %s pieces of content (some of them may have been touched more than once)" % (changed_options,
                                                                            changed_objects)
        IStatusMessage(self.request).addStatusMessage(feedback)
        self.request.response.redirect("%s/@@keyword_migrator" % context.absolute_url())
