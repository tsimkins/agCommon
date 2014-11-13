from Products.Five import BrowserView
from Products.agCommon import getPanoramaHomepageImage
from zope.interface import implements, Interface

class IJavaScriptView(Interface):
    pass

class JavaScriptView(BrowserView):

    implements(IJavaScriptView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

class TileHomepage(JavaScriptView):
    
    def __call__(self):

        RESPONSE =  self.request.RESPONSE
        RESPONSE.setHeader('Content-Type', 'application/x-javascript')
        RESPONSE.setHeader('Cache-Control', 'max-age=3600, s-maxage=3600, public, must-revalidate, proxy-revalidate')
        
        return getPanoramaHomepageImage(self.context, homepage_type="tile")