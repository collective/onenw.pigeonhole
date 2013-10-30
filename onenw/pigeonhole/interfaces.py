from zope.interface import Interface
from zope.interface import Attribute

class IPigeonholeAware(Interface):
    """Marker interface for Pigeonhole-aware content types"""



class IPHSchemaExtender(Interface):
    """Interface for our adapter.  This adapter makes normal content type classes
    Pigeonhole-aware by extending their schemas"""
    
    def getFields():
        """Returns the extra schema fields that we're adding on"""



class IPHAwarenessView(Interface):
    """Interface for our browser view"""
    
    def shouldBePHConfigured():
        """Returns True iff the current user has Modify portal content permission
        and context's Pigeonhole settings are not yet configured """

class IPigeonholizer(Interface):
    """Local utility to designate and remember which types are Pigeonhole aware"""

    # these are the interfaces that are PH Aware
    ph_aware_types = Attribute("""A list of types that are Pigeonhole-aware""")
    
    def pigeonholize(portal_type):
        """Make portal_type Pigeonhole-aware
        
        To preserve the "local" nature of PH (ie to not affect other Plone sites
        within this Zope) this is done in two steps:
        
        - mark all existing instances of portal_type as PH Aware
        - (hypothetical) register an event that ensures that all newly
          created instances of portal_type are simiarly marked
        """

    def unpigeonholize(portal_type):
        """Walk the catalog and unmark all instances of portal_type
        as PH Aware
        """

class IKeywordMigrator(Interface):
    """Interface for browser class supporting migration PH keyword options"""
    
    def getKeywords():
        """Returns a list of dicts of PH field names and options for all PH fields
        that are *active* and *actually have options*.
           obj looks like:
            [{'field_id': 'ph_field_1',
              'field_name': 'Audience',
              'values': ['NASCAR Dads', 'Soccer Moms'],
              },
             ]
        
           Note that this method only examines currently listed options -- it doesn't check
           the catalog for existing values that might be present.
        """
    
    def migrateKeywords(mapping=None):
        """Takes a mapping of field ids & old option values to new values.
           Does two things:
            - grabs each item that has that value assigned and remaps
            - changes the options in the PH settings from the old option
              to the new one.
              
           Mapping looks like:
           [{'field_id': 'ph_field_1',
             'mapping': ('NASCAR Dads', 'NASCAR parents',
                         'Soccer Moms', 'Soccer Parents',)
            },]
            
          Returns a status message.
        """

class IOrphans(Interface):
    """Interface for a browser class rescuing orphaned Pigeonhole metadata.
       ("Orphaned" means data tagged with values that, for whatever reason, are no longer options.)
    """
    
    def findOrphans():
        """Print a list of keywords for each Pigeonhole index (whether it's enabled or not) that don't correspond with the
        current list of options, and a count for the number of content items that are so tagged.
        """

    def saveOrphans(mapping):
        """Takes a mapping like IKeywordMigrator.migrateKeywords to remap content.  The differences are:
           - it doesn't touch the settings
           - you can map to None, which removes the tag without reassigning to anything
           """