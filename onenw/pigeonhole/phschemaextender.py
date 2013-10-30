from zope.interface import implements
from zope.component import adapts
from archetypes.schemaextender.interfaces import ISchemaExtender

from Products.Archetypes import atapi

from onenw.pigeonhole.interfaces import IPigeonholeAware
from onenw.pigeonhole.fields import TagsField
from onenw.pigeonhole.fields import CheckboxField
from onenw.pigeonhole.fields import PHMultiSelectionWidget

class PHSchemaExtender(object):
    implements(ISchemaExtender)
    adapts(IPigeonholeAware)
    
    _fields = [CheckboxField('relatable',
                             schemata='categorization',
                             widget=atapi.BooleanWidget(
                                        label='Should this page be a candidate to show up in other pages\' "related" portlets?',
                                        description="""Uncheck this box if this page is a section homepage, or any other content that you wouldn't want to see in as "related" content.""",
                                        ),
                             default=True,
                            ),
                ]
    
    # Pigeonhole has *4* fields, for the time being
    for x in range(1,5):
        _fields.append(TagsField('ph_field_%s' % x,
                                field_num=x, # this is a TagsField special field
                                schemata='categorization',
                                enforceVocabulary=True,
                                widget=PHMultiSelectionWidget(
                                    field_num=x, # likewise, a PHMultiSelectionWidget special field
                                    label="PH Field %s" % x,
                                    description=" ",
                                    format="checkbox",
                                    visible = { 'edit' :'dynamic', # 'dynamic' is a custom value
                                                'view' : 'invisible' },
                                    ),
                                ),
                        )
    
    def __init__(self, context):
        self.context = context
    
    def getFields(self):
        return self._fields


