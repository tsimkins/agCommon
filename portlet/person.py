from zope import schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements
from plone.memoize.compress import xhtml_compress

from plone.app.portlets.portlets import base
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.cache import render_cachekey

from Acquisition import aq_acquire, aq_inner
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

class IPerson(IPortletDataProvider):

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    show_header = schema.Bool(
        title=_(u"Show portlet header"),
        description=_(u""),
        required=True,
        default=False)

    people = schema.TextLine(
        title=_(u"Person id(s)"),
        description=_(u"The id(s) of the person to show.  If blank, defaults to the author for News Items.  Set a ZMI 'lines' property of 'person_portlet_types' for additional portlet types."),
        required=False)

    show_address = schema.Bool(
        title=_(u"Show office address"),
        description=_(u""),
        required=True,
        default=False)

    show_image = schema.Bool(
        title=_(u"Show person image"),
        description=_(u""),
        required=True,
        default=False)

    image_size = schema.Choice(
            title=_(u"heading_image_size",
                default=u"Image Size"),
            description=_(u"description_image_size",
                default=u""),
            default='small',
            required=True,
            vocabulary=SimpleVocabulary.fromValues([u'small', u'large']),
        )

    hide = schema.Bool(
        title=_(u"Hide portlet"),
        description=_(u"Tick this box if you want to temporarily hide "
                      "the portlet without losing your text."),
        required=True,
        default=False)

class Assignment(base.Assignment):

    implements(IPerson)

    header = ""
    show_header = False
    people = ""
    show_address = False
    show_image = False
    image_size = u'small'
    hide = False

    def __init__(self, header=u"", show_header=show_header, people=people, 
                 show_address=show_address, show_image=show_image, 
                 image_size=image_size, hide=hide, *args, **kwargs):
        base.Assignment.__init__(self, *args, **kwargs)
        self.header = header
        self.show_header = show_header
        self.people = people
        self.show_address = show_address
        self.show_image = show_image
        self.hide = hide
        self.image_size = image_size
                
    @property
    def title(self):
        if self.header:
            return self.header
        else:
            return "Person Portlet"


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('templates/person.pt')

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

        try:
            person_portlet_types = aq_acquire(self.context, 'person_portlet_types')
        except AttributeError:
            person_portlet_types = ['News Item']
            

        if self.data.people:
            peopleList = self.data.people.replace(' ', '').split(",")
        elif self.context.portal_type in person_portlet_types:
            peopleList = list(self.context.listCreators())
        else:
            peopleList = None
        
        self.people = []
        
        if peopleList:
            catalog = getToolByName(context, 'portal_catalog')
            search_results = catalog.searchResults({'portal_type' : 'FSDPerson', 'id' : peopleList })
            
            for id in peopleList:
                for r in search_results:
                    if r.id == id:
                        self.people.append(r)
      
    def render(self):
        return xhtml_compress(self._template())

    @property
    def available(self):
        return not self.data.hide and self.people

    @property
    def image_size(self):
        if self.data.image_size:
            return self.data.image_size
        else:
            return 'small'

    @property
    def image_scale(self):
        return {
                'large' : 'normal',
                'small' : 'thumb'
        }.get(self.image_size, 'thumb')

class AddForm(base.AddForm):
    form_fields = form.Fields(IPerson)
    label = _(u"Add Person Portlet")
    description = _(u"This portlet displays information for FSDPerson objects.")

    def create(self, data):
        return Assignment(**data)

class EditForm(base.EditForm):
    form_fields = form.Fields(IPerson)
    label = _(u"Edit Person Portlet")
    description = _(u"This portlet displays information for FSDPerson objects.")
