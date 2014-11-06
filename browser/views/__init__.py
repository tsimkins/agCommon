from Acquisition import aq_inner
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.agCommon import getContextConfig
from Products.agCommon.browser.interfaces import IFSDShortBio
from RestrictedPython.Utilities import same_type as _same_type
from RestrictedPython.Utilities import test as _test
from StringIO import StringIO 
from collective.contentleadimage.leadimageprefs import ILeadImagePrefsForm
from collective.contentleadimage.utils import getImageAndCaptionFields, getImageAndCaptionFieldNames
from plone.app.workflow.browser.sharing import SharingView, AUTH_GROUP
from plone.memoize.instance import memoize
from zope.component import getUtility, getMultiAdapter
from zope.component.interfaces import ComponentLookupError
from zope.interface import implements, Interface

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

try:
    from agsci.ExtensionExtender.counties import getSurroundingCounties
except ImportError:
    def getSurroundingCounties(c):
        return c

try:
    from pyPdf import PdfFileReader
except ImportError:
    def PdfFileReader(*args, **kwargs):
        return None

try:
    from agsci.ExtensionExtender.interfaces import IExtensionPublicationExtender
except ImportError:
    class IExtensionPublicationExtender(Interface):
        """
            Placeholder interface
        """

try:
    from agsci.UniversalExtender.interfaces import IUniversalPublicationExtender
except ImportError:
    class IUniversalPublicationExtender(Interface):
        """
            Placeholder interface
        """

"""
    Interface Definitions
"""

class IAgendaView(Interface):
    """
    agenda view interface
    """

    pass

class IEventTableView(Interface):
    """
    event table view interface
    """

    pass

class ISearchView(Interface):

    pass

class IFolderView(Interface):

    pass


"""
    Class Definitions
"""

