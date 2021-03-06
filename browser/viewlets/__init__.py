from AccessControl import getSecurityManager
from Acquisition import aq_inner, aq_base, aq_chain
from DateTime import DateTime
from Products.agCommon import getSearchConfig, toISO, getBackgroundImages, \
                              MAX_HOMEPAGE_IMAGE_WIDTH, MAX_HOMEPAGE_IMAGE_HEIGHT
from Products.ATContentTypes.interfaces.event import IATEvent
from Products.ATContentTypes.interfaces.news import IATNewsItem
from Products.FacultyStaffDirectory.interfaces.person import IPerson
from Products.CMFCore.Expression import Expression, getExprContext
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from Products.ContentWellPortlets.browser.viewlets import ContentWellPortletsViewlet
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile, ZopeTwoPageTemplateFile
from Products.agCommon import getContextConfig, scrubPhone
from Products.agCommon.browser.views import FolderView, PublicationView
from cgi import escape
from collective.contentleadimage.utils import getImageAndCaptionFields, getImageAndCaptionFieldNames
from collective.contentleadimage.browser.viewlets import LeadImageViewlet
from hashlib import md5
from ..interfaces import ICollegeHomepage, IInspectletEnabled
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
import json
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

class EmptyViewlet(ViewletBase):

    def index(self):
        return "<!-- This viewlet intentionally left blank. -->"

class AgCommonViewlet(ViewletBase):

    search_section = False

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
    def isSiteHomepage(self):
        return (self.isHomePage and IPloneSiteRoot.providedBy(self.context.aq_parent))

    @property
    def hide_breadcrumbs(self):
        # Determine if we should hide breadcrumbs

        # The answer is now 'no.'
        return False


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
    def isDefaultPage(self):
        # Determine if we're the default page

        parent = self.context.aq_parent

        try:
            parent_default_page_id = parent.getDefaultPage()
        except AttributeError:
            parent_default_page_id = ''

        return (self.context.id == parent_default_page_id)

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
    def portlet_format(self):
        return getattr(self.context, 'homepage_portlet_format', 'standard')

    @property
    def isSyndicationAllowed(self):
        try:
            syntool = self.context.restrictedTraverse('@@syndication-util')
            return (syntool.site_enabled() and syntool.context_enabled())
        except AttributeError:
            syntool = getToolByName(self.context, 'portal_syndication')
            return syntool.isSyndicationAllowed(self.context)

    @memoize
    def getSection(self):
        return self.agcommon_utilities.getSection(search=self.search_section)

    @property
    def portal_url(self):
        return self.context.portal_url()

    @property
    def agcommon_utilities(self):
        return self.context.restrictedTraverse('@@agcommon_utilities')

    def get_agcommon_properties(self, property_id, property_default=None):
        return self.agcommon_utilities.get_agcommon_properties(property_id, property_default)


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

class SectionTitleViewlet(AgCommonViewlet):

    def section_url(self):
        section = self.getSection()

        if section:
            return section.absolute_url()

        return None


    def section_title(self):
        section = self.getSection()

        if section:
            return section.Title()

        return None


class HomepageColumnsViewlet(PortletViewlet):
    index = ViewPageTemplateFile('templates/homepage-columns.pt')


class HomepageTextViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/homepagetext.pt')

    def showHomepageHeading(self):
        section = self.getSection()

        if section:
            return (section.Title() == self.context.Title())

        else:
            return (self.portal_state.portal().Title() == self.context.Title())


class HomepageImageViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/homepageimage.pt')

    @memoize
    def image_data(self):

        background_images = None

        p = self.context.aq_parent

        if 'background-images' in p.objectIds():
            background_images = p['background-images']

        elif getattr(self.context, 'acquire_background_images', False):
            try:
                background_images = self.context.restrictedTraverse('background-images')
            except:
                pass

        if background_images:

            max_height = self.get_agcommon_properties('max_homepage_image_width',
                                                  MAX_HOMEPAGE_IMAGE_WIDTH)

            max_width = self.get_agcommon_properties('max_homepage_image_height',
                                                 MAX_HOMEPAGE_IMAGE_HEIGHT)

            return getBackgroundImages(background_images,
                                       maxWidth=max_height,
                                       maxHeight=max_width)

        return ([], [])

    def image_urls(self):
        return ";".join(self.image_data()[0])

    def image_heights(self):
        return ";".join(self.image_data()[1])

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

    # Don't show the title if we have a slider.
    # Don't show it if we're the site root.
    @property
    def showTitle(self):
        if self.slider_has_contents:
            return False

        return not IPloneSiteRoot.providedBy(self.context.aq_parent)


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
    def isPerson(self):
        portal_type = getattr(self.context, 'portal_type', None)
        return (portal_type == 'FSDPerson')

    @property
    def hide_addthis(self):

        # Hide if not enabled in agCommon properties
        if not self.get_agcommon_properties('enable_addthis', False):
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

    @property
    def likeurl(self):
        _ = escape(safe_unicode(self.context.absolute_url()))
        return _.replace('https://', 'http://') # So we don't lose the old like

    def show_fblike(self):

        hide_fblike = getattr(self.context, 'hide_fblike', False)
        show_fblike = getattr(self.context, 'show_fblike', False)
        is_homepage = self.isHomePage
        is_anon = self.anonymous

        if is_anon:
            if show_fblike:
                return True

            if is_homepage or hide_fblike:
                return False

            return True

        return False


class FooterViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/footer.pt')

    def update(self):

        # Get copyright info

        self.footer_copyright = self.get_agcommon_properties('footer_copyright', '')
        self.footer_copyright_link = self.get_agcommon_properties('footer_copyright_link', '')

        self.footer_copyright_2 = self.get_agcommon_properties('footer_copyright_2', None)
        self.footer_copyright_link_2 = self.get_agcommon_properties('footer_copyright_link_2', None)

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

        (leadImage_fieldname, leadImageCaption_fieldname) = getImageAndCaptionFieldNames(context)
        (leadImage_field, leadImageCaption_field) = getImageAndCaptionFields(context)

        try:
            if leadImage_field and leadImage_field.get(context) and leadImage_field.get(context).get_size() > 0:
                image_url = "%s/%s" % (context.absolute_url(), leadImage_fieldname)
                image_mime_type = leadImage_field.getContentType(context)
        except:
            pass

        return (image_url, image_mime_type)

    def update(self):

        super(FBMetadataViewlet, self).update()

        site_title = safe_unicode(self.site_title)
        page_title = safe_unicode(self.page_title())
        org_title = safe_unicode(self.org_title)

        titles = [x for x in (page_title, site_title, org_title) if x and x.lower() != 'none']
        unique_titles = list(set(titles))
        unique_titles.sort(key=lambda x: titles.index(x))

        if len(unique_titles) == 3:
            self.fb_site_name = u'%s (%s)' % tuple(unique_titles[1:3])
            self.fb_title = u'%s (%s)' % tuple(unique_titles[0:2])
        elif len(unique_titles) == 2:
            self.fb_title = self.fb_site_name = '%s (%s)' % tuple(unique_titles[0:2])
        else:
            self.fb_title = self.fb_site_name = unique_titles[0]

        self.showFBMetadata = True

        self.fb_url = self.context.absolute_url()

        try:
            # Remove this page's id from the URL if it's a default page.
            if self.isDefaultPage and self.context.absolute_url().endswith("/%s" % self.context.id) :
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
        self.fbadmins = ['100001031380608', '9370853', '100003483428817']

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

        if self.isSyndicationAllowed:
            self.allowed = True
            self.url = '%s/RSS' % self.context_state.object_url()
            self.page_title = self.context_state.object_title
        else:
            self.allowed = False

    render = ViewPageTemplateFile('templates/rsslink.pt')

class SiteRSSViewlet(ViewletBase):
    def update(self):

        self.show_site_rss = False

        try:
            self.site_rss_title = self.get_agcommon_properties('site_rss_title', '')
            self.site_rss_link = self.get_agcommon_properties('site_rss_link', '')

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

    def getPeopleResults(self, peopleList):
        portal_catalog = getToolByName(self.context, 'portal_catalog')
        return portal_catalog.searchResults({'portal_type' : 'FSDPerson', 'id' : peopleList })

    def getPersonInfo(self, brain):
        obj = brain.getObject()
        job_titles = obj.getJobTitles()

        return {
            'name' : obj.pretty_title_or_id(),
            'title' : job_titles and job_titles[0] or '',
            'url' : obj.absolute_url(),
            'phone' : obj.getOfficePhone(),
            'email' : obj.getEmail(),
            'image' : getattr(obj, 'image_thumb', None),
            'tag' : getattr(obj, 'tag', None)
        }

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
            search_results = self.getPeopleResults(peopleList)

            for id in peopleList:
                found = False

                for r in search_results:
                    if r.id == id:
                        people.append(self.getPersonInfo(r))
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
            self.xid = md5(self.url).hexdigest()


    @property
    def url(self):
        _ = self.context.absolute_url()
        return _.replace('https://', 'http://') # So we don't lose old comments

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

