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

class IRelatedContentPortlet(IPortletDataProvider):

    portlet_title = schema.TextLine(title=u"Title for the portlet",
                                    default=u"Also See...",
                                    required=True)

    number_of_items = schema.Int(title=u"Number of items to display",
                                 description=u"What's the maximum number of items to appear "
                                              "in this portlet?",
                                 default=3)

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

class Assignment(base.Assignment):
    implements(IRelatedContentPortlet)

    def __init__(self, portlet_title="", number_of_items=3, which_fields_relate=(), which_content_types=('Document',)):
        self.portlet_title = portlet_title
        self.number_of_items = number_of_items
        self.which_fields_relate = which_fields_relate
        self.which_content_types = which_content_types

    @property
    def title(self):
        return u"Related Content Portlet"

class Renderer(base.Renderer):

    render = ViewPageTemplateFile('relatedcontent.pt')

    @property
    def available(self):
        return len(self._data()) > 0

    def getRelatedContent(self):
        return self._data()[:self.data.number_of_items]

    def getPortletHeader(self):
        return self.data.portlet_title

    def css_class(self):
        """Generate a CSS class from the portlet header
        """
        header = self.data.portlet_title
        normalizer = getUtility(IIDNormalizer)
        return "portlet-related-content-%s" % normalizer.normalize(header)

    # By using the @memoize decorator, the return value of the function will
    # be cached. Thus, calling it again does not result in another query.
    # See the plone.memoize package for more.
    @memoize
    def _data(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        portal = getToolByName(self.context, 'portal_url').getPortalObject()

        query = {'sort_on': 'Date',
                 'sort_order': 'reverse',
                 'portal_type': self.data.which_content_types,
                 'review_state': 'published',
                 'sort_limit': self.data.number_of_items+1,
                 'is_relatable': True,
                 }
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
        
        # weed out the current page
        me = self.context.absolute_url()
        results = [b for b in catalog(**query) if b.getURL() != me]
        return results[:self.data.number_of_items]


class AddForm(base.AddForm):
    form_fields = form.Fields(IRelatedContentPortlet)
    label = u"Add Related Content portlet"
    description = u'This portlet displays a list of content from the site that is considered "related" to the current ' + \
                  u'page.  It sorts them by their "Effective Date" (more or less the date they were published).  It shows just their Title.'

    form_fields['which_fields_relate'].custom_widget = PHMultiCheckBoxWidget
    form_fields['which_content_types'].custom_widget = MultiCheckBoxThreeColumnWidget

    def create(self, data):
        assignment = Assignment()
        form.applyChanges(assignment, self.form_fields, data)
        return assignment

class EditForm(base.EditForm):
    form_fields = form.Fields(IRelatedContentPortlet)
    label = u"Edit Related Content portlet"
    description = u'This portlet displays a list of content from the site that is considered "related" to the current ' + \
                  u'page.  It sorts them by their "Effective Date" (more or less the date they were published).  It shows just their Title.'
    form_fields['which_fields_relate'].custom_widget = PHMultiCheckBoxWidget
    form_fields['which_content_types'].custom_widget = MultiCheckBoxThreeColumnWidget
