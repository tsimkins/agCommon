from Products.Five import BrowserView
from Products.agCommon import getPanoramaHomepageImage
from zope.interface import implements, Interface
import templates

class ICSSView(Interface):
    pass

class CSSView(BrowserView):

    implements(ICSSView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

class TileHomepage(CSSView):
    
    total_width = templates.total_width()
    padding = templates.tile_homepage_padding
    max_blocks = 5
    max_items = 5

    def getBlockWidths(self, min_width=0):

        widths = []

        for i in range(1,self.max_blocks+1):
            for j in range(1,i+1):
                w = ((100.0*j)/i)
                if w >= min_width:
                    widths.append(w)
        
        return [('%d' % x, '%0.6f' % x, x/100) for x in sorted(list(set(widths)))]

    def getRSSImageCSS(self):

        css = []

        for (block_klass, block_css, block_percent) in self.getBlockWidths(min_width=50):
            css.append(templates.portlet_rss_image % {
                    'block_klass' : block_klass, 
                    })

        return css

    def getBlockCSS(self, mq=None):

        css = []

        for (block_klass, block_css, block_percent) in self.getBlockWidths():
        
            block_width = block_percent*self.total_width
            
            if mq in ('SMALLPHONE', 'BIGPHONE'):
                block_width = self.total_width
                block_css = '100'
                block_percent = 1
            
            content_width = block_width - (2*self.padding)
            content_width_percent = content_width/block_width
            content_margin_percent = self.padding/block_width            
        
            css.append(templates.portlet_block_css % {
                    'block_klass' : block_klass, 
                    'block_css' : block_css, 
                    'block_percent' : 100.0*block_percent,
                    'content_width_percent' : 100*content_width_percent,
                    'content_margin_percent' : 100*content_margin_percent,
                    })
            
            for n in range(1,self.max_items+1):
                css.extend(self.getItemCSS(n, block_percent, block_klass, mq=mq))

        return css

    def getItemCSS(self, n, block_percent, block_klass, mq=''):
        column_count = n

        if mq in ('TABLET'):
            if n >= 5:
                column_count = 3
            elif n == 4:
                column_count = 2
        elif mq in ('BIGPHONE', 'SMALLPHONE'):
            column_count = 1
            
        css = []
        
        block_width = block_percent*self.total_width
        total_padding = 2*column_count*self.padding
        content_width = (block_width - total_padding)/column_count
        content_width_percent = content_width/block_width
        padding_percent = self.padding/block_width

        css.append(templates.portlet_item_css % {'block_klass' : block_klass, 'n' : n, 'content_width_percent' : content_width_percent*100, 'padding_percent' : padding_percent*100, 'n_child' : column_count})
        
        return css

    
    def getContentWellPortletCSS(self):
    
        homepage_text_width = (self.total_width - 2*self.padding)/self.total_width
        homepage_text_padding = container_margin = self.padding/self.total_width
    
        return [templates.contentwellportlet_css % {'homepage_text_width' : 100*homepage_text_width, 'homepage_text_padding' : 100*homepage_text_padding, 'container_margin' : 100*container_margin}]

    def getPortletCSS(self):
        return [templates.portlet_css]

    def getMediaQuery(self, max_width=None, min_width=None):
        if max_width and min_width:
            return """
                @media handheld, screen and (max-width: %dpx) and (min-width: %dpx) {
                    %%s
                }
            """ % (max_width, min_width)
        elif max_width:
            return """
                @media handheld, screen and (max-width: %dpx) {
                    %%s
                }
            """ % (max_width)
        elif min_width:
            return """
                @media handheld, screen and (min-width: %dpx) {
                    %%s
                }
            """ % (min_width)
        else:
            return '%s'

    def __call__(self):

        RESPONSE =  self.request.RESPONSE
        RESPONSE.setHeader('Content-Type', 'text/css')
        RESPONSE.setHeader('Cache-Control', 'max-age=3600, s-maxage=3600, public, must-revalidate, proxy-revalidate')
        
        css = []
        css.extend(self.getPortletCSS())
        css.extend(self.getContentWellPortletCSS())
        css.extend(self.getRSSImageCSS())

        mq_list = [
                ('DESKTOP', self.getMediaQuery(min_width=769)),
                ('TABLET', self.getMediaQuery(max_width=768)),
                ('BIGPHONE', self.getMediaQuery(max_width=520)),
                ('SMALLPHONE', self.getMediaQuery(max_width=480)),
        ]
        
        for (mq, mq_format) in mq_list:
            css.append(mq_format % "\n".join(self.getBlockCSS(mq=mq)))

        return """
        /* Automagically generated tile homepage css */
        %s
        """ % ("\n".join(css))