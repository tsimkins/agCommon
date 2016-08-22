from . import BaseView
from Products.CMFCore.utils import getToolByName

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