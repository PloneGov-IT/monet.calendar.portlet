# -*- coding: utf-8 -*-

import datetime
import time

from Acquisition import aq_chain, aq_inner
from AccessControl import getSecurityManager

from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements
from zope import schema

from plone.memoize import ram
from plone.memoize.instance import memoize
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

    header = schema.TextLine(title=PloneMessageFactory(u'Portlet header'),
                             description=PloneMessageFactory(u'Title of the rendered portlet'),
                             required=True)

    calendar_section_path = schema.Choice(title=_(u'Calendar Section'),
                                          description=_('calendar_section_path',
                                                        u'Calendar section providing the events to be shown in the portlet'),
                                          required=True,
                                          source=SearchableTextSourceBinder({'object_provides': IMonetCalendarSection.__identifier__},
                                                                            default_query='path: '))

    days_before = schema.Int(title=_('Days before'),
                             description=_('days_before_help',
                                           u'Number of days, before the current date, to be included in the search.\n '
                                           u'Keep 0 to show only today events.'),
                             required=True,
                             min=0,
                             default=0)

    days_after = schema.Int(title=_('Days after'),
                            description=_('days_after_help',
                                           u'Number of days, after the current date, to be included in the search.\n '
                                           u'Keep 0 to show only today events.'),
                            required=True,
                            min=0,
                            default=7)

    header_as_link = schema.Bool(title=_(u"Header as link"),
                              description=_('header_as_link_help',
                                            _(u"Tick this box if you want that the portlet header will "
                                               "be a link to then related calendar.")
                                             ),
                              required=True,
                              default=True)


    omit_border = schema.Bool(title=_(u"Hide portlet"),
                              description=_('hide_portlet_help',
                                            _(u"Tick this box if you want to render the text above "
                                               "without the standard header, border or footer.")
                                             ),
                              required=True,
                              default=False)


    timeout = schema.Int(title=_(u'Cache timeout'),
                         description=_(u'Expiration time for cached results (in minutes)'),
                         required=True,
                         default=0)





class Assignment(base.Assignment):

    implements(IMonetCalendarPortlet)

    header = u''
    calendar_section_path = u'path: '
    days_before = 0
    days_after = 0
    omit_border = False
    header_as_link = True
    timeout = 0

    def __init__(self, header, calendar_section_path, days_before, days_after, omit_border, header_as_link, timeout):
        self.header = header
        self.calendar_section_path = calendar_section_path
        self.days_before = days_before
        self.days_after = days_after
        self.omit_border = omit_border
        self.header_as_link = header_as_link
        self.timeout = timeout


    @property
    def title(self):
        return 'Calendar: ' + self.header





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

    @property
    def calendar_section(self):
        root = self.portal()
        calendar = root.restrictedTraverse(self.data.calendar_section_path.lstrip('/'), default=None)
        return calendar

    @property    
    def calendar_view(self):
        calendar_view = getMultiAdapter((self.calendar_section, self.request), name=u'monetsearchevents')
        return calendar_view

    def getFromTo(self):
        """Obtain a from/to dict in a way compatible with parameters for Calendar view
        something like: {'date':date , 'date_from': date, 'date_to': date_to}
        """        
        today = datetime.date.today()
        date_from = today - datetime.timedelta(self.data.days_before)
        date_to = today + datetime.timedelta(self.data.days_after)
        if self.data.days_before==self.data.days_after==0:
            return {'date': date_from}
        return {'date': date_from, 'date_from': date_from, 'date_to': date_to}

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
        root = self.portal()
        node = root.restrictedTraverse(self.data.calendar_section_path.lstrip('/'))

        for node in aq_chain(aq_inner(node)):
            if IMonetCalendarSearchRoot.providedBy(node):
                return node
        return root


    @memoize
    def portal(self):
        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        return portal_state.portal()


    @ram.cache(_key)
    def render(self):
        return xhtml_compress(self._template())




class AddForm(base.AddForm):
    form_fields = form.Fields(IMonetCalendarPortlet)
    form_fields['calendar_section_path'].custom_widget = UberSelectionWidget

    def create(self, data):
        return Assignment(**data)



class EditForm(base.EditForm):
    form_fields = form.Fields(IMonetCalendarPortlet)
    form_fields['calendar_section_path'].custom_widget = UberSelectionWidget


