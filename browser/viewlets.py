from AccessControl import getSecurityManager
from Acquisition import aq_inner, aq_base, aq_chain
from DateTime import DateTime
from Products.CMFCore.Expression import Expression, getExprContext
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from Products.ContentWellPortlets.browser.viewlets import ContentWellPortletsViewlet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile, ZopeTwoPageTemplateFile
from Products.agCommon import getContextConfig, scrubPhone
from Products.agCommon.browser.views import FolderView, PublicationView
from agsci.subsite.content.interfaces import ISection, ISubsite
from cgi import escape
from collective.contentleadimage.browser.viewlets import LeadImageViewlet
from hashlib import md5
from plone.app.discussion.browser.comments import CommentsViewlet
from plone.app.layout.nextprevious.view import NextPreviousView
from plone.app.layout.viewlets.common import SearchBoxViewlet, TableOfContentsViewlet, ViewletBase
from plone.app.layout.viewlets.content import ContentRelatedItems as ContentRelatedItemsBase
from plone.memoize.instance import memoize
from plone.portlets.interfaces import ILocalPortletAssignable, IPortletManager
from urllib import urlencode
from zope.component import getMultiAdapter, provideAdapter, ComponentLookupError, getUtility
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import Interface, implements
from zope.viewlet.interfaces import IViewlet
import re
 
try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

try:
    from agsci.ExtensionExtender.counties import data as county_data
except ImportError:
    county_data = {}


from zope.publisher.interfaces.browser import IBrowserView,IDefaultBrowserLayer

from Products.Five.browser import BrowserView

class AgCommonViewlet(ViewletBase):

    def update(self):
        pass

    @property
    def portal_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_portal_state')

    @property
    def context_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_context_state')

    @property
    def anonymous(self):
        return self.portal_state.anonymous()

    @property
    def homepage_h1(self):
        return getContextConfig(self.context, 'homepage_h1')

    @property
    def homepage_h2(self):
        return getContextConfig(self.context, 'homepage_h2')
    @property
    def hide_breadcrumbs(self):
        # Determine if we should hide breadcrumbs

        # If we have a homepage overlay set
        if self.homepage_h1 or self.homepage_h2:
            return True

        # If we have a slider configured on a homepage
        if getattr(self.context, 'portal_type') in ['HomePage'] and self.context.getReferences(relationship = 'IsHomePageSliderFor'):
            return True
    
        return getContextConfig(self.context, 'hide_breadcrumbs', False)

    def isLayout(self, views=[]):
        try:
            layout = self.context.getLayout()
        except:
            layout = None
            
        if layout in views:
            return True
        else:
            for v in views:
                if v in self.context.absolute_url():
                    return True
    
            return False

    @property
    def isHomePage(self):
        return self.isLayout(views=['document_homepage_view', 'document_subsite_view', 'portlet_homepage_view', 'panorama_homepage_view', 'tile_homepage_view'])

    @property
    def showLegacyHomePagePortlets(self):
        return (self.isHomePage and self.portlet_format == 'standard')

    @property
    def showAboveContentPortlets(self):
        return (self.isHomePage and self.portlet_format == 'tile') or not self.isHomePage

    @property
    def showHomepageText(self):
        return getattr(self.context, 'show_homepage_text', True)

    @property    
    def isFolderFullView(self):
        folder_views = ['folder_full_view_item', 'folder_full_view', 'newsletter_view', 'newsletter_email', 'newsletter_print'] 
        parent = self.context.getParentNode()
        try:
            default_page = parent.getDefaultPage()
        except AttributeError:
            default_page = None
        
        if default_page and default_page in parent.objectIds():
            try:
                layout = parent[default_page].getLayout()
            except:
                layout = None
        else:
            try:
                layout = parent.getLayout()
            except:
                layout = None
    
        if layout in folder_views:
            return True
        else:
            for v in folder_views:
                if v in self.context.absolute_url():
                    return True
    
            return False
    
    @property
    def showTwoColumn(self):
    
        try:
            layout = self.context.getLayout()
        except:
            layout = None
            
        if layout in ['factsheet_view']:
            return True
        else:
            return False

    @property
    def image_format(self):
        return getattr(self.context, 'homepage_image_format', 'standard')

    @property
    def portlet_format(self):
        return getattr(self.context, 'homepage_portlet_format', 'standard')

