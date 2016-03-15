from . import NewsletterView as _NewsletterView
from . import NewsletterEmail as _NewsletterEmail


class NewsletterView(_NewsletterView):

    def getParentURL(self):
        
        parent = self.context.getParentNode()

        return getattr(self.context.aq_base, 'more_url', parent.absolute_url())

    
class NewsletterEmail(_NewsletterEmail, NewsletterView):

    pass