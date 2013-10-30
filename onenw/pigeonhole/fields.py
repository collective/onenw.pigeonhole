from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes import atapi
from types import DictType
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_base

class CheckboxField(ExtensionField, atapi.BooleanField):
    pass

class TagsField(ExtensionField, atapi.LinesField):
    
    def __init__(self, name=None, **kwargs):
        """Override the normal init so that we can store which field this is.
        This lets us reuse this type for multiple fields in a single content type.

        Sorry for the hack."""
        if kwargs.has_key('field_num'):
            self.field_num = kwargs["field_num"]
        atapi.LinesField.__init__(self, name, **kwargs)

    def Vocabulary(self, content_instance):
        portal_properties = getToolByName(content_instance, 'portal_properties')
        props = portal_properties.pigeonhole
        return atapi.DisplayList([(x, x) for x in props.getProperty('ph_field_values_%s' % self.field_num)])

# from AT.Widget
_marker = []

class PHMultiSelectionWidget(atapi.MultiSelectionWidget):
    """We need to customize this widget so that we can have dynamic values for certain
       properties, but without being able to touch the content object's class (to
       create methods there).  They're all derived from the property sheet."""
       
    field_num = 0
       
    def __init__(self, *args, **kwargs):
        if kwargs.has_key('field_num'):
            self.field_num = kwargs["field_num"]
        super(atapi.MultiSelectionWidget, self).__init__(*args, **kwargs)

    def Label(self, instance, **kwargs):
        """Returns a label, ideally from the PH property sheet and corresponding to the number of the field."""
        portal_properties = getToolByName(instance, 'portal_properties')
        if hasattr(portal_properties, "pigeonhole"):
            # sorry for the gratuitous meta-ness
            label_label = "ph_field_name_%s" % self.field_num 
            if hasattr(portal_properties.pigeonhole, label_label):
                return getattr(portal_properties.pigeonhole, label_label)
        return self._translate_attribute(instance, 'label')

    def isVisible(self, instance, mode='view'):
        """Extend the default isVisible from AT to include a "dynamic" option,
        derived from the property sheet.  Still use the visible dict. Dynamic
        means consult property sheet for this field; True means visible, False invisible.
        
        Original doc string from AT:
        decide if a field is visible in a given mode -> 'state'

        Return values are visible, hidden, invisible

        The value for the attribute on the field may either be a dict with a
        mapping for edit and view::

            visible = { 'edit' :'hidden', 'view' : 'invisible' }

        Or a single value for all modes::

            True/1:  'visible'
            False/0: 'invisible'
            -1:      'hidden'
            
        visible: The field is shown in the view/edit screen
        invisible: The field is skipped when rendering the view/edit screen
        hidden: The field is added as <input type="hidden" />

        The default state is 'visible'.
        """
        vis_dic = getattr(aq_base(self), 'visible', _marker)
        state = 'visible'
        if vis_dic is _marker:
            return state
        if type(vis_dic) is DictType:
            state = vis_dic.get(mode, state)
            if state == 'dynamic':
                portal_properties = getToolByName(instance, 'portal_properties')
                if hasattr(portal_properties, "pigeonhole"):
                    visible_label = "ph_field_visible_%s" % self.field_num 
                    if hasattr(portal_properties.pigeonhole, visible_label):
                        v = getattr(portal_properties.pigeonhole, visible_label)
                        if not v:
                            return "invisible"
                return 'visible'
        elif not vis_dic:
            state = 'invisible'
        elif vis_dic < 0:
            state = 'hidden'
        return state

    def Description(self, instance, **kwargs):
        """Returns the description, dynamically derived from the property sheet."""
        portal_properties = getToolByName(instance, 'portal_properties')
        if hasattr(portal_properties, "pigeonhole"):
            description_label = "ph_field_description_%s" % self.field_num 
            if hasattr(portal_properties.pigeonhole, description_label):
                return getattr(portal_properties.pigeonhole, description_label)
        return self.description