class PortletViewlet(AgCommonViewlet):

    def can_manage_portlets(self):

        if not ILocalPortletAssignable.providedBy(self.context):
            return False
        mtool = getToolByName(self.context, 'portal_membership')
        return mtool.checkPermission("Portlets: Manage portlets", self.context)


class TopNavigationViewlet(AgCommonViewlet):   
    index = ViewPageTemplateFile('templates/topnavigation.pt')

    def getClassName(self, saction):
        klass = []
        if saction.get('url') == self.container_url():
            klass.append('alternate')
        elif saction.get('alternate_color'):
            klass.append('alternate')
        return " ".join(klass)

    @memoize
    def container_url(self):
        # URL that contains the section
        container_url = None
        topnavigation = self.topnavigation()

        matches = []

        for t in self.topnavigation():
            portal_url = self.context.portal_url()
            context_url = self.context.absolute_url()
            menu_url = t.get('url')
            urls = [menu_url]
            
            # Handle additional URLs configured in portal_actions
            if t.get('additional_urls'):
                econtext = getExprContext(self.context)
                for u in t.get('additional_urls'):
                    try:
                        url_expr = Expression(u)
                        urls.append(url_expr.__call__(econtext))
                    except:
                        pass
                    
            for t_url in urls:
                # Remove trailing / to normalize
                if t_url.endswith("/"):
                    t_url = t_url[0:-1]
                if portal_url.endswith("/"):
                    portal_url = portal_url[0:-1]
                if context_url.endswith("/"):
                    context_url = context_url[0:-1]
                    
                if portal_url != t_url and context_url.startswith(t_url):
                    matches.append(menu_url) # Remove trailing slash

        if matches:
            container_url = sorted(matches, key=lambda x:len(x), reverse=True)[0]

        return container_url

    @memoize
    def topnavigation(self):
        topMenu = getContextConfig(self.context, 'top-menu', 'topnavigation')
        return self.context_state.actions(category=topMenu)

    def update(self):
        pass


class RightColumnViewlet(PortletViewlet):   
    index = ViewPageTemplateFile('templates/rightcolumn.pt')


class CenterColumnViewlet(PortletViewlet):   
    index = ViewPageTemplateFile('templates/centercolumn.pt')


class HomepageTextViewlet(AgCommonViewlet):   
    index = ViewPageTemplateFile('templates/homepagetext.pt')


class HomepageImageViewlet(AgCommonViewlet):   
    index = ViewPageTemplateFile('templates/homepageimage.pt')

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def slider_target(self):
        target = self.context.getReferences(relationship = 'IsHomePageSliderFor')
        if target:
            return target[0]
        return None

    def folderContents(self):
        target = self.slider_target
        if target and target.portal_type == 'Topic':
            item_count = target.itemCount

            if not item_count:
                item_count = 7

            # Explicitly exclude expired items

            query = target.buildQuery()
            
            query['expires'] = {'query' : DateTime(), 'range' : 'min'}

            results = self.portal_catalog.searchResults(query)

            return results[:item_count]

        return []

    @property
    def slider_has_contents(self):
        return (len(self.folderContents()) > 0)
        
class FlexsliderViewlet(HomepageImageViewlet, FolderView):   
    index = ViewPageTemplateFile('templates/flexslider.pt')
    
    def slider_title(self):
        target = self.slider_target
        if target and target.portal_type == 'Topic':
            return target.Title()

    def slider_random(self):
        if getattr(self.context, 'slider_random', False):
            return "random"
        else:
            return "sequential"


class PublicationCodeViewlet(AgCommonViewlet, PublicationView):

    def show_viewlet(self):
        return (self.publication_code or self.publication_series)

