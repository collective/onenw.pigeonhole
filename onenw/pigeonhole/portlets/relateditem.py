import random
from zope import schema
from zope.component import getUtility
from zope.formlib import form
from zope.interface import implements

from plone.app.portlets.portlets import base
from plone.app.controlpanel.widgets import MultiCheckBoxThreeColumnWidget
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.browser.configlet import PHMultiCheckBoxWidget
from onenw.pigeonhole.catalog import ph_field_1, ph_field_2,\
                                     ph_field_3, ph_field_4

def vocabulary(choices):
    """Create a SimpleVocabulary from a list of values and titles."""
    return schema.vocabulary.SimpleVocabulary(
               [schema.vocabulary.SimpleTerm(v, title=v) for v in choices])

TIEBREAKER_RANDOM = u'Choose a random one'
TIEBREAKER_DATE   = u'Choose the most recently published one'

class IRelatedItemPortlet(IPortletDataProvider):

    portlet_title = schema.TextLine(title=u"Title for the portlet",
                                    default=u"Overheard...",
                                    required=True)

    header_override = schema.Bool(title=u"Use the item's Title as the portlet's title instead",
                                 description=u"Check here if, instead of the title entered above, you'd like to use the item's title for the portlet.",
                                 default=False)

    which_fields_relate = schema.Tuple(title=u'Which fields determine "relatedness"?',
                                       description=u'For which of the following fields must content need to overlap with the current page in order to be considered "related"?',
                                       default=(),
                                       value_type=schema.Choice(vocabulary="onenw.pigeonhole.vocabularies.ActiveFieldsVocabularyFactory"),
                                       )

    which_content_types = schema.Tuple(title=u"Which Content Types?",
                           description=u"Which content types should be candidates for this portlet?",
                           default=('Document',),
                           value_type=schema.Choice(vocabulary="onenw.pigeonhole.vocabularies.PigeonholeTypesVocabularyFactory"),
                           )
    
    tie_breaker = schema.Choice(title=u"Tie Breaker Method",
                                description=u"If more than one item matches the above criteria, how should ties be resolved?",
                                default=TIEBREAKER_RANDOM,
                                vocabulary=vocabulary((TIEBREAKER_RANDOM, TIEBREAKER_DATE,)),
                               )

class Assignment(base.Assignment):
    implements(IRelatedItemPortlet)

    def __init__(self, portlet_title="", header_override=False, which_fields_relate=(), which_content_types=('Document',), tie_breaker=TIEBREAKER_RANDOM):
        self.portlet_title = portlet_title
        self.header_override = header_override
        self.which_fields_relate = which_fields_relate
        self.which_content_types = which_content_types
        self.tie_breaker = tie_breaker

    @property
    def title(self):
        return u"Related Item Portlet"

class Renderer(base.Renderer):

    render = ViewPageTemplateFile('relateditem.pt')

    @property
    def available(self):
        return self._data() is not None

    def getRelatedItem(self):
        return self._data()

    def getPortletHeader(self):
        if self.data.header_override and self._data() is not None:
            return self._data().Title()
        else:
            return self.data.portlet_title

    def css_class(self):
        """Generate a CSS class from the portlet header
        """
        header = self.data.portlet_title
        normalizer = getUtility(IIDNormalizer)
        return "portlet-related-item-%s" % normalizer.normalize(header)

    # By using the @memoize decorator, the return value of the function will
    # be cached. Thus, calling it again does not result in another query.
    # See the plone.memoize package for more.        
    @memoize
    def _data(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        portal =  getToolByName(self.context, 'portal_url').getPortalObject()

        query = {'portal_type': self.data.which_content_types,
                 'review_state': 'published',
                 'is_relatable': True,
                 }
        if self.data.tie_breaker == TIEBREAKER_DATE:
            query['sort_on'] = 'Date'
            query['sort_limit'] = 1
            query['sort_order'] = 'reverse'
        
        active_field_ids = self.data.which_fields_relate

        # (not doing this in a loop bc getting the ph_field_* methods might be a little ugly looking)
        if "ph_field_1" in active_field_ids:
            query['ph_field_1'] = ph_field_1(self.context, portal)
        if "ph_field_2" in active_field_ids:
            query['ph_field_2'] = ph_field_2(self.context, portal)
        if "ph_field_3" in active_field_ids:
            query['ph_field_3'] = ph_field_3(self.context, portal)
        if "ph_field_4" in active_field_ids:
            query['ph_field_4'] = ph_field_4(self.context, portal)
        
        # for now we won't weed out the current page -- unlikely to be an issue
        results = catalog(**query)
        if not results:
            return None
        else:
            if self.data.tie_breaker == TIEBREAKER_RANDOM:
                item = random.choice(results)
            else:
                item = results[0]
            return item.getObject()


class AddForm(base.AddForm):
    form_fields = form.Fields(IRelatedItemPortlet)
    label = u"Add Related Item portlet"
    description = u'This portlet displays the body of a single item from the site that is considered "related" to the current page.'

    form_fields['which_fields_relate'].custom_widget = PHMultiCheckBoxWidget
    form_fields['which_content_types'].custom_widget = MultiCheckBoxThreeColumnWidget

    def create(self, data):
        assignment = Assignment()
        form.applyChanges(assignment, self.form_fields, data)
        return assignment

class EditForm(base.EditForm):
    form_fields = form.Fields(IRelatedItemPortlet)
    label = u"Edit Related Content portlet"
    description = u'This portlet displays the body of a single item from the site that is considered "related" to the current page.'
    form_fields['which_fields_relate'].custom_widget = PHMultiCheckBoxWidget
    form_fields['which_content_types'].custom_widget = MultiCheckBoxThreeColumnWidget
