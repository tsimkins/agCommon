##title=News Item Redirect View

"""
newsitem_redirect_view
Redirect to the News Item's website target URL, if and only if:
 - A website entry exists
 - AND current user doesn't have permission to edit the News Item
"""

from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter

mtool = getToolByName(context, 'portal_membership')

can_edit = mtool.checkPermission('Modify portal content', context)

try:
    redirectURL = context.article_link
except AttributeError:
    redirectURL = None

if redirectURL and not can_edit:
    # Send to the configured website
    return context.REQUEST.RESPONSE.redirect(redirectURL)
else:
    # newsitem_view.pt is a template in the plone_content skin layer
    request = container.REQUEST
    RESPONSE =  request.RESPONSE

    portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
    anonymous = portal_state.anonymous()    
    
    if not anonymous:
        RESPONSE.setHeader('Cache-Control', 'max-age=0, must-revalidate, private')
    else:
        RESPONSE.setHeader('Cache-Control', 'max-age=0, s-maxage=86400, must-revalidate, public, proxy-revalidate')

    return context.newsitem_view()
