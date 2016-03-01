from . import NewsletterView as _NewsletterView
from . import NewsletterEmail as _NewsletterEmail


class NewsletterView(_NewsletterView):

    def getParentURL(self):
        parent = self.context.getParentNode()
        return parent.absolute_url()
    
class NewsletterEmail(_NewsletterEmail, NewsletterView):

    pass