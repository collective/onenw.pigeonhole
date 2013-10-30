from Acquisition import aq_base
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
import pkg_resources

if pkg_resources.get_distribution('Plone').parsed_version >= ('00000003', '00000003'):
    from plone.indexer import indexer
    HAS_INDEXER = True
else:
    from Products.CMFPlone.CatalogTool import registerIndexableAttribute
    HAS_INDEXER = False
from onenw.pigeonhole.interfaces import IPigeonholeAware

def get_ph_field_value(field_number, obj):
    """
    Returns the value of the given Pigeon Hole field.
    """
    
    base_obj = aq_base(obj)
    if hasattr(base_obj, 'Schema'):
        field_name = "ph_field_%i" % field_number
        props = getToolByName(obj, "portal_properties")
        if props and hasattr(props, 'pigeonhole'):
            if getattr(props.pigeonhole, 
                'ph_field_visible_%i' % field_number, False):
                field = base_obj.Schema().get(field_name) 
                if field is not None:
                    return field.getAccessor(base_obj)()
    # if all else fails...
    return ()

def ph_field_1(obj, portal=None, **kwargs):
    """ Return the ph_field_1 value from this content object if appropriate.
        ("Appropriate" means that this field is enabled in the control panel.)
        For use primarily to catalog."""
    return get_ph_field_value(1, obj)

def ph_field_2(obj, portal=None, **kwargs):
    """ Return the ph_field_2 value from this content object if appropriate.
        ("Appropriate" means that this field is enabled in the control panel.)
        For use primarily to catalog."""
    return get_ph_field_value(2, obj)

def ph_field_3(obj, portal=None, **kwargs):
    """ Return the ph_field_3 value from this content object if appropriate.
        ("Appropriate" means that this field is enabled in the control panel.)
        For use primarily to catalog."""
    return get_ph_field_value(3, obj)

def ph_field_4(obj, portal=None, **kwargs):
    """ Return the ph_field_4 value from this content object if appropriate.
        ("Appropriate" means that this field is enabled in the control panel.)
        For use primarily to catalog."""
    return get_ph_field_value(4, obj)

def is_relatable(obj, portal=None, **kwargs):
    """ Return true if this obj has the relatable checkbox checked."""
    if hasattr(obj, 'Schema'):
        return obj.Schema().get('relatable').getAccessor(obj)()
    return False

def is_ph_configured(obj, portal=None, **kwargs):
    """ Returns true if it appears that obj has had its pigeonhole metadata set.
    
        We return False iff:
        - item is IPigeonholeAware
        - relatable is True (True by default)
        - active metadata fields are all empty
        (The idea is that relatable w/o KWs selected is a meaningless state and not
        intentional.  Note that it's not a dysfunctional state, but probably not how
        users want it to be.)
    """
    # if it's not PH Aware, this isn't super meaningful
    if not IPigeonholeAware.providedBy(obj):
        return True
    # check if relatable is checked
    if obj.Schema().get('relatable').getAccessor(obj)() is True:
        props = getToolByName(obj, "portal_properties")
        if props and hasattr(props, 'pigeonhole'):
            for x in range(1,5):
                field_name = "ph_field_%s" % x
                visible = "ph_field_visible_%s" % x
                if getattr(props.pigeonhole, visible):
                    field_val = obj.Schema().get(field_name).getAccessor(obj)()
                    if field_val and len(field_val)>0:
                        # good enough -- we found a field that is active and 
                        # has data
                        return True
            return False
    return True

# make these methods available to the portal_catalog
if HAS_INDEXER:
    # Plone 3.3+
    # These indexers need to be registered for Interface instead of
    # IPigeonholeAware because otherwise non-pigeonhole aware types can acquire
    # the values from a pigeonhole-aware parent.
    ph_indexer = indexer(Interface)
    ph_field_1_indexer = ph_indexer(ph_field_1)
    ph_field_2_indexer = ph_indexer(ph_field_2)
    ph_field_3_indexer = ph_indexer(ph_field_3)
    ph_field_4_indexer = ph_indexer(ph_field_4)
    is_relatable_indexer = ph_indexer(is_relatable)
    is_ph_configured_indexer = ph_indexer(is_ph_configured)
else:
    # BBB Plone < 3.3
    registerIndexableAttribute("ph_field_1", ph_field_1)
    registerIndexableAttribute("ph_field_2", ph_field_2)
    registerIndexableAttribute("ph_field_3", ph_field_3)
    registerIndexableAttribute("ph_field_4", ph_field_4)
    registerIndexableAttribute("is_relatable", is_relatable)
    registerIndexableAttribute("is_ph_configured", is_ph_configured)
