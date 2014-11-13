##title=Person Alias View

"""
person_redirect_view
Redirect to the person's website target URL, if and only if:
 - A website entry exists
 - AND current user doesn't have permission to edit the Person
"""

from Products.CMFCore.utils import getToolByName

mtool = getToolByName(context, 'portal_membership')

can_edit = mtool.checkPermission('Modify portal content', context)

try:
    redirectURL = context.primary_profile
except AttributeError:
    redirectURL = None

if redirectURL and not can_edit:
    # Send to the configured website
    return context.REQUEST.RESPONSE.redirect(redirectURL)
else:
    # person_view.pt is a template in the plone_content skin layer
    return context.person_view()