class AddThisViewlet(PublicationCodeViewlet):   
    index = ViewPageTemplateFile('templates/addthis.pt')

    def update(self):
        pass

    @property
    def isSyndicationAllowed(self):
        syntool = getToolByName(self.context, 'portal_syndication')
        return syntool.isSyndicationAllowed(self.context)
        
    @property
    def isPerson(self):
        portal_type = getattr(self.context, 'portal_type', None)
        return (portal_type == 'FSDPerson')

    @property
    def hide_addthis(self):

        ptool = getToolByName(self.context, "portal_properties")

        # Hide if not enabled in agCommon properties
        if not ptool.agcommon_properties.enable_addthis:
            return True

        # If in folder_full_view_item, hide it on the individual items.
        elif self.isFolderFullView:
            return True

        else:
            return getContextConfig(self.context, 'hide_addthis', False)

    @property
    def show_addthis(self):
        if self.hide_addthis:
            return False

        if not self.anonymous:
            return False

        if self.isHomePage:
            if self.showHomepageText:
                # Only show the viewlet if we're called from inside the 
                # homepage text viewlet.  We're discovering this by the 
                # lack of a manager
                return not (self.manager)
            else:
                return False
        
        return True

    @property
    def translationLanguages(self):
        return dict ([
                        ('fr', u'Fran&ccedil;ais'),
                        ('es', u'Espa&ntilde;ol'), 
                    ]
                )

    def showTranslationWidget(self):
        return getContextConfig(self.context, 'provide_translation_widget', False)

    def getTranslationLanguages(self):
        return self.translationLanguages.keys()

    def getTranslationUrl(self, c):
        data = { 'u' : self.context.absolute_url(), 'sl' : 'en', 'tl' : c }
        return "http://translate.google.com/translate?%s" % urlencode(data)

    def getTranslationLabel(self, c):
        return self.translationLanguages.get(c, '')

        
class FBLikeViewlet(AgCommonViewlet):   
    index = ViewPageTemplateFile('templates/fblike.pt')

    def update(self):
        self.likeurl = escape(safe_unicode(self.context.absolute_url()))

        
class FooterViewlet(AgCommonViewlet):   
    index = ViewPageTemplateFile('templates/footer.pt')

    def update(self):

        # Get copyright info
        ptool = getToolByName(self.context, "portal_properties")

        self.footer_copyright = ptool.agcommon_properties.footer_copyright
        self.footer_copyright_link = ptool.agcommon_properties.footer_copyright_link

        try:
            self.footer_copyright_2 = ptool.agcommon_properties.footer_copyright_2
            self.footer_copyright_link_2 = ptool.agcommon_properties.footer_copyright_link_2
        except AttributeError:  
            self.footer_copyright_2 = None
            self.footer_copyright_link_2 = None
      

        footerlinks = getContextConfig(self.context, 'footerlinks', 'footerlinks')

        self.footerlinks = self.context_state.actions(category=footerlinks)
        
class CustomTitleViewlet(AgCommonViewlet):

    def update(self):
        try:
            self.page_title = self.view.page_title
        except AttributeError:
            self.page_title = self.context_state.object_title
        
        self.portal_title = self.portal_state.portal_title()

        self.site_title = getContextConfig(self.context, 'site_title', self.portal_title)
        
        if self.site_title == self.portal_title:
            self.org_title = "Penn State University"
        else:
            self.org_title = "Penn State College of Ag Sciences"

        self.org_title = getContextConfig(self.context, 'org_title', self.org_title)
        
class TitleViewlet(CustomTitleViewlet):
    
    def index(self):
    
        portal_title = escape(safe_unicode(self.site_title))
        page_title = escape(safe_unicode(self.page_title()))
        org_title = escape(safe_unicode(self.org_title))

        if page_title == portal_title == org_title:
            return u"<title>%s</title>" % (org_title)
        elif org_title == portal_title:
            return u"<title>%s &mdash; %s</title>" % (page_title, org_title)
        elif page_title == portal_title:
            return u"<title>%s &mdash; %s</title>" % (portal_title, org_title)
        elif not org_title or org_title.lower() == 'none':
            return u"<title>%s &mdash; %s</title>" % (
                page_title,
                portal_title)
        else:
            return u"<title>%s &mdash; %s &mdash; %s</title>" % (
                page_title,
                portal_title,
                org_title)