class FolderView(BrowserView):

    implements(IFolderView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def show_date(self):
        return getContextConfig(self.context, 'show_date', False)

    @property
    def show_image(self):
        return getContextConfig(self.context, 'show_image', False)

    @property
    def show_read_more(self):
        return getContextConfig(self.context, 'show_read_more', False)

    @property
    def portal_state(self):
        return getMultiAdapter((self.context, self.request), name=u'plone_portal_state')

    @property
    def context_state(self):
        return getMultiAdapter((self.context, self.request),
                                name=u'plone_context_state')

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def anonymous(self):
        return self.portal_state.anonymous()

    @property
    def show_short_bio(self):
        return IFSDShortBio.providedBy(self.context)

    # Providing Restricted Python "test" method
    def test(self, *args):
        return _test(*args)

    # Providing Restricted Python "test" same_type
    def same_type(self, arg1, *args):
        return _same_type(arg1, *args)

    @property
    def prefs(self):
        portal = getUtility(IPloneSiteRoot)
        return ILeadImagePrefsForm(portal)

    def getImageFieldName(self, obj):
        return getImageAndCaptionFieldNames(obj)[0]

    def tag(self, obj, css_class='tileImage', scale=None):
        context = aq_inner(obj)

        (field, titlef) = getImageAndCaptionFields(obj)

        if titlef is not None:
            title = titlef.get(context)
        else:
            title = ''
        if field is not None:
            if field.get_size(context) != 0:
                if not scale:
                    scale = self.prefs.desc_scale_name
                return field.tag(context, scale=scale, css_class=css_class, title=title)
        return ''

    def getItemClass(self, item, layout='folder_listing'):

        # Default classes for all views
        item_class = ['tileItem', 'visualIEFloatFix']

        # If "Hide items excluded from navigation" is checked on the folder, 
        # and this item is excluded, apply the 'excludeFromNav' class
        if getattr(self.context.aq_base, 'hide_exclude_from_nav', False) and getattr(item, 'exclude_from_nav'):
            item_class.append('excludeFromNav')

        # Per-layout classes
        if layout == 'folder_summary_view':
            # Class for rows in summary view
            item_class.append('tileSummary')
            
            # Special classes for person
            if item.portal_type == 'FSDPerson':
                item_class.append('tileItemLeadImage')

            # Another if we're showing images
            elif self.show_image:
                item_class.append('tileSummaryLeadImage')
            

        elif layout == 'folder_listing':
        
            if 'excludeFromNav' not in item_class:
                item_class.append('contenttype-%s' % item.Type.lower())

            if self.show_image:
                item_class.append('tileItemLeadImage')
            

        return " ".join(item_class)

class SearchView(FolderView):

    implements(ISearchView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def page_title(self):
        if 'FSDPerson' in self.request.form.get('portal_type', []):
            return 'Search People'
        elif 'Event' in self.request.form.get('portal_type', []):
            return 'Search Events'
        elif 'News Item' in self.request.form.get('portal_type', []):
            return 'Search News'
        elif 'courses' in self.request.form.get('Subject', []):
            return 'Search Courses'
        else:
            return 'Search'

    def sort_order(self):
        if self.sort_on() in ['created', 'modified', 'effective']:
            return 'descending'
        else:
            return 'ascending'

    def sort_on(self):
        if self.request.form.get('sort_on'):
            return self.request.form['sort_on']
        elif 'FSDPerson' in self.request.form.get('portal_type', []):
            return 'getSortableName'
        elif 'Event' in self.request.form.get('portal_type', []):
            return 'start'
        elif 'News Item' in self.request.form.get('portal_type', []):
            return 'effective'
        else:
            return ''

    def getResults(self):
        now = DateTime()

        try:
            ziptool = getToolByName(self.context, 'extension_zipcode_tool')
        except AttributeError:
            ziptool = None

        filtered_results = []
        files = []

        use_types_blacklist = self.request.form.get("use_types_blacklist", True)
        use_navigation_root = self.request.form.get("use_navigation_root", True)
        
        # Counties
        counties = self.request.form.get('Counties')

        if counties and len(counties) == 1:
            self.request.form['Counties'] = getSurroundingCounties(counties[0])
        
        # ZIP Code search
        
        search_zip = self.request.form.get('zip_code_input')
        search_zip_radius = self.request.form.get('zip_code_radius')
        
        if ziptool and search_zip and search_zip_radius:
            # We have a ziptool
            zips = ziptool.getNearbyZIPs(search_zip, search_zip_radius)
            all_zips = self.portal_catalog.uniqueValuesFor('zip_code')
            search_zip_list = list(set(zips) & set(all_zips))
            search_zip_list.append('00000')
            self.request.form['zip_code'] = search_zip_list
            
        results = self.context.queryCatalog(REQUEST=self.request,use_types_blacklist=use_types_blacklist, use_navigation_root=use_navigation_root)

        for r in results:
            if self.anonymous and r.portal_type == 'Event' and r.end < now:
                continue
            if r.portal_type in ['File']:
                files.append(r)
            else:
                filtered_results.append(r)
        
        filtered_results.extend(files)
        
        def getDistance(z1, z2):
            return ziptool.getDistance(z1, z2,novalue=9999)
        
        # Switch order for people to distance
        if ziptool and search_zip and 'FSDPerson' in self.request.form.get('portal_type', []):
            filtered_results.sort(key=lambda x: getDistance(x.zip_code, search_zip))
        
        return filtered_results

class AgendaView(FolderView):
    """
    agenda browser view
    """
    implements(IAgendaView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

        parent = self.context.getParentNode()
        if self.context.id == parent.getDefaultPage():
            self.here_url = parent.absolute_url()
        else:
            self.here_url = self.context.absolute_url()

    def getFolderContents(self, contentFilter={}):

        events = []
        folder_path = ""

        if self.context.portal_type == 'Topic':
            try:
                events = self.context.queryCatalog(**contentFilter)
            except AttributeError:
                # We don't like a relative path here for some reason.
                # Until we figure it out, fall through and just do the default query.
                # That should work in most cases.
                parent_physical_path = list(self.context.getPhysicalPath())
                parent_physical_path.pop()
                folder_path = '/'.join(parent_physical_path)
                pass

            # If we're a collection (Topic), we may be a default page.  Figure out
            # if we're the default page, and if so, set the here_url to our parent.
            parent = self.context.getParentNode()
            if self.context.id == parent.getDefaultPage():
                self.here_url = parent.absolute_url()

        if not events:
            catalog = self.portal_catalog

            if not folder_path:
                folder_path = '/'.join(self.context.getPhysicalPath())

            events = catalog.searchResults({'portal_type' : ['Event', 'TalkEvent'],
                                            'path' : {'query': folder_path, 'depth' : 4},
                                            'start' : {'query' : DateTime(), 'range' : 'min'},
                                            'sort_on' : 'start' })
        return events

    def data(self, contentFilter={}):

        site_properties = getToolByName(self.context, 'portal_properties').get("site_properties")
        day_format = site_properties.localTimeFormat
        month_format = '%B %Y'

        # Set the 'agenda_view_day' property in the ZMI to show the agenda by
        # days rather than by month.  It's not worth having a separate view,
        # since it will be a very small minority of use cases.

        self.show_days = getContextConfig(self.context, 'agenda_view_day', False)

        days = {}
        months = {}
        agenda = []

        events = self.getFolderContents(contentFilter)

        for e in events:

            if e.portal_type == 'Event' or e.portal_type == 'TalkEvent':
                event_start = e.start
                month = event_start.strftime('%Y-%m')
                day = event_start.strftime('%Y-%m-%d')

                if not months.get(month):
                    months[month] = {'id' : event_start.strftime(month_format).lower().replace(' ', '-'),
                                     'label' : event_start.strftime(month_format), 'items' : []}

                if not days.get(day):
                    days[day] = {'id' : event_start.strftime(day_format).lower().replace(' ', '-'),
                                 'label' : event_start.strftime(day_format), 'items' : []}

                months[month]['items'].append(e)
                days[day]['items'].append(e)


        if self.show_days:

            for d in sorted(days.keys()):
                agenda.append(days[d])

        else:

            for m in sorted(months.keys()):
                agenda.append(months[m])

        return agenda



    def getBodyText(self):
        return self.context.getBodyText()

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()


class EventTableView(AgendaView):
    """
    agenda browser view
    """
    implements(IEventTableView)


class HomepageView(FolderView):

    implements(IFolderView)

    @property
    def image_format(self):
        return getattr(self.context, 'homepage_image_format', 'standard')

    @property
    def portlet_format(self):
        return getattr(self.context, 'homepage_portlet_format', 'standard')
        
    @property
    def hasDescriptionOrText(self):
        if self.hasDescription or self.hasText:
            return True
        else:
            return False

    @property
    def hasDescription(self):
        if self.context.Description():
            return True
        else:
            return False

    @property
    def hasText(self):
        if self.context.getText():
            return True
        else:
            return False

    @property
    def showHomepageText(self):
        if self.hasText():
            return getattr(self.context, 'show_homepage_text', True)
        else:
            return getattr(self.context, 'show_homepage_text', False)

class ModifiedSharingView(SharingView):

    template = ViewPageTemplateFile('../templates/sharing.pt')

    @memoize
    def role_settings(self):
        """Get current settings for users and groups for which settings have been made.

        Returns a list of dicts with keys:

         - id
         - title
         - type (one of 'group' or 'user')
         - roles

        'roles' is a dict of settings, with keys of role ids as returned by
        roles(), and values True if the role is explicitly set, False
        if the role is explicitly disabled and None if the role is inherited.
        """

        existing_settings = self.existing_role_settings()
        user_results = self.user_search_results()
        group_results = self.group_search_results()

        for g in existing_settings:
            if g['id'] != AUTH_GROUP and g['type'] == 'group':
                g['group_url'] = "%s/@@usergroup-groupmembership?groupname=%s" % (getSite().absolute_url(), g['id'])

        current_settings = existing_settings + user_results + group_results

        # We may be called when the user does a search instead of an update.
        # In that case we must not loose the changes the user made and
        # merge those into the role settings.
        requested = self.request.form.get('entries', None)
        if requested is not None:
            knownroles = [r['id'] for r in self.roles()]
            settings = {}
            for entry in requested:
                roles = [r for r in knownroles
                                if entry.get('role_%s' % r, False)]
                settings[(entry['id'], entry['type'])] = roles

            for entry in current_settings:
                desired_roles = settings.get((entry['id'], entry['type']), None)

                if desired_roles is None:
                    continue
                for role in entry["roles"]:
                    if entry["roles"][role] in [True, False]:
                        entry["roles"][role] = role in desired_roles

        current_settings.sort(key=lambda x: safe_unicode(x["type"])+safe_unicode(x["title"]))

        return current_settings

class RSSTemplateView(FolderView):

    pass

class AnnualEventRedirect(FolderView):
    
    """
    course_annual_redirect
    Redirect to the course's upcoming event if, and only if:
     - The course collection has a 'course-annual' tag
     - There is one and only one upcoming event
     - AND current user is logged out
    """

    def __call__(self):
        RESPONSE =  self.request.RESPONSE
        
        results = self.context.queryCatalog()
        
        if results and len(results) == 1 and self.anonymous:
            event = results[0]
            return RESPONSE.redirect(event.getURL())
        else:
            if not self.anonymous:
                RESPONSE.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')
            else:
                RESPONSE.setHeader('Cache-Control', 'max-age=0, s-maxage=300, must-revalidate, public, proxy-revalidate')
        
            return getMultiAdapter((self.context, self.request), name=u'agenda_view')()


class PublicationView(FolderView):

    @property
    def publication_code(self):
        return getattr(self.context, 'extension_publication_code', None)

    @property
    def publication_series(self):
        return getattr(self.context, 'extension_publication_series', None)

    @property
    def publication_cost(self):
        return getattr(self.context, 'extension_publication_cost', None)

    @property
    def publication_for_sale(self):
        return getattr(self.context, 'extension_publication_for_sale', None)

    @property
    def contact_pdc(self):
        return getattr(self.context, 'extension_publication_contact_pdc', None)

    @property
    def orderPublication(self):
        return getattr(self.context, 'extension_publication_contact_pdc', False)

    @property
    def order_url(self):
        return '%s/order' % self.context.absolute_url()

        
    @property
    def downloadPDF(self):
        return (self.pdf_url != '')

    @property
    def pdf_url(self):

        # Integrate Extension PDF download
        if IExtensionPublicationExtender.providedBy(self.context) or IUniversalPublicationExtender.providedBy(self.context):
            if hasattr(self.context, 'extension_publication_file') and self.context.extension_publication_file:
                return '%s/extension_publication_file' % self.context.absolute_url()
            elif hasattr(self.context, 'extension_publication_url') and self.context.extension_publication_url:
                return self.context.extension_publication_url
            elif hasattr(self.context, 'extension_publication_download') and self.context.extension_publication_download:
                return '%s/pdf_factsheet' % self.context.absolute_url()

        return ''

    def getPDF(self):

       if self.context.getContentType() in ['application/pdf']:
            file = self.context.getFile()
            file_data = StringIO(file.data)
            return PdfFileReader(file_data)
        
       return None

    def getNumPages(self):

        pdf = self.getPDF()
        
        if pdf:
            return pdf.getNumPages()
        
        return None

class OrderPublicationView(PublicationView):

    def page_title(self):
        return 'Order Publication: %s' % self.context.Title()