from zope.app.form.browser import MultiCheckBoxWidget
from zope.app.form.browser import TextAreaWidget
from zope import schema
from zope.formlib.form import FormFields

from zope.interface import Interface
from zope.interface import implements
from zope.component import adapts
from zope.component import getUtility
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.widgets import MultiCheckBoxThreeColumnWidget
from plone.fieldsets.fieldsets import FormFieldsets

from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.interfaces import IPigeonholizer

class IPHTypes(Interface):

    ph_aware_types = schema.Tuple(title=u"Pigeonhole-aware Content Types",
                           description=u"Which content types should be extended to contain the metadata fields listed below?",
                           missing_value=tuple(),
                           value_type=schema.Choice(vocabulary="plone.app.vocabularies.ReallyUserFriendlyTypes"),
                           )
    show_warning = schema.Bool(title=u"Should users get a warning for content that has not had the Pigeonhole settings filled out?",
                              description=u"The warning simply highlights the Categorization tab in the edit page.")

class IPHFieldOne(Interface):
    ph_field_visible_1 = schema.Bool(title=u"Should Field 1 be active?", 
                              description=u"Should this field show up on the edit form?")
    ph_field_name_1 = schema.TextLine(title=u"Field 1 Name", description=u" ", default=None, required=True)
    ph_field_description_1 = schema.Text(title=u"Field 1 Description",
                                  description=u"How would you like to describe this field to people editing content?",
                                  required=False,
                                  )
    ph_field_values_1 = schema.List(title=u"Field 1 Options",
                                    description=u"These are the keywords that may be assigned to content in the site. "
                                                 "Click the 'Add' button below to add a new option.",
                                    value_type=schema.TextLine(),
                                    )

class IPHFieldTwo(Interface):
    ph_field_visible_2 = schema.Bool(title=u"Should Field 2 be active?", 
                                     description=u"Should this field show up on the edit form?")
    ph_field_name_2 = schema.TextLine(title=u"Field 2 Name", description=u" ", default=None, required=True)
    ph_field_description_2 = schema.Text(title=u"Field 2 Description",
                                  description=u"How would you like to describe this field to people editing content?",
                                  required=False,
                                  )
    ph_field_values_2 = schema.List(title=u"Field 2 Options",
                                    description=u"These are the keywords that may be assigned to content in the site. "
                                                 " Click the 'Add' button below to add a new option.",
                                    value_type=schema.TextLine(),
                                    )

class IPHFieldThree(Interface):
    ph_field_visible_3 = schema.Bool(title=u"Should Field 3 be active?",
                                     description=u"Should this field show up on the edit form?")
    ph_field_name_3 = schema.TextLine(title=u"Field 3 Name", description=u" ", default=None, required=True)
    ph_field_description_3 = schema.Text(title=u"Field 3 Description",
                                  description=u"How would you like to describe this field to people editing content?",
                                  required=False,
                                  )
    ph_field_values_3 = schema.List(title=u"Field 3 Options",
                                    description=u"These are the keywords that may be assigned to content in the site. "
                                                 "Click the 'Add' button below to add a new option.",
                                    value_type=schema.TextLine(),
                                    )

class IPHFieldFour(Interface):
    ph_field_visible_4 = schema.Bool(title=u"Should Field 4 be active?", 
                                     description=u"Should this field show up on the edit form?")
    ph_field_name_4 = schema.TextLine(title=u"Field 4 Name", description=u" ", default=None, required=True)    
    ph_field_description_4 = schema.Text(title=u"Field 4 Description",
                                  description=u"How would you like to describe this field to people editing content?",
                                  required=False,
                                  )
    ph_field_values_4 = schema.List(title=u"Field 4 Options",
                                    description=u"These are the keywords that may be assigned to content in the site. "
                                                 "Click the 'Add' button below to add a new option.",
                                    value_type=schema.TextLine(),
                                    )

class IPigeonholeCPSchema(IPHTypes, IPHFieldOne, IPHFieldTwo, IPHFieldThree, IPHFieldFour):
    """Combined schema for the adapter lookup.
    """

class PigeonholeCPAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(IPigeonholeCPSchema)

    def __init__(self, context):
        super(PigeonholeCPAdapter, self).__init__(context)
        portal_properties = getToolByName(context, 'portal_properties')
        self.ph_props = getattr(portal_properties, 'pigeonhole')
        self.utility = getUtility(IPigeonholizer)
        self.smart_folder_tool = getToolByName(context, 'portal_atct')
        self.css_tool = getToolByName(context, 'portal_css')
        self.catalog  = getToolByName(context, 'portal_catalog')

    def _updateATCTTool(self, index, name=None, change_availability=None):
        """Helper method to update the index listings used in Collections.
           change_availability allows us to enable/disable explicitly only.
           Accepted values are: enable, disable, None (ie no change)
        """
        DEFAULT_CRITERIA = ('ATSelectionCriterion', # pick from existing vals
                            'ATListCriterion',      # ad hoc list (in case certain vals aren't indexed yet)
                            )
        args = { 'criteria': DEFAULT_CRITERIA, }
        if change_availability == 'disable':
            args['enabled'] = False
        elif change_availability == 'enable':
            args['enabled'] = True
        if name is not None:
            args['friendlyName'] = name
        
        if index not in self.smart_folder_tool.getIndexes():
            self.smart_folder_tool.addIndex(index, **args)
        else:
            self.smart_folder_tool.updateIndex(index, **args)

    def _updateVocab(self, field_num, new_vals):
        """delete old entries and set the property in the prop sheet
        for the correct field number"""
        if isinstance(new_vals, str):
            new_vals = (new_vals,)
        field_name = 'ph_field_%s' % field_num
        old_vals = getattr(self.ph_props, "ph_field_values_%s" % field_num)
        # find old entries and delete them
        for old_val in set(old_vals) - set(new_vals):
            query = {field_name:old_val,}
            for brain in self.catalog(**query):
                item = brain.getObject()
                mutator  = item.Schema().get(field_name).getMutator(item)
                vals = list(item.Schema().get(field_name).getAccessor(item)())
                vals.remove(old_val)
                mutator(vals)
                item.reindexObject()
        ph_field_values_x = "ph_field_values_%s" % field_num
        args = {ph_field_values_x: new_vals}
        self.ph_props.manage_changeProperties(**args)


    def set_ph_aware_types(self, value):
        if value is not None:
            to_add = [a for a in value if a not in self.utility.ph_aware_types]
            to_del = [a for a in self.utility.ph_aware_types if a not in value]
        
            for typ in to_add:
                self.utility.pigeonholize(typ)
            for typ in to_del:
                self.utility.unpigeonholize(typ)

    def get_ph_aware_types(self):
        return self.utility.ph_aware_types
    ph_aware_types = property(get_ph_aware_types, set_ph_aware_types)

    def set_show_warning(self, value):
        id = "++resource++unconfigured-ph-content.css"
        if value:
            value = True
        else:
            value = False
        if id in self.css_tool.getResourceIds():
            self.css_tool.getResource(id).setEnabled(value)
            self.css_tool.cookResources()
        # XXX we should really raise an exception here if we can't find the resource
    def get_show_warning(self):
        id = "++resource++unconfigured-ph-content.css"
        if id in self.css_tool.getResourceIds():
            return self.css_tool.getResource(id).getEnabled()
        # XXX we should really raise an exception here if we can't find the resource
        return False
    show_warning = property(get_show_warning, set_show_warning)

    def set_ph_field_name_1(self, value):
        self.ph_props.manage_changeProperties(ph_field_name_1=value)
        self._updateATCTTool('ph_field_1', name=value)
    def get_ph_field_name_1(self):
        return self.ph_props.ph_field_name_1
    ph_field_name_1 = property(get_ph_field_name_1, set_ph_field_name_1)

    def set_ph_field_values_1(self, value):
        self._updateVocab(1, value)
    def get_ph_field_values_1(self):
        return self.ph_props.ph_field_values_1
    ph_field_values_1 = property(get_ph_field_values_1, set_ph_field_values_1)

    def set_ph_field_visible_1(self, value):
        self.ph_props.manage_changeProperties(ph_field_visible_1=value)
        if value is False:
            change = "disable"
        else:
            change = "enable"
        self._updateATCTTool('ph_field_1', change_availability=change)
    def get_ph_field_visible_1(self):
        return self.ph_props.ph_field_visible_1
    ph_field_visible_1 = property(get_ph_field_visible_1, set_ph_field_visible_1)

    def set_ph_field_description_1(self, value):
        self.ph_props.manage_changeProperties(ph_field_description_1=value)
    def get_ph_field_description_1(self):
        return self.ph_props.ph_field_description_1
    ph_field_description_1 = property(get_ph_field_description_1, set_ph_field_description_1)

    def set_ph_field_name_2(self, value):
        self.ph_props.manage_changeProperties(ph_field_name_2=value)
        self._updateATCTTool('ph_field_2', name=value)
    def get_ph_field_name_2(self):
        return self.ph_props.ph_field_name_2
    ph_field_name_2 = property(get_ph_field_name_2, set_ph_field_name_2)

    def set_ph_field_values_2(self, value):
        self._updateVocab(2, value)
    def get_ph_field_values_2(self):
        return self.ph_props.ph_field_values_2
    ph_field_values_2 = property(get_ph_field_values_2, set_ph_field_values_2)

    def set_ph_field_visible_2(self, value):
        self.ph_props.manage_changeProperties(ph_field_visible_2=value)
        if value is False:
            change = "disable"
        else:
            change = "enable"
        self._updateATCTTool('ph_field_2', change_availability=change)
    def get_ph_field_visible_2(self):
        return self.ph_props.ph_field_visible_2
    ph_field_visible_2 = property(get_ph_field_visible_2, set_ph_field_visible_2)

    def set_ph_field_description_2(self, value):
        self.ph_props.manage_changeProperties(ph_field_description_2=value)
    def get_ph_field_description_2(self):
        return self.ph_props.ph_field_description_2
    ph_field_description_2 = property(get_ph_field_description_2, set_ph_field_description_2)

    def set_ph_field_name_3(self, value):
        self.ph_props.manage_changeProperties(ph_field_name_3=value)
        self._updateATCTTool('ph_field_3', name=value)
    def get_ph_field_name_3(self):
        return self.ph_props.ph_field_name_3
    ph_field_name_3 = property(get_ph_field_name_3, set_ph_field_name_3)

    def set_ph_field_values_3(self, value):
        self._updateVocab(3, value)
    def get_ph_field_values_3(self):
        return self.ph_props.ph_field_values_3
    ph_field_values_3 = property(get_ph_field_values_3, set_ph_field_values_3)

    def set_ph_field_visible_3(self, value):
        self.ph_props.manage_changeProperties(ph_field_visible_3=value)
        if value is False:
            change = "disable"
        else:
            change = "enable"
        self._updateATCTTool('ph_field_3', change_availability=change)
    def get_ph_field_visible_3(self):
        return self.ph_props.ph_field_visible_3
    ph_field_visible_3 = property(get_ph_field_visible_3, set_ph_field_visible_3)

    def set_ph_field_description_3(self, value):
        self.ph_props.manage_changeProperties(ph_field_description_3=value)
    def get_ph_field_description_3(self):
        return self.ph_props.ph_field_description_3
    ph_field_description_3 = property(get_ph_field_description_3, set_ph_field_description_3)

    def set_ph_field_name_4(self, value):
        self.ph_props.manage_changeProperties(ph_field_name_4=value)
        self._updateATCTTool('ph_field_4', name=value)
    def get_ph_field_name_4(self):
        return self.ph_props.ph_field_name_4
    ph_field_name_4 = property(get_ph_field_name_4, set_ph_field_name_4)

    def set_ph_field_values_4(self, value):
        self._updateVocab(4, value)
    def get_ph_field_values_4(self):
        return self.ph_props.ph_field_values_4
    ph_field_values_4 = property(get_ph_field_values_4, set_ph_field_values_4)

    def set_ph_field_visible_4(self, value):
        self.ph_props.manage_changeProperties(ph_field_visible_4=value)
        if value is False:
            change = "disable"
        else:
            change = "enable"
        self._updateATCTTool('ph_field_4', change_availability=change)
    def get_ph_field_visible_4(self):
        return self.ph_props.ph_field_visible_4
    ph_field_visible_4 = property(get_ph_field_visible_4, set_ph_field_visible_4)

    def set_ph_field_description_4(self, value):
        self.ph_props.manage_changeProperties(ph_field_description_4=value)
    def get_ph_field_description_4(self):
        return self.ph_props.ph_field_description_4
    ph_field_description_4 = property(get_ph_field_description_4, set_ph_field_description_4)

