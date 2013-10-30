from zope.component import getUtility, getMultiAdapter
from zope.app.component.hooks import setHooks, setSite

from plone.portlets.interfaces import IPortletType
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletDataProvider
from plone.portlets.interfaces import IPortletRenderer
from plone.app.portlets.storage import PortletAssignmentMapping
 
from onenw.pigeonhole.browser.configlet import PigeonholeCPAdapter
from onenw.pigeonhole.portlets import relatednews
from onenw.pigeonhole.portlets import relatedevents
from onenw.pigeonhole.portlets import relatedcontent
from onenw.pigeonhole.portlets import relateditem
from onenw.pigeonhole.tests.base import FunctionalTestCase

from DateTime.DateTime import DateTime

class TestPortletSetup(FunctionalTestCase):

    def afterSetUp(self):
        setHooks()
        setSite(self.portal)
        self.setRoles(('Manager',))
        self.portlets = ({'module': relatednews, 'name': 'RelatedNews',},
                         {'module': relatedevents, 'name': 'RelatedEvents',},
                         {'module': relatedcontent, 'name': 'RelatedContent',},
                         {'module': relateditem, 'name': 'RelatedItem',},
                         )

    def testPortletTypeRegistered(self):
        for name in ["onenw.pigeonhole.%s" % n['name'] for n in self.portlets]:
            portlet = getUtility(IPortletType, name=name)
            self.assertEquals(portlet.addview, name)
 
    def testInterfaces(self):
        for module in [p['module'] for p in self.portlets]:
            portlet = module.Assignment()
            self.failUnless(IPortletAssignment.providedBy(portlet))
            self.failUnless(IPortletDataProvider.providedBy(portlet.data))

    def testInvokeAddview(self):
        for p in self.portlets:
            name = "onenw.pigeonhole.%s" % p['name']
            portlet = getUtility(IPortletType, name=name)
            mapping = self.portal.restrictedTraverse('++contextportlets++plone.leftcolumn')
            for m in mapping.keys():
                del mapping[m]
            addview = mapping.restrictedTraverse('+/' + portlet.addview)

            addview.createAndAdd(data={})

            self.assertEquals(len(mapping), 1)
            self.failUnless(isinstance(mapping.values()[0], p['module'].Assignment))

    def testInvokeEditView(self):
        for module in [p['module'] for p in self.portlets]:
            mapping = PortletAssignmentMapping()
            request = self.folder.REQUEST

            mapping['foo'] = module.Assignment()
            editview = getMultiAdapter((mapping['foo'], request), name='edit')
            self.failUnless(isinstance(editview, module.EditForm))

    def testRenderer(self):
        context = self.folder
        request = self.folder.REQUEST
        for module in [p['module'] for p in self.portlets]:
            view = self.folder.restrictedTraverse('@@plone')
            manager = getUtility(IPortletManager, name='plone.leftcolumn', context=self.portal)
            assignment = module.Assignment()

            renderer = getMultiAdapter((context, request, view, manager, assignment), IPortletRenderer)
            self.failUnless(isinstance(renderer, module.Renderer))

