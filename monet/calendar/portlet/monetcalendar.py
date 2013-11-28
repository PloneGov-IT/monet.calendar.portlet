# -*- coding: utf-8 -*-

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from monet.calendar.extensions.browser.usefulforsearch import UsefulForSearchEvents
from plone.app.portlets.portlets.calendar import Renderer as BaseRenderer
from plone.app.portlets.portlets.calendar import _render_cachekey
from plone.memoize import ram
from plone.memoize.compress import xhtml_compress


class Renderer(BaseRenderer, UsefulForSearchEvents):
    """A new calendar portlet, with no day highlight"""
    _template = ViewPageTemplateFile('monetcalendar.pt')
    
    def getDateString(self,daynumber):
        return '%s-%s-%s' % (self.year, self.month, daynumber)

    @ram.cache(_render_cachekey)
    def render(self):
        return xhtml_compress(self._template())

#    def getEventsForCalendar(self):
#        return BaseRenderer.getEventsForCalendar(self)
