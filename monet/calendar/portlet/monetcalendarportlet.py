
import datetime
import time

from Acquisition import aq_chain, aq_inner
from AccessControl import getSecurityManager

from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements
from zope import schema

from plone.memoize import ram
from plone.memoize.compress import xhtml_compress
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget
from plone.app.portlets.portlets import base
from plone.app.vocabularies.catalog import SearchableTextSourceBinder

from monet.calendar.extensions.interfaces import IMonetCalendarSection, IMonetCalendarSearchRoot

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory
from Products.CMFCore.utils import getToolByName

from monet.calendar.event.interfaces import IMonetEvent
from monet.calendar.portlet import MonetCalendarPortletMessageFactory as _
from monet.calendar.extensions.browser.monetsearchevents import daterange


class IMonetCalendarPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    header = schema.TextLine(title=PloneMessageFactory(u"Portlet header"),
                             description=PloneMessageFactory(u"Title of the rendered portlet"),
                             required=True)

    calendar_section_path = schema.Choice(title=_(u"Calendar Section"),
                                          description=_(u"Object providing the events to show in the portlet"),
                                          required=True,
                                          source=SearchableTextSourceBinder({'object_provides': IMonetCalendarSection.__identifier__},
                                                                            default_query='path: '))

    days_before = schema.Int(title=_('Nr. giorni prima'),
                             required=True,
                             min=0,
                             default=0)

    days_after = schema.Int(title=_('Nr. giorni dopo'),
                            required=True,
                            min=0,
                            default=7)

    timeout = schema.Int(title=_(u'Cache timeout'),
                         description=_(u'Expiration time for cached results (in minutes)'),
                         required=True,
                         default=0)






class Assignment(base.Assignment):

    implements(IMonetCalendarPortlet)


    def __init__(self, header, calendar_section_path, days_before, days_after, timeout):
        self.header = header
        self.calendar_section_path = calendar_section_path
        self.days_before = days_before
        self.days_after = days_after
        self.timeout = timeout


    @property
    def title(self):
        return self.header







def _key(method, rend):
    if not rend.data.timeout:
        return time.time()

    key = u':'.join(unicode(x) for x in
                    [
                        time.time() // (60 * rend.data.timeout),
                        rend.data.calendar_section_path,
                        rend.data.days_before,
                        rend.data.days_after,
                        rend.data.timeout,
                        getSecurityManager().getUser().getId()
                    ]).encode('utf-8')
    return key





class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('monetcalendarportlet.pt')


    def events(self):
        catalog = getToolByName(self, 'portal_catalog')
        query = {
                'object_provides': IMonetEvent.__identifier__,
                'path': '/'.join(self.search_root().getPhysicalPath()),
                }

        today = datetime.date.today()

        selected_dates = set(daterange(start_date=today - datetime.timedelta(self.data.days_before),
                                       end_date=today + datetime.timedelta(self.data.days_after)))

        ret = set()
        for brain in catalog(**query):
            if set(brain.getDates).intersection(selected_dates):
                ret.add(brain)

        return sorted(ret, key=lambda x: min(x.getDates))


    def search_root(self):
        """
        walks up hirarchy looking for 
        """
        root = self.portal()
        node = root.restrictedTraverse(self.data.calendar_section_path.lstrip('/'))

        for node in aq_chain(aq_inner(node)):
            if IMonetCalendarSearchRoot.providedBy(node):
                return node
        return root


    def portal(self):
        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        return portal_state.portal()


    @ram.cache(_key)
    def render(self):
        return xhtml_compress(self._template())







class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IMonetCalendarPortlet)
    form_fields['calendar_section_path'].custom_widget = UberSelectionWidget

    def create(self, data):
        return Assignment(**data)



class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IMonetCalendarPortlet)
    form_fields['calendar_section_path'].custom_widget = UberSelectionWidget


