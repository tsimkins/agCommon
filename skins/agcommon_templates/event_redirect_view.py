##title=Event Redirect View

"""
event_redirect_view
Redirect to the event's website target URL, if and only if:
 - A website entry exists
 - AND current user doesn't have permission to edit the event
"""

from Products.CMFCore.utils import getToolByName

mtool = getToolByName(context, 'portal_membership')

can_edit = mtool.checkPermission('Modify portal content', context)

try:
    redirectURL = context.eventUrl
except AttributeError:
    redirectURL = None

if redirectURL and not can_edit:
    # Send to the configured website
    return context.REQUEST.RESPONSE.redirect(redirectURL)
else:
    # event_view.pt is a template in the plone_content skin layer
    return context.event_view()

