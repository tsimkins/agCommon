try:
    import simplejson as json
except ImportError:
    import json

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.TinyMCE.browser.browser import TinyMCEBrowserView as View
from Products.TinyMCE.browser.interfaces.browser import ITinyMCEBrowserView
from zope.interface import implements
from zope.component.hooks import getSite

class TinyMCEBrowserView(View):
    implements(ITinyMCEBrowserView)

    def jsonConfiguration(self, field):
        """Return the configuration in JSON"""

        utility = getToolByName(aq_inner(self.context), 'portal_tinymce')
        config = utility.getConfiguration(context=self.context,
                                          field=field,
                                          request=self.request)
        config['convert_urls'] = True
        config['relative_urls'] = False
        config['remove_script_host'] = True
        
        return json.dumps(config)