class PortletsHeaderViewlet(_ContentWellPortletsViewlet):
    name = 'InHeaderPortletManager'
    manage_view = '@@manage-portletsinheader'

class PortletsBelowViewlet(_ContentWellPortletsViewlet):
    name = 'BelowPortletManager'
    manage_view = '@@manage-portletsbelowcontent'

class PortletsAboveViewlet(_ContentWellPortletsViewlet):
    name = 'AbovePortletManager'
    manage_view = '@@manage-portletsabovecontent'

class FooterPortletsViewlet(_ContentWellPortletsViewlet):
    name = 'FooterPortletManager'
    manage_view = '@@manage-portletsfooter'

class MultiSearchViewlet(AgCommonViewlet):

    search_section = True

    def getSearchOptions(self):

        return getSearchConfig(context=self.context, path=self.section_path,
                               section_title=self.section_title,
                               site_title=self.site_title)

    @property
    def site_title(self):
        site = getSite()

        if site:
            return site.Title()

        return None

    @property
    def section_title(self):
        section = self.getSection()

        if section:
            return section.Title()

        return None

    @property
    def section_path(self):
        section = self.getSection()

        if section:
            return '/'.join(section.getPhysicalPath())

        return None


class LocalSearchViewlet(MultiSearchViewlet):

    def counties(self):
        return sorted(county_data.keys())

    def searchURL(self):
        anchor = ""

        if self.context.getLayout() in ['extension_course_view'] or 'courses' in self.context.Subject():
            anchor = "#event-listing"

        default_search_url ='%s/search' % self.portal_url
        localsearch_collection_path = self.context.getProperty('localsearch_collection_path', '')

        if self.context.portal_type in ['Topic']:
            if self.context.getProperty('localsearch_override_collection', False):
                return default_search_url # If we override the collection filtering behavior
            else:
                parent = self.context.getParentNode()

                if self.context.getId() == parent.getDefaultPage():
                    return '%s%s' % (parent.absolute_url(), anchor)
                else:
                    return '%s%s' % (self.context.absolute_url(), anchor)

        elif localsearch_collection_path:
            if localsearch_collection_path.startswith('/'):
                localsearch_collection_path = localsearch_collection_path[1:]
                try:
                    return getSite().restrictedTraverse(localsearch_collection_path).absolute_url()
                except AttributeError:
                    pass

        return default_search_url

    @property
    def section_path(self):
        section = self.context

        if self.isDefaultPage:
            section = self.context.aq_parent

        return ['/'.join(section.getPhysicalPath()), ]

class ContentRelatedItems(ContentRelatedItemsBase):

    def show_related_items(self):
        if self.related_items():
            return getattr(self.context, 'show_related_items', True)
        return False

class GooglePlusViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/googleplus-head.pt')

    @property
    def url(self):
        return self.get_agcommon_properties('googleplus_url', None)


class GoogleStructuredDataViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/google-structured-data.pt')

    def getImage(self):
        # Check for item image
        context = self.context

        (image_field, image_caption_field) = getImageAndCaptionFields(context)
        (image_field_name, image_caption_field_name) = getImageAndCaptionFieldNames(context)

        if image_field and \
            image_field.get(context) and \
            image_field.get(context).get_size():
            return '%s/%s' % (context.absolute_url(), image_field_name)

        return ''

    def data(self):

        context = self.context

        data = {}

        if ICollegeHomepage.providedBy(self.context):
            data = {
                    '@context': 'http://schema.org',
                    '@type': 'EducationalOrganization',
                    'address': {    '@type': 'PostalAddress',
                                    'addressLocality': 'University Park',
                                    'addressRegion': 'PA',
                                    'postalCode': '16802',
                                    'streetAddress': 'Penn State University'},
                    'logo': 'http://agsci.psu.edu/psu-agsciences-logo.png',
                    'name': 'Penn State College of Agricultural Sciences',
                    'sameAs': [
                        'http://www.facebook.com/agsciences',
                        'http://www.twitter.com/agsciences',
                        'http://plus.google.com/+PennStateAgSciences',
                        'http://instagram.com/agsciences',
                        'http://www.linkedin.com/company/penn-state-college-of-agricultural-sciences',
                        'http://www.youtube.com/psuagsciences',
                        'http://en.wikipedia.org/wiki/Penn_State_College_of_Agricultural_Sciences'],
                    'telephone': '+1-814-865-7521',
                    'url': 'http://agsci.psu.edu'
                    }

        elif IATEvent.providedBy(context):

            data = {
                    '@context': 'http://schema.org',
                    '@type': 'Event',
                    'name': context.Title(),
                    'description' : context.Description(),
                    'startDate' : toISO(context.start()),
                    'endDate' : toISO(context.end()),
                    'url' : context.absolute_url(),
                    'location' : {
                        "@type" : "Place",
                        "address" : getattr(context, 'location', ''),
                        "name" : getattr(context, 'location', ''),
                    }
            }

        elif IATNewsItem.providedBy(context):

            data = {
                    '@context': 'http://schema.org',
                    '@type': 'Article',
                    'headline': context.Title(),
                    'description' : context.Description(),
                    'datePublished' : toISO(context.effective()),
                    'url' : context.absolute_url(),
            }

        elif IPerson.providedBy(context):

            jobTitles = context.getJobTitles()

            if jobTitles:
                job_title = jobTitles[0]
            else:
                job_title = ""

            address = ', '.join(context.getOfficeAddress().strip().split("\n"))

            data = {
                    '@context': 'http://schema.org',
                    '@type': 'Person',
                    'url' : context.absolute_url(),
                    'email' : context.getEmail(),
                    'givenName' : context.getFirstName(),
                    'additionalName' : context.getMiddleName(),
                    'familyName' : context.getLastName(),
                    'telephone' : context.getOfficePhone(),
                    'jobTitle' : job_title,
                    'workLocation' : {
                        '@type' : 'PostalAddress',
                        'addressCountry' : 'US',
                        'addressLocality' : context.getOfficeCity(),
                        'addressRegion' : context.getOfficeState(),
                        'postalCode' : context.getOfficePostalCode(),
                        'streetAddress' : address,
                    }
            }

        data['image'] = self.getImage()

        if data:
            return json.dumps(data, indent=4)

        return None

# Google Tag Manager
# Note: This is not called from configure.zcml like a standard viewlet.  Google
# documentation says to include it immediately after the body tag, so that's
# what we're doing in this case.  This is called from main_template with:
#
#    <tal:googletagmanager
#        replace="structure provider:agcommon.googletagmanager" />
#
# which renders the viewlet as part of the template.  This uses the
# "provideAdapter" line at the bottom of this file.

class GoogleTagManagerViewlet(AgCommonViewlet):
    index = ViewPageTemplateFile('templates/google_tag_manager.pt')

    @property
    def gtm_account(self):

        # No tag manager for logged in users.
        if not self.anonymous:
            return None

        return self.get_agcommon_properties('gtm_account', None)


class LogoViewlet(AgCommonViewlet):

    def site_header(self):
        return self.agcommon_utilities.getSiteHeader()

    def department_header(self):
        return self.agcommon_utilities.getDepartmentHeader()

    def logo_url(self):
        if self.site_header() == 'penn_state':
            return 'http://www.psu.edu'

        elif self.site_header() == 'extension':
            return '//extension.psu.edu'

        return '//agsci.psu.edu'

    def portal_title(self):
        return self.portal_state.portal_title()

    def navigation_root_url(self):
        return self.portal_state.navigation_root_url()


class EditorMessageViewlet(AgCommonViewlet):

    @property
    def message(self):
        return self.get_agcommon_properties('editor_message', None)

    def show(self):

        if not self.anonymous:
            return not not self.message

        return False

class InspectletViewlet(AgCommonViewlet):

    @property
    def enabled(self):

        for i in aq_chain(self.context):

            if IInspectletEnabled.providedBy(i):
                return True

            if IPloneSiteRoot.providedBy(i):
                break

    def show(self):

        if self.anonymous:
            return not not self.enabled

class DataTablesViewlet(AgCommonViewlet):
    pass

# provideAdapter for viewlets to be registered in standalone mode

provideAdapter(ContributorsViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='agcommon.contributors')

provideAdapter(AnalyticsViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='plone.analytics')

provideAdapter(AddThisViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='agcommon.addthis')

provideAdapter(GoogleTagManagerViewlet, adapts=(Interface,IDefaultBrowserLayer,IBrowserView), provides=IContentProvider, name='agcommon.googletagmanager')
