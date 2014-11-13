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
from Products.CMFPlone.utils import normalizeString
from plone.app.layout.viewlets.common import ViewletBase

class IRelatedItems(IPortletDataProvider):

    pass

class Assignment(base.Assignment):
    implements(IRelatedItems)
        
    @property
    def title(self):
        return "Related Items"


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('templates/relateditems.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        self.anonymous = portal_state.anonymous()
        self.portal_url = portal_state.portal_url()
        self.typesToShow = portal_state.friendly_types()

        plone_tools = getMultiAdapter((context, self.request), name=u'plone_tools')
        self.catalog = plone_tools.catalog()
        
        self.wtool = getToolByName(context, 'portal_workflow')
        
        context_state = getMultiAdapter((self.context, self.request), name=u'plone_context_state')

    def render(self):
        return xhtml_compress(self._template())

    @property
    def available(self):
        return self.context.computeRelatedItems()


class AddForm(base.AddForm):
    form_fields = form.Fields(IRelatedItems)
    label = _(u"Add Related Items Portlet")
    description = _(u"This portlet displays related items.")

    def create(self, data):
        return Assignment()

class EditForm(base.EditForm):
    form_fields = form.Fields(IRelatedItems)
    label = _(u"Edit Related Items Portlet")
    description = _(u"This portlet displays related items.")
