from zope import schema
from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements
from plone.memoize.compress import xhtml_compress

from plone.app.portlets.portlets import base
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.cache import render_cachekey

from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from zope.app.form.browser import TextAreaWidget

class ITwitter(IPortletDataProvider):

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    show_header = schema.Bool(
        title=_(u"Show portlet header"),
        description=_(u""),
        required=True,
        default=False)

    twitter_url = schema.TextLine(
        title=_(u"Twitter URL"),
        description=_(u"URL of Twitter feed"),
        required=True)
        
    widget_id = schema.TextLine(
        title=_(u"Widget ID"),
        description=_(u"From https://twitter.com/settings/widgets"),
        required=True)

    widget_height = schema.Int(
        title=_(u"Widget Height"),
        description=_(u""),
        required=True,
        default=600)

class Assignment(base.Assignment):

    implements(ITwitter)

    def __init__(self, header=u"", show_header=False, twitter_url=None, widget_id=None, widget_height=600, *args, **kwargs):
        base.Assignment.__init__(self, *args, **kwargs)
        self.header = header
        self.show_header = show_header
        self.twitter_url = twitter_url
        self.widget_id = widget_id
        self.widget_height = widget_height                
    @property
    def title(self):
        if self.header:
            return self.header
        else:
            return "Twitter Portlet"


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('templates/twitter.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        self.anonymous = portal_state.anonymous()
        self.portal_url = portal_state.portal_url()
        self.typesToShow = portal_state.friendly_types()

        plone_tools = getMultiAdapter((context, self.request), name=u'plone_tools')
        self.catalog = plone_tools.catalog()
        
        context_state = getMultiAdapter((self.context, self.request), name=u'plone_context_state')
        
        catalog = getToolByName(context, 'portal_catalog')
        
        
      
    def render(self):
        return xhtml_compress(self._template())


class AddForm(base.AddForm):
    form_fields = form.Fields(ITwitter)
   
    label = _(u"Add Twitter Portlet")
    description = _(u"This portlet displays a Twitter feed.")

    def create(self, data):
        return Assignment(**data)

class EditForm(base.EditForm):
    form_fields = form.Fields(ITwitter)
    label = _(u"Edit Twitter Portlet")
    description = _(u"This portlet displays a Twitter feed.")
