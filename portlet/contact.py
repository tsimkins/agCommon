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

"""
Address

214 Donohoe Road, Suite E
Donohoe Center
Greensburg, PA 15601
Contact

Phone: 724-837-1402
Fax: 724-837-7613
Email: WestmorelandExt@psu.edu
Office Hours

Monday-Friday, 8:30 to 4:30
Directions

Directions to our office
"""

class IContact(IPortletDataProvider):

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    show_header = schema.Bool(
        title=_(u"Show portlet header"),
        description=_(u""),
        required=True,
        default=False)

    address = schema.Text(
        title=_(u"Physical Address"),
        description=_(u""),
        required=False)

    directions_text = schema.TextLine(
        title=_(u"Directions Text"),
        description=_(u"Linked text for directions"),
        required=False)
        
    directions_link = schema.TextLine(
        title=_(u"Directions URL"),
        description=_(u""),
        required=False)

    office_hours = schema.Text(
        title=_(u"Office Hours"),
        description=_(u""),
        required=False)
        
    phone = schema.TextLine(
        title=_(u"Phone"),
        description=_(u""),
        required=False)

    fax = schema.TextLine(
        title=_(u"Fax"),
        description=_(u""),
        required=False)
        
    email = schema.TextLine(
        title=_(u"Email"),
        description=_(u""),
        required=False)

    hide = schema.Bool(
        title=_(u"Hide portlet"),
        description=_(u"Tick this box if you want to temporarily hide "
                      "the portlet without losing your information."),
        required=True,
        default=False)

class Assignment(base.Assignment):

    implements(IContact)

    def __init__(self, header=u"", show_header=False, address=None, directions_text=None, directions_link=None, office_hours=None, phone=None, fax=None, email=None, hide=False, *args, **kwargs):
        base.Assignment.__init__(self, *args, **kwargs)
        self.header = header
        self.show_header = show_header
        self.address = address
        self.office_hours = office_hours
        self.phone = phone
        self.fax = fax
        self.email = email
        self.directions_text = directions_text
        self.directions_link = directions_link
        self.hide = hide
                
    @property
    def title(self):
        if self.header:
            return self.header
        else:
            return "Contact Portlet"


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('templates/contact.pt')

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

    @property
    def available(self):
        return not self.data.hide


class AddForm(base.AddForm):
    form_fields = form.Fields(IContact)
    form_fields['office_hours'].custom_widget = TextAreaWidget
    form_fields['office_hours'].custom_widget.height = 5
    form_fields['address'].custom_widget = TextAreaWidget
    form_fields['address'].custom_widget.height = 5
    
    label = _(u"Add Contact Portlet")
    description = _(u"This portlet displays some common contact information.")

    def create(self, data):
        return Assignment(**data)

class EditForm(base.EditForm):
    form_fields = form.Fields(IContact)
    form_fields['office_hours'].custom_widget = TextAreaWidget
    form_fields['office_hours'].custom_widget.height = 5
    form_fields['address'].custom_widget = TextAreaWidget
    form_fields['address'].custom_widget.height = 5
    label = _(u"Edit Contact Portlet")
    description = _(u"This portlet displays some common contact information.")
