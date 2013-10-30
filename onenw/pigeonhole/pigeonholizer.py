from zope.interface import implements
from zope.interface import alsoProvides
from zope.interface import directlyProvides, directlyProvidedBy
from zope.component import getUtility
from zope.component import adapter
from zope.component.interfaces import ComponentLookupError
from zope.app.component.hooks import getSite
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from Products.Archetypes.interfaces import IBaseObject
from Products.CMFCore.utils import getToolByName

from onenw.pigeonhole.interfaces import IPigeonholizer
from onenw.pigeonhole.interfaces import IPigeonholeAware

try:
    # add support for blob-based Images and Files
    from plone.app.blob.interfaces import IATBlobFile, IATBlobImage
    blobsAvailable = True
except ImportError:
    blobsAvailable = False

# for new versions of at.schemaextender, we'll need to explicitly invalidate
# its cache
try:
    from archetypes.schemaextender.extender import disableCache
except ImportError:
    disableCache = None

class Pigeonholizer(object):
    """Local utility to designate and remember which types are Pigeonhole aware"""

    implements(IPigeonholizer)

    def getPHAwareTypes(self):
        """Return the values listed in the property sheet"""
        site = getSite()
        properties = getToolByName(site, 'portal_properties')
        ph_props = properties.get('pigeonhole', None)
        if ph_props and hasattr(ph_props, 'ph_aware_types'):
            return list(ph_props.ph_aware_types)
        return []
    
    def setPHAwareTypes(self, types):
        """Record list of types in property sheet"""
        site = getSite()
        properties = getToolByName(site, 'portal_properties')
        ph_props = properties.get('pigeonhole', None)
        if ph_props:
            ph_props.manage_changeProperties(ph_aware_types=types)
    
    ph_aware_types = property(getPHAwareTypes, setPHAwareTypes)
    

    def pigeonholize(self, portal_type):
        """Make a content type class PH aware"""
        site = getSite()
        catalog = getToolByName(site, 'portal_catalog')
        for brain in catalog(portal_type=portal_type):
            obj = brain.getObject()
            if not IPigeonholeAware.providedBy(obj):
                alsoProvides(obj, IPigeonholeAware)
        
        if portal_type not in self.ph_aware_types:
            self.ph_aware_types = self.ph_aware_types + [portal_type,]

    def unpigeonholize(self, portal_type):
        """Remove pigeonhole awareness from content_type"""
        site = getSite()
        catalog = getToolByName(site, 'portal_catalog')
        for brain in catalog(portal_type=portal_type):
            obj = brain.getObject()
            if IPigeonholeAware.providedBy(obj):
                directlyProvides(obj, directlyProvidedBy(obj)-IPigeonholeAware)
        
        self.ph_aware_types = list(set(self.ph_aware_types) - set([portal_type]))

# Our event handler for newly created AT content
# This is subscribed universally bc I don't know a local way
# This is mitigated by the conditional on having the local utility
@adapter(IBaseObject, IObjectCreatedEvent)
def markNewContentObject(obj, event):
    """Mark newly created content as Pigeonhole-aware if its 
    portal type is in our list of Aware types"""

    # get our local utility
    # this is incidentally also our lame check
    # to see if PH is installed here
    try:
        utility = getUtility(IPigeonholizer)
    except ComponentLookupError:
        # ignore problems when we can't find the utility -- PH might not
        # be installed
        utility = None
    if utility is not None:
        if obj.portal_type in utility.ph_aware_types:
            alsoProvides(obj, IPigeonholeAware)
        elif blobsAvailable:
            # in Plone 3, the meta_type for blob-based Images and Files
            # is just ATBlob, but thanks to a custom factory, they DO have
            # marker interfaces set. Check them!
            if "Image" in utility.ph_aware_types and \
                IATBlobImage.providedBy(obj):
                alsoProvides(obj, IPigeonholeAware)
            elif "File" in utility.ph_aware_types and \
                IATBlobFile.providedBy(obj):
                alsoProvides(obj, IPigeonholeAware)
        if disableCache is not None:
            disableCache(getSite().REQUEST)