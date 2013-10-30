try:
    from zope.app.schema.vocabulary import IVocabularyFactory
except ImportError:
    # Zope 2.13
    from zope.schema.interfaces import IVocabularyFactory
from zope.component import getUtility
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter
from onenw.pigeonhole.interfaces import IPigeonholizer


class ActiveFieldsVocabulary(object):
    """Vocabulary factory for active pigeonhole fields.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        portal = getToolByName(context, 'portal_url').getPortalObject()
        
        cp_adapter = PigeonholeCPAdapter(portal)
        items = []
        for x in range(1,5):
            field_visible = getattr(cp_adapter, "get_ph_field_visible_%s" % x)()
            if field_visible:
                field_id = 'ph_field_%s' % x
                field_name = getattr(cp_adapter, "get_ph_field_name_%s" % x)()
                items.append(SimpleTerm(field_id, field_id, field_name))
        return SimpleVocabulary(items)

ActiveFieldsVocabularyFactory = ActiveFieldsVocabulary()


class PigeonholeTypesVocabulary(object):
    """Vocabulary factory for content types that are Pigeonhole-aware.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        util = getUtility(IPigeonholizer)
        return SimpleVocabulary([SimpleTerm(t,t,t) for t in util.ph_aware_types])

PigeonholeTypesVocabularyFactory = PigeonholeTypesVocabulary()
