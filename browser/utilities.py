from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import normalizeString
from Products.Five import BrowserView
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from Products.agCommon import getContextConfig
from Products.agCommon import increaseHeadingLevel as _increaseHeadingLevel
from urllib import urlencode
from zope.component import getMultiAdapter
from zope.interface import implements, Interface
import re

try:
    from agsci.ExtensionExtender.counties import getSurroundingCounties
except ImportError:
    def getSurroundingCounties(c):
        return c


class IAgCommonUtilities(Interface):

    def substituteEventLocation(self):
        pass

    def substituteTitle(self):
        pass

    def reorderTopicContents(self):
        pass

    def toMarkdown(self):
        pass

    def getUTM(self):
        pass

    def customBodyClass(self):
        pass

    def contentFilter(self):
        pass


class AgCommonUtilities(BrowserView):

    implements(IAgCommonUtilities)

    def substituteEventLocation(self, item):

        if getContextConfig(self.context, 'show_event_location'):
            show_event_location = True
        else:
            show_event_location = False

        if show_event_location and (item.portal_type == 'Event' or item.portal_type == 'TalkEvent'):
            if hasattr(item, 'short_location'):
                if isinstance(item, AbstractCatalogBrain):
                    if item.short_location:
                        return item.short_location
                elif item.short_location():
                    return item.short_location()
            elif item.location.strip():
                return item.location.strip()

        return None

    def substituteTitle(self, item, context):

        item_title = item.Title.strip()

        if 'courses' in context.Subject():
            course_title = '%s:' % context.Title().strip()
            if item_title.startswith(course_title):
                item_title = item_title.replace(course_title, '', 1).strip()

        return item_title

    def reorderTopicContents(self, topicContents, order_by_id=None, order_by_title=None, zip_code_input=None):

        try:
            ziptool = getToolByName(self.context, 'extension_zipcode_tool')
        except AttributeError:
            ziptool = None

        if ziptool and zip_code_input:

            def getDistance(z1, z2):
                return ziptool.getDistance(z1, z2,novalue=9999)

            topicContents = sorted([x for x in topicContents], key=lambda x: getDistance(getattr(x, 'zip_code', ''), zip_code_input))

            return topicContents

        elif order_by_id:

            def getId(item):
                if isinstance(item, AbstractCatalogBrain):
                    return item.getId
                else:
                    return item.getId()

            # The +1 applied to both outcomes is so that the index of 0 is not evaluated as false.
            return sorted(topicContents, key=lambda x: getId(x) in order_by_id and (order_by_id.index(getId(x)) + 1) or (len(order_by_id) + 1))

            # Reference code
            # The below is slightly faster than the above in cases where order_by_id <= ~5, but the above scales better.
            # I left it in as an explanation of what the above is doing.
            """
            ordered = []
            unordered = []

            # Grab all the unordered items
            for item in topicContents:
                if item.getId not in order_by_id:
                    unordered.append(item)

            # Grab the ordered items, in order
            for id in order_by_id:
                for item in topicContents:
                    if item.getId == id:
                        ordered.append(item)

            # Combine the two lists
            ordered.extend(unordered)

            return ordered
            """
        elif order_by_title:
            ordered = []
            uuids = {}

            def getConfig(item):
                if isinstance(item, AbstractCatalogBrain):
                    return item.UID
                else:
                    return item.UID()

            def getTitle(item):
                if isinstance(item, AbstractCatalogBrain):
                    return item.Title
                else:
                    return item.Title()

            for t in order_by_title:
                r = re.compile(t)

                # Pull out matching items
                for item in topicContents:
                    if not uuids.get(getConfig(item)) and r.search(getTitle(item)):
                        ordered.append(item)
                        uuids[getConfig(item)] = 1

            for item in topicContents:
                if not uuids.get(getConfig(item)):
                    ordered.append(item)
                    uuids[getConfig(item)] = 1

            return ordered
        else:
            return topicContents

    def toMarkdown(self, text):
        portal_transforms = getToolByName(self.context, 'portal_transforms')
        return portal_transforms.convert('markdown_to_html', text)

    def getUTM(self, source=None, medium=None, campaign=None, content=None):
        data = {}

        if source:
            data["utm_source"] = source

        if medium:
            data["utm_medium"] = medium

        if campaign:
            data["utm_campaign"] = campaign

        if content:
            data["utm_content"] = content

        return urlencode(data)

    def customBodyClass(self):
        context = aq_base(self.context)
        body_classes = []

        # Get object parent
        parent = self.context.getParentNode()

        # Check for two_column attribute
        if hasattr(context, 'two_column') and context.two_column:
            body_classes.append('custom-two-column')

        # Show text with only h2s with the h2s styled as h3s
        try:
            if hasattr(context, 'folder_text'):
                body_text = str(context.folder_text)
            elif hasattr(context, 'getText'):
                body_text = str(context.getText())
            else:
                body_text = ''
        except:
            body_text = ''

        if body_text and '<h2' in body_text.lower() and '<h3' not in body_text.lower():
            # Don't add this class on aliased courses.
            if not getattr(context, 'extension_course_single_event', 'normal') == 'alias':
                body_classes.append('custom-h2-as-h3')

        # If 'show_mobile_nav' property is set or
        # we're the homepage at the root of the site,
        # set class navigation-mobile

        try:
            # Explicitly enabled or is a homepage at the root of the site
            if getattr(self.context, 'show_mobile_nav', False) or (self.context.portal_type == 'HomePage' and parent.portal_type == 'Plone Site'):
                body_classes.append("navigation-mobile")
        except:
            pass

        # If we have a property of 'enable_subsite_nav' set on
        # ourself, or if we're the default page and have it set on our parent
        # object, add a class of 'navigation-subsite'
        try:
            parent_default = parent.getDefaultPage()
        except AttributeError:
            parent_default = ''

        try:
            # Explicitly enabled or is a homepage at the root of the site
            if context.getProperty('enable_subsite_nav', False) or self.context.getId() == parent_default and parent.getProperty('enable_subsite_nav', False):
                body_classes.append("navigation-subsite-root")
        except:
            pass

        # Is subsite navigation enabled?
        if getContextConfig(self.context, 'enable_subsite_nav'):
            body_classes.append("navigation-subsite")

        # Use the Penn State (as opposed to the college) header if main_site is set.
        if getContextConfig(self.context, 'main_site'):
            body_classes.append("penn-state-header")

        # Append custom classes
        if getContextConfig(self.context, 'custom_class'):
            body_classes.extend(['custom-%s' % str(x) for x in getContextConfig(self.context, 'custom_class').split()])

        # Set "empty-top-navigation" body class
        topMenu =  getContextConfig(self.context, 'top-menu', 'topnavigation')

        portal_actions = getToolByName(self.context, 'portal_actions')

        if not portal_actions.get(topMenu, None):
            body_classes.append('empty-top-navigation')

        # Contents below folder
        if getattr(context, "listing_after_text", False):
            body_classes.append('listing-after-text')

        # Contents below folder
        if getattr(context, "hide_breadcrumbs", False):
            body_classes.append('hide-breadcrumbs')
        
        # Panorama Image
        if getattr(context, 'portal_type', '') in ['HomePage']:
            image_format = getattr(context, "homepage_image_format", "standard")     
            body_classes.append('homepage-image-format-%s' % image_format)

            portlet_format = getattr(context, "homepage_portlet_format", "standard")     
            body_classes.append('homepage-portlet-format-%s' % portlet_format)
            
        return ' '.join(body_classes)

    def contentFilter(self):

        contentFilter = {}

        portal_catalog = getToolByName(self.context, "portal_catalog")
        indexes = portal_catalog.indexes()
        indexes.append('zip_code_input') # Because we're doing a calculation on it, not a raw search

        for k in self.request.form.keys():

            if k in indexes:

                # ZIP Code search
                if k == 'zip_code_input':

                    search_zip = self.request.form.get('zip_code_input')
                    search_zip_radius = self.request.form.get('zip_code_radius')

                    if not search_zip_radius:
                        search_zip_radius = 50 # Default radius

                    if search_zip and search_zip_radius:

                        try:
                            ziptool = getToolByName(self.context, 'extension_zipcode_tool')
                        except AttributeError:
                            pass
                        else:
                            # We have a ziptool
                            zips = ziptool.getNearbyZIPs(search_zip, search_zip_radius)
                            all_zips = portal_catalog.uniqueValuesFor('zip_code')
                            search_zip_list = list(set(zips) & set(all_zips))
                            search_zip_list.append('00000')
                            contentFilter['zip_code'] = search_zip_list
                elif k == 'Counties':
                    counties = self.request.form.get(k)

                    if counties:
                        if len(counties) == 1:
                            contentFilter[k] = getSurroundingCounties(counties[0])
                        else:
                            contentFilter[k] = counties
                else:
                    contentFilter[k] = self.request.form[k]

        return contentFilter

    def increaseHeadingLevel(self, text):
        return _increaseHeadingLevel(text)