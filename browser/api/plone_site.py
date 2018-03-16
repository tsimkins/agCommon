from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite
from Products.agCommon import execute_under_special_role
            
import requests
from . import BaseView

class PloneSiteView(BaseView):

    def getData(self, recursive=True):

        uid = self.request.get('UID', None)

        if uid:
            portal_catalog = getToolByName(self.context, 'portal_catalog')
            results = portal_catalog.searchResults({'UID' : uid})
            if results:
                o = results[0].getObject()
                return o.restrictedTraverse('@@api-json').getData()

        return {}

class MagentoProductRedirectsView(BaseView):

    # Bypass all filtering.  This is raw output. Also, cheat and run this as 
    # a Manager
    def getFilteredData(self, recursive=True):
        return execute_under_special_role(['Manager'], self.getData)

    def getData(self, recursive=True):

        site = getSite()

        data = []

        cms_url = 'http://cms.extension.psu.edu/@@original-plone-ids'

        response = requests.get(cms_url).json()

        lookup = dict([(x.get('plone_id'), x.get('target')) for x in response])

        uids = lookup.keys()

        results = self.portal_catalog.searchResults({'UID' : uids})

        for r in results:

            url = r.getURL()[len(site.absolute_url()):]
            target = lookup.get(r.UID)

            review_state = r.review_state
            
            if not review_state:
                review_state = None
            
            data.append({
                'source' : url,
                'target' : target,
                'review_state' : review_state,
            })

        return data