class FBMetadataViewlet(CustomTitleViewlet):
    
    index = ViewPageTemplateFile('templates/fbmetadata.pt')

    def getImageInfo(self, context=None):
        image_url = image_mime_type = ''
        
        if not context:
            context = self.context
        
        try:
            leadImage_field = context.getField('leadImage', None)
            image_field = context.getField('image', None)
        except AttributeError:
            leadImage_field = None
            image_field = None
            
        if leadImage_field and leadImage_field.get_size(context) > 0:
            image_url = "%s/leadImage" % context.absolute_url()
            image_mime_type = leadImage_field.getContentType(context)
        elif image_field and image_field.get_size(context) > 0:

            sizes = {}

            if hasattr(image_field, 'sizes') and image_field.sizes:
                sizes = image_field.sizes

            image_url = "%s/image" % context.absolute_url()

            image_mime_type = image_field.getContentType(context)

        return (image_url, image_mime_type)
        

    def isDefaultPage(self):
        # Determine if we're the default page
        
        parent = self.context.getParentNode()
        
        try:
            parent_default_page_id = parent.getDefaultPage()
        except AttributeError:
            parent_default_page_id = ''

        return (self.context.id == parent_default_page_id)
        
    def update(self):
    
        super(FBMetadataViewlet, self).update()
    
        portal_title = safe_unicode(self.site_title)
        page_title = safe_unicode(self.page_title())
        org_title = safe_unicode(self.org_title)
        
        if not org_title or org_title.lower() == 'none':
            self.fb_title = page_title
            self.fb_site_name = portal_title
        elif page_title == portal_title:
            self.fb_title = portal_title
            self.fb_site_name = org_title
        else:
            self.fb_title = page_title
            self.fb_site_name = "%s (%s)" % (portal_title, org_title)
                
        self.showFBMetadata = True

        self.fb_url = self.context.absolute_url()
        
        try:
            # Remove this page's id from the URL if it's a default page.
            if self.isDefaultPage() and self.context.absolute_url().endswith("/%s" % self.context.id) :
                self.fb_url = self.fb_url[0:-1*(len(self.context.id)+1)]
        except:
            pass
        
        # Assign image URL and mime type
        image_url = image_mime_type = ''
        
        # Look up through the acquisition chain until we hit a Plone site, 
        # Section, or Subsite

        for i in aq_chain(self.context):
            if IPloneSiteRoot.providedBy(i):
                break
            
            (image_url, image_mime_type) = self.getImageInfo(i)
            
            if image_url:
                break
            
        # Fallback
        if not image_url:
            image_url = "%s/social-media-site-graphic.png" % self.context.portal_url()

        (self.fb_image, self.link_mime_type) = (image_url, image_mime_type)
        self.link_metadata_image = self.fb_image
        
        # FB config
        self.fbadmins = ['100001031380608','9370853','1485890864', '100003483428817']

        self.fbadmins.extend(getContextConfig(self.context, 'fbadmins', []))
            
        self.fbadmins = ','.join(self.fbadmins)

        self.fbappid = getContextConfig(self.context, 'fbappid', '374493189244485')

        self.fbpageid = getContextConfig(self.context, 'fbpageid', '53789486293')

            
class KeywordsViewlet(AgCommonViewlet):
    
    index = ViewPageTemplateFile('templates/keywords.pt')
    
    def update(self):

        super(KeywordsViewlet, self).update()
        
        tools = getMultiAdapter((self.context, self.request), name=u'plone_tools')
        
        sm = getSecurityManager()
        
        self.user_actions = self.context_state.actions(category='user')
        
        plone_utils = getToolByName(self.context, 'plone_utils')
        
        self.getIconFor = plone_utils.getIconFor
        
class NextPreviousViewlet(ViewletBase, NextPreviousView):
    render = ZopeTwoPageTemplateFile('templates/nextprevious.pt')

class PathBarViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/path_bar.pt')
        
    def update(self):
        super(PathBarViewlet, self).update()

        # Get the site id
        self.site = getSite().getId()
                
        self.navigation_root_url = self.portal_state.navigation_root_url()
    
        self.is_rtl = self.portal_state.is_rtl()

        breadcrumbs_view = getMultiAdapter((self.context, self.request),
                                           name='breadcrumbs_view')
                                           
        if 'extension.psu.edu' in self.site:
            start_breadcrumbs = 2
        else:
            start_breadcrumbs = 1
        end_breadcrumbs = 2
        total_breadcrumbs = start_breadcrumbs + end_breadcrumbs

        all_breadcrumbs = breadcrumbs_view.breadcrumbs()

        if len(all_breadcrumbs) > (total_breadcrumbs + 1):
            empty = {'absolute_url': None, 'Title': '...', }
            all_breadcrumbs = list(all_breadcrumbs)
            self.breadcrumbs = all_breadcrumbs[0:start_breadcrumbs] + [empty] + all_breadcrumbs[-1*end_breadcrumbs:]
        else:
            self.breadcrumbs = all_breadcrumbs