class TinyTextAreaWidget(TextAreaWidget):
    """We don't need much for our descriptions"""

    height=5
    width=30

fs_phtypes = FormFieldsets(IPHTypes)
fs_phtypes.id = 'phtypes'
fs_phtypes.label = u'Basic Settings'

fs_phfield1 = FormFieldsets(IPHFieldOne)
fs_phfield1.id = 'phfield1'
fs_phfield1.label = u'Field 1'

fs_phfield2 = FormFieldsets(IPHFieldTwo)
fs_phfield2.id = 'phfield2'
fs_phfield2.label = u'Field 2'

fs_phfield3 = FormFieldsets(IPHFieldThree)
fs_phfield3.id = 'phfield3'
fs_phfield3.label = u'Field 3'

fs_phfield4 = FormFieldsets(IPHFieldFour)
fs_phfield4.id = 'phfield4'
fs_phfield4.label = u'Field 4'

class PHMultiCheckBoxWidget(MultiCheckBoxWidget):

    def __init__(self, field, request):
        """Initialize the widget."""
        super(MultiCheckBoxWidget, self).__init__(field,
            field.value_type.vocabulary, request)


class PigeonholeCP(ControlPanelForm):

    form_fields = FormFieldsets(fs_phtypes, fs_phfield1, fs_phfield2, fs_phfield3, fs_phfield4)

    # title of the page
    label = "Pigeonhole settings"
    # explanatory text
    description = u"""Pigeonhole is an add-on to Plone that allows you to modify content types
                    to include up to four custom axes of metadata.  In these settings, you decide
                    how many of these fields are active, what they are called, and what their 
                    keywords options should be, as well as to which content types they should apply."""
    # fieldset legend
    form_name = "Pigeonhole settings"
    form_fields['ph_aware_types'].custom_widget = MultiCheckBoxThreeColumnWidget
    for i in range(1,5):
        form_fields['ph_field_description_%s' % i].custom_widget = TinyTextAreaWidget