class TestPortletFunctionality(FunctionalTestCase):

    def afterSetUp(self):

        self.setRoles(('Manager',))
        # configure PH
        ctl_panel = PigeonholeCPAdapter(self.portal)
        ctl_panel.set_ph_field_values_1(['Fishermen', 'Fisherwomen', 'Fisherbabies'])
        ctl_panel.set_ph_field_values_2(['Fish', 'Forests',])

    def createContent(self, type_name, prefix):
        # (unless your computer is REALLY slow, this should be in the future for the lifespan of
        # the running of the tests...)
        tomorrow = DateTime()+1

        # Create and publish 4 items
        # First 3 will share Audience (ph_field_1).
        # First 2 will share Program Area (ph_field_2).
        for x in range(1,5):
            id = '%s%s' % (prefix, x)
            self.portal.invokeFactory(type_name, id)
            if type_name == 'Event':
                e = getattr(self.portal, id).setEndDate(tomorrow)
            self.portal.portal_workflow.doActionFor(getattr(self.portal, id), 'publish')
            # set Effective Date so that these guys are spaced out a little
            # we'll back date them based on their number
            ed = DateTime() - (5-x)
            getattr(self.portal, id).setEffectiveDate(ed)
            
        for x in range(1,4):
            id = '%s%s' % (prefix, x)
            obj = getattr(self.portal, id)
            obj.Schema().get('ph_field_1').getMutator(obj)(('Fishermen',))
            obj.reindexObject()

        for x in range(1,3):
            id = '%s%s' % (prefix, x)
            obj = getattr(self.portal, id)
            obj.Schema().get('ph_field_2').getMutator(obj)(('Fish',))
            obj.reindexObject()

    def renderer(self, context=None, request=None, view=None, manager=None, assignment=None):
        context = context or self.folder
        request = request or self.folder.REQUEST
        view = view or self.folder.restrictedTraverse('@@plone')
        manager = manager or getUtility(IPortletManager, name='plone.leftcolumn', context=self.portal)
        return getMultiAdapter((context, request, view, manager, assignment), IPortletRenderer)

    def test_related_news_items(self):
        self.createContent('News Item', 'n')

        # when using just Audience (ph_field_1) for determining relatedness, you should see
        # two results when looking at n1
        r = self.renderer(assignment=relatednews.Assignment(which_fields_relate=('ph_field_1',)),
                          context=self.portal.n1)
        news = r.getNews()
        self.assertEquals(2, len(news),
                          "Expecting 2 items; got %s." % len(news))

        # the results should be sorted from most recently published on down
        self.assertEquals(['n3','n2'], [n.id for n in news])

        # when using both ph_field_1 and ph_field_2, we should just get 1 when looking at n1
        r = self.renderer(assignment=relatednews.Assignment(which_fields_relate=('ph_field_1','ph_field_2')),
                          context=self.portal.n1)
        self.assertEquals(1, len(r.getNews()),
                          "Expecting 1 items; got %s." % len(r.getNews()))

        # when using both ph_field_1 and ph_field_2, we should just get none when looking at n3
        r = self.renderer(assignment=relatednews.Assignment(which_fields_relate=('ph_field_1','ph_field_2')),
                          context=self.portal.n3)
        self.assertEquals(0, len(r.getNews()),
                          "Expecting no items; got %s." % len(r.getNews()))

    def test_related_events(self):
        self.createContent('Event', 'e')

        # when using just Audience (ph_field_1) for determining relatedness, you should see
        # two results when looking at e1
        r = self.renderer(assignment=relatedevents.Assignment(which_fields_relate=('ph_field_1',)),
                          context=self.portal.e1)
        self.assertEquals(2, len(r.getEvents()),
                          "Expecting 2 items; got %s." % len(r.getEvents()))

        # when using both ph_field_1 and ph_field_2, we should just get 1 when looking at e1
        r = self.renderer(assignment=relatedevents.Assignment(which_fields_relate=('ph_field_1','ph_field_2')),
                          context=self.portal.e1)
        self.assertEquals(1, len(r.getEvents()),
                          "Expecting 1 items; got %s." % len(r.getEvents()))

        # when using both ph_field_1 and ph_field_2, we should just get none when looking at e3
        r = self.renderer(assignment=relatedevents.Assignment(which_fields_relate=('ph_field_1','ph_field_2')),
                          context=self.portal.e3)
        self.assertEquals(0, len(r.getEvents()),
                          "Expecting no items; got %s." % len(r.getEvents()))

    def test_related_content(self):
        self.createContent('News Item', 'n')
        self.createContent('Document', 'd')
        # when using just Audience (ph_field_1) for determining relatedness, you should see
        # two results when looking at d1
        r = self.renderer(assignment=relatedcontent.Assignment(which_fields_relate=('ph_field_1',),
                                                               which_content_types=('Document',),),
                          context=self.portal.d1)
        self.assertEquals(2, len(r.getRelatedContent()),
                          "Expecting 2 items; got %s." % len(r.getRelatedContent()))

        # when using both ph_field_1 and ph_field_2 for docs AND newsitems, we should now get 3
        # when looking at d1
        r = self.renderer(assignment=relatedcontent.Assignment(number_of_items=8,
                                                               which_fields_relate=('ph_field_1','ph_field_2'),
                                                               which_content_types=('Document', 'News Item'),),
                          context=self.portal.d1)
        self.assertEquals(3, len(r.getRelatedContent()),
                          "Expecting 3 items; got %s." % len(r.getRelatedContent()))

        # when using both ph_field_1 and ph_field_2, we should just get none when looking at n3
        r = self.renderer(assignment=relatedcontent.Assignment(which_fields_relate=('ph_field_1','ph_field_2'),
                                                              which_content_types=('Document', 'News Item'),),
                          context=self.portal.n3)
        self.assertEquals(0, len(r.getRelatedContent()),
                          "Expecting no items; got %s." % len(r.getRelatedContent()))

    def test_unrelated_content(self):
        """Prove that if 'relatable' field is False then it won't show in a portlet."""
        self.createContent('Document', 'd')
        self.createContent('News Item', 'n')
        self.createContent('Event', 'e')
        
        # mark them ALL unrelated
        for x in range(1,5):
            for prefix in ('e','d','n'):
                id = '%s%s' % (prefix, x)
                obj = getattr(self.portal, id)
                obj.Schema().get('relatable').getMutator(obj)(False)
                obj.reindexObject()

        # we're never expecting results
        # related content
        r = self.renderer(assignment=relatedcontent.Assignment(which_fields_relate=('ph_field_1',),
                                                               which_content_types=('Document',
                                                                                    'News Item',
                                                                                    'Event',
                                                                                    ),
                                                                ),
                          context=self.portal.d1)
        self.assertEquals(0, len(r.getRelatedContent()),
                          "Expecting no items; got %s." % len(r.getRelatedContent()))

        # related news
        r = self.renderer(assignment=relatednews.Assignment(which_fields_relate=('ph_field_1',)),
                          context=self.portal.d1)
        self.assertEquals(0, len(r.getNews()),
                          "Expecting no items; got %s." % len(r.getNews()))

        # related events
        r = self.renderer(assignment=relatedevents.Assignment(which_fields_relate=('ph_field_1',),),
                          context=self.portal.n3)
        self.assertEquals(0, len(r.getEvents()),
                          "Expecting no items; got %s." % len(r.getEvents()))

    def test_portletsFailNicelyinPHUnawareContexts(self):
        """Bug where portlets bonk when in, say, OOTB a folder"""
        r = self.renderer(assignment=relatednews.Assignment(which_fields_relate=('ph_field_1',)),
                          context=self.portal)
        r.getNews()
        r = self.renderer(assignment=relatedevents.Assignment(which_fields_relate=('ph_field_1',)),
                          context=self.portal)
        r.getEvents()
        r = self.renderer(assignment=relatedcontent.Assignment(number_of_items=2,
                                                               which_fields_relate=('ph_field_1',),
                                                               which_content_types=('Document',),),
                          context=self.portal)
        r.getRelatedContent()
    
    def test_related_item(self):
        self.createContent('Document', 'd')
        r = self.renderer(assignment=relateditem.Assignment(which_fields_relate=('ph_field_1',),
                                                            which_content_types=('Document',),
                                                            portlet_title='My Portlet',
                                                            tie_breaker=relateditem.TIEBREAKER_DATE,
                                                            ),
                          context=self.portal.d1)
        # test getPortletHeader w/o override
        self.assertEquals('My Portlet',r.getPortletHeader())
        # test that we're getting the most recently published.  Random option is a little tricky to test...
        self.assertEquals('d3',r.getRelatedItem().getId())

        r = self.renderer(assignment=relateditem.Assignment(which_fields_relate=('ph_field_1',),
                                                            which_content_types=('Document',),
                                                            header_override=True,
                                                            ),
                          context=self.portal.d1)
        # test getPortletHeader w/ override
        self.assertEquals('',r.getPortletHeader())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortletSetup))
    suite.addTest(makeSuite(TestPortletFunctionality))
    return suite
