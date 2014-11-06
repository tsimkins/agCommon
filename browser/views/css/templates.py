# CSS Template variables

from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
import re

# Properties

tile_homepage_padding = 15.0

def total_width():
    return 899.0
    default_width = 1000.0
    site = getSite()
    try:
        portal_skins = getToolByName(site, 'portal_skins')
    except AttributeError:
        return default_width

    try:
        base_properties = portal_skins.restrictedTraverse('agcommon_styles/base_properties')
    except KeyError:
        return default_width

    width = base_properties.getProperty('maxWidth', '')

    if not width:
        return default_width

    width = re.sub('[A-Za-z]+', '', width)

    try:
        return float(width)
    except ValueError:
        return default_width


# Tile Homepage CSS templates

portlet_rss_image = """

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .rssImage {
    width: 33.333333333333333%%;
    float: right;
    margin: 0 0 0.125em 0.888888888888889%%;
    padding: 0;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .portletfeedmixerimageleft .rssImage {
    width: 33.333333333333333%%;
    float: left;
    margin: 0;
    padding: 0;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .portletfeedmixerimagelarge .rssImage {
    width: auto;
    float: none;
    margin: 0;
    padding: 0;
    margin-bottom: 0.25em;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .portletfeedmixerimageleft .title,
#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .portletfeedmixerimageleft .portletItemDetails {
    margin-left: 35%%;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .portletfeedmixerimagelarge .title,
#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-1 .portletfeedmixerimagelarge .portletItemDetails {
    margin-left: 0;
}

"""

portlet_block_css = """
        
#content .tilePortletContainer .portlet-width-%(block_klass)s {
    width: %(block_percent)0.6f%%;
    float: left;
    padding: 0;
    margin: 0;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s .portletHeader,
#content .tilePortletContainer .portlet-width-%(block_klass)s .portletFooter,
#content .tilePortletContainer .portlet-width-%(block_klass)s img.feedmixerCollectionLeadImage {
    width: %(content_width_percent)0.6f%%;
    margin-left: %(content_margin_percent)0.6f%%;
    margin-right: %(content_margin_percent)0.6f%%;    
    display: block;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s .portletFooter {
    clear: both;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s img.feedmixerCollectionLeadImage {
    padding: 0;
    height: auto;
    margin-top: 1em;
    margin-bottom: -0.5em;
}

"""

portlet_item_css = """

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-%(n)s .portletItem {
    width: %(content_width_percent)0.6f%%;
    margin-left: %(padding_percent)0.6f%%;
    margin-right: %(padding_percent)0.6f%%;
    float: left;
}

#content .tilePortletContainer .portlet-width-%(block_klass)s.portlet-item-count-%(n)s .portletItem:nth-child(%(n_child)sn + 1) {
    clear: left;
}
"""

contentwellportlet_css = """
#content .tilePortletContainer .navTreeItem a:hover, 
#content .tilePortletContainer dd.portletItem .navTreeItem a:hover {
    background-color: transparent;
}

#content .tilePortletContainer .navTreeItem a, 
#content .tilePortletContainer dd.portletItem .navTreeItem a {
    padding: 0;
}

#content .tilePortletContainer {
    display: block;
    margin-left: -%(container_margin)0.6f%%;
    margin-right: -%(container_margin)0.6f%%;
}

#portal-column-content.sl #content .tilePortletContainer .agCommonPortlet .portletHeader {
    font-size: 1.25em;
}

#portal-column-content.sl #content .tilePortletContainer .agCommonPortlet .portletItem {
    margin-bottom: 0.875em;
}

div.tilePortletManager {
    float: none;
    clear: both;
    width: 100%%;
    margin: 0;
    padding: 0;
}

"""

portlet_css = """
#content .tilePortletContainer .portlet {
    margin-bottom: 0.375em;
}

#content .tilePortletContainer .portlet img {
    max-width: 100%;
    width: 100%;
    height: auto;
}

#content .tilePortletContainer .rssImage {
    margin-bottom: 0.25em;
}

"""
