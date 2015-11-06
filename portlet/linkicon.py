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

class ILinkIcon(IPortletDataProvider):

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    show_header = schema.Bool(
        title=_(u"Show portlet header"),
        description=_(u""),
        required=True,
        default=False)

    items = schema.Choice(title=_(u'Link/Icon Set Id'),
                       description=_(u'The id of the link/icon set in portal_actions'),
                       required=True,
                       vocabulary="agcommon.portlet.portal_actions"
                       )
                       
    hide = schema.Bool(
        title=_(u"Hide portlet"),
        description=_(u"Tick this box if you want to temporarily hide "
                      "the portlet without losing your text."),
        required=True,
        default=False)

class Assignment(base.Assignment):

    implements(ILinkIcon)

    header = ""
    show_header = ""
    items = ""
    hide = False

    def __init__(self, header=u"", show_header=u"", items=items, hide=False, *args, **kwargs):
        base.Assignment.__init__(self, *args, **kwargs)
        self.header = header
        self.show_header = show_header
        self.items = items
        self.hide = hide
                
    @property
    def title(self):
        if self.header:
            return self.header
        else:
            return "Links and Icons"


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('templates/linkicon.pt')

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
        
        self.linkIcons = context_state.actions(category=self.data.items)

    def getIconClass(self, icon):
        icon_classes = {
            'icons/blog.png' : 'fa-pencil-square',
            'icons/blogger.png' : 'fa-pencil-square',
            'icons/contact.png' : 'fa-question-circle',
            'icons/directory.png' : 'fa-group',
            'icons/facebook.png' : 'fa-facebook-square',
            'icons/feed.png' : 'fa-rss-square',
            'icons/flickr.png' : 'fa-flickr',
            'icons/google-plus.png' : 'fa-google-plus-square',
            'icons/info.png' : 'fa-info-circle',
            'icons/instagram.png' : 'fa-instagram',
            'icons/linkedin.png' : 'fa-linkedin-square',
            'icons/message.png' : 'fa-envelope-o',
            'icons/pinterest.png' : 'fa-pinterest',
            'icons/play-button.png' : 'fa-play-circle',
            'icons/podcast.png' : 'fa-headphones',
            'icons/rss.png' : 'fa-rss-square',
            'icons/twitter.png' : 'fa-twitter-square',
            'icons/typepad.png' : 'fa-pencil-square',
            'icons/vcard.png' : 'fa-pencil-square',
            'icons/youtube.png' : 'fa-youtube',
        }

        for k in icon_classes.keys():
            if icon.endswith(k):
                return 'fa fa-fw %s' % icon_classes[k]

        return 'icon'

    def getClass(self, licon):
        klass = ['title']
        icon = licon.get('icon')
        if icon:
            klass.append(self.getIconClass(icon))
        return " ".join(klass)

    def show_icon(self, licon):
        icon = licon.get('icon')
        return (icon and self.getIconClass(icon) == 'icon')

    def render(self):
        return xhtml_compress(self._template())

    @property
    def available(self):
        return self.linkIcons and not self.data.hide


class AddForm(base.AddForm):
    form_fields = form.Fields(ILinkIcon)
    label = _(u"Add Icon and Link Portlet")
    description = _(u"This portlet displays icons and links configured in portal_actions.")

    def create(self, data):
        return Assignment(**data)

class EditForm(base.EditForm):
    form_fields = form.Fields(ILinkIcon)
    label = _(u"Edit Icon and Link Portlet")
    description = _(u"This portlet displays icons and links configured in portal_actions.")
