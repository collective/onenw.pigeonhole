from zope.interface import implements
from zope.component import getMultiAdapter
from Acquisition import aq_inner

from Products.Five import BrowserView
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.permissions import ModifyPortalContent

from onenw.pigeonhole.interfaces import IPHAwarenessView
from onenw.pigeonhole.interfaces import IPigeonholeAware
from onenw.pigeonhole.catalog import is_ph_configured


class PHAwarenessView(BrowserView):
    """Provides view methods for interacting with PH content"""

    implements(IPHAwarenessView)

    def shouldBePHConfigured(self):
        """Returns True iff the current user has Modify portal content permission
        and context's Pigeonhole settings are not yet configured """
        context = aq_inner(self.context)
        if not _checkPermission(ModifyPortalContent, context):
            return False
        else:
            portal_state = getMultiAdapter((context, self.request), 
                                            name=u'plone_portal_state')
            return not is_ph_configured(context, portal_state.portal())