class LeadImageHeader(LeadImageViewlet, AgCommonViewlet):

    def update(self):
    
        # Only show header if we're on a subsite homepage

        context = aq_inner(self.context)
        portal_type = getattr(context, 'portal_type', None)

        try:
            layout = self.context.getLayout()
        except:
            layout = None

        self.showHeader = layout == 'document_subsite_view' and portal_type == 'HomePage'

class AnalyticsViewlet(BrowserView):
    implements(IViewlet, IContentProvider)

    def __init__(self, context, request, view, manager=None):
        super(AnalyticsViewlet, self).__init__(context, request)
        self.__parent__ = view
        self.context = context
        self.request = request
        self.view = view
        self.manager = manager

    def update(self):
        self.portal_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_portal_state')
        self.anonymous = self.portal_state.anonymous()

    def render(self):
        """render the agsci webstats snippet"""

        if self.anonymous:
            ptool = getToolByName(self.context, "portal_properties")
            snippet = safe_unicode(ptool.site_properties.webstats_js)

        else:
            snippet = ""

        return snippet

class UnitAnalyticsViewlet(AnalyticsViewlet):

    def render(self):
        """render the unit webstats snippet"""   

        if self.anonymous:
            ptool = getToolByName(self.context, "portal_properties")
            snippet = safe_unicode(ptool.site_properties.getProperty("unit_webstats_js", ""))
        else:
            snippet = ""

        return snippet
        

class RSSViewlet(AgCommonViewlet):
    def update(self):
        super(RSSViewlet, self).update()
        syntool = getToolByName(self.context, 'portal_syndication')
        if syntool.isSyndicationAllowed(self.context):
            self.allowed = True
            self.url = '%s/RSS' % self.context_state.object_url()
            self.page_title = self.context_state.object_title
        else:
            self.allowed = False

    render = ViewPageTemplateFile('templates/rsslink.pt')
    
class SiteRSSViewlet(ViewletBase):
    def update(self):
        ptool = getToolByName(self.context, "portal_properties")

        self.show_site_rss = False
        try:
            self.site_rss_title = ptool.agcommon_properties.site_rss_title
            self.site_rss_link = ptool.agcommon_properties.site_rss_link

            if self.site_rss_title and self.site_rss_link:
                self.show_site_rss = True

        except AttributeError:
            # Don't show site RSS
            pass
            
        
    render = ViewPageTemplateFile('templates/site_rss.pt')    

class TableOfContentsViewlet(AgCommonViewlet):

    index = ViewPageTemplateFile('templates/toc.pt')

    @property
    def enabled(self):
        obj = aq_base(self.context)
        getTableContents = getattr(obj, 'getTableContents', None)      

        enabled = False

        if getTableContents is not None:
            try:
                enabled = getTableContents()
            except KeyError:   
                # schema not updated yet
                enabled = False

        if self.isFolderFullView:
            enabled = False

        if self.full_width:
            enabled = True
        
        return enabled

    def getClass(self):
        klass = ['toc']
        
        if self.full_width:
            klass.append('toc-full-width')
        
        return " ".join(klass)

    @property
    def full_width(self):
        return getattr(self.context, 'toc_full_width', False)

class ContributorsViewlet(AgCommonViewlet):

    implements(IContentProvider)

    index = ViewPageTemplateFile('templates/contributors.pt')

    def title(self):
        return getContextConfig(self.context, 'contact_title', default='Contact Information')

    def showCreators(self):
        return not not getContextConfig(self.context, 'contact_creators')

    def showForContentTypes(self):
        return getContextConfig(self.context, 'person_portlet_types', default=['News Item'])

    @property
    def people(self):
       
        psuid_re = re.compile("^[A-Za-z][A-Za-z0-9_]*$") # Using one from FSD
        
        people = []
        
        if self.showCreators():
            if self.context.portal_type not in self.showForContentTypes():
                return people
            peopleList = [x.strip() for x in self.context.listCreators()]
        else:
            peopleList = [x.strip() for x in self.context.Contributors()]
            
        if peopleList:
            portal_catalog = getToolByName(self.context, 'portal_catalog')
            search_results = portal_catalog.searchResults({'portal_type' : 'FSDPerson', 'id' : peopleList })
            
            for id in peopleList:
                found = False
    
                for r in search_results:
                    if r.id == id:
    
                        obj = r.getObject()
                        job_titles = obj.getJobTitles()
    
                        people.append({
                                            'name' : obj.pretty_title_or_id(), 
                                            'title' : job_titles and job_titles[0] or '', 
                                            'url' : obj.absolute_url(),
                                            'phone' : obj.getOfficePhone(),
                                            'email' : obj.getEmail(),
                                            'image' : getattr(obj, 'image_thumb', None),
                                            'tag' : getattr(obj, 'tag', None)
                                            })
                        found = True

                if not found and not psuid_re.match(id):
                    parts = id.split("|")
                    parts.extend(['']*(5-len(parts)))
                    (name, title, f1, f2, f3) = parts
                    (url, email, phone) = ('', '', '')
                    
                    for i in (f1, f2, f3):
                        if '@' in i:
                            email = i
                        elif i.startswith('http'):
                            url = i
                        else:
                            tmp_phone = scrubPhone(i, return_original=False)
                            if tmp_phone:
                                phone = tmp_phone
                    
                    people.append({'name' : name, 
                                            'title' : title, 
                                            'url' : url,
                                            'phone' : phone,
                                            'email' : email,
                                            'image' : None,})

        return people

    @property
    def is_printed_newsletter(self):
        return 'newsletter_print' in self.request.getURL()


