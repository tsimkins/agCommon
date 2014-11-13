from zope.schema.interfaces import IVocabularyFactory
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from Products.CMFPlone import PloneMessageFactory as _

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

from Products.CMFCore.utils import getToolByName

class PortalActionsVocabulary(object):
    """Vocabulary factory for cache timeouts.
    """
    implements(IVocabularyFactory)

    def __call__(self, context):

        plone_actions = ['document_actions',
                         'site_actions',
                         'folder_buttons',
                         'object',
                         'object_buttons',
                         'portal_tabs',
                         'user',
                         'topnavigation']
    
        portal_actions = getToolByName(context, 'portal_actions')
        
        terms = [SimpleTerm(None, title=_(u"Choose an id..."))]
        
        for term in sorted(portal_actions.keys()):
            if not plone_actions.count(term):
                terms.append(SimpleTerm(term, title=_(term)))

        return SimpleVocabulary(terms)

PortalActionsVocabularyFactory = PortalActionsVocabulary()