class CustomCommentsViewlet(CommentsViewlet):

    def update(self):       
        super(CustomCommentsViewlet, self).update()
        try:
            self.xid = md5(self.context.UID()).hexdigest()
        except AttributeError:
            self.xid = md5(self.context.absolute_url()).hexdigest()

class _ContentWellPortletsViewlet(ContentWellPortletsViewlet, AgCommonViewlet):

    def have_portlets(self, view=None):
        """Determine whether a column should be shown.
        """
        portlets = False
        context = aq_inner(self.context)
        layout = getMultiAdapter((context, self.request), name=u'plone_layout')

        for (manager_obj, manager_name) in self.portletManagers():
            if layout.have_portlets(manager_name, view=view):
                portlets = True
        
        return portlets

    def portletManagersToShow(self):
        visibleManagers = []
        for mgr, name in self.portletManagers():
            if mgr(self.context, self.request, self).visible:
                visibleManagers.append(name)
        
        managers = []
        numManagers = len(visibleManagers)
        for counter, name in enumerate(visibleManagers):
            managers.append((name, (name.split('.')[-1])))
        return managers
    
    def showManagePortlets(self):
        if self.canManagePortlets:
            if self.isHomePage:
                return True
            elif self.canManageBodyPortlets():
                return True
        return False

    def canManageBodyPortlets(self):
        return getattr(self.context, 'manage_body_portlets', False)
        

class PortletsBelowViewlet(_ContentWellPortletsViewlet):
    name = 'BelowPortletManager'
    manage_view = '@@manage-portletsbelowcontent'

class PortletsAboveViewlet(_ContentWellPortletsViewlet):
    name = 'AbovePortletManager'
    manage_view = '@@manage-portletsabovecontent'

class FooterPortletsViewlet(_ContentWellPortletsViewlet):
    name = 'FooterPortletManager'
    manage_view = '@@manage-footerportlets'
    
class LocalSearchViewlet(SearchBoxViewlet):

    def counties(self):
        return sorted(county_data.keys())

    def searchURL(self):

        default_search_url ='%s/search' % self.site_url
        localsearch_collection_path = self.context.getProperty('localsearch_collection_path', '')

        if self.context.portal_type in ['Topic']:
            if self.context.getProperty('localsearch_override_collection', False):
                return default_search_url # If we override the collection filtering behavior
            else:
                parent = self.context.getParentNode()
                
                if self.context.getId() == parent.getDefaultPage():
                    return parent.absolute_url()
                else:
                    return self.context.absolute_url()
        elif localsearch_collection_path:
            if localsearch_collection_path.startswith('/'):
                localsearch_collection_path = localsearch_collection_path[1:]
                try:
                    return getSite().restrictedTraverse(localsearch_collection_path).absolute_url()
                except AttributeError:
                    pass

        return default_search_url

class ContentRelatedItems(ContentRelatedItemsBase):
   
    def show_related_items(self):
        if self.related_items():
            return getattr(self.context, 'show_related_items', True)
        return False

# provideAdapter for viewlets to be registered in standalone mode

provideAdapter(ContributorsViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='agcommon.contributors')

provideAdapter(AnalyticsViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='plone.analytics')

provideAdapter(AddThisViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='agcommon.addthis')
