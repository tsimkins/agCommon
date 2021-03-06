from plonetheme.sunburst.browser.interfaces import IThemeSpecific as ISunburstTheme
from zope.viewlet.interfaces import IViewletManager
from plone.app.portlets.interfaces import IColumn
from zope.interface import Interface

class IThemeSpecific(ISunburstTheme):
    """Marker interface that defines a Zope 3 skin layer bound to a Skin
       Selection in portal_skins.
       If you need to register a viewlet only for the "agCommon"
       skin, this is the interface that must be used for the layer attribute
       in agCommon/browser/configure.zcml.
    """

class IRightColumn(IColumn):
	"""A viewlet manager that sits inside the main content area and floats to the right
	"""
	
class IHomepageImage(IColumn):
	"""A viewlet manager where you can create the homepage image
	"""
	
class ICenterColumn(IColumn):
	"""A viewlet manager that sits inside the main content area.  Used for news on the front page
	"""

class ITableOfContents(Interface):
    """These are the content types that can have a table of contents
    """

class IContributors(Interface):
    """These are the content types that can have a contributors listing
    """

class IFSDShortBio(Interface):
    """Invisible magic switch to turn on the FSDPerson short bio behavior for a
       folder. Doing an interface instead of a checkbox, since it only needs to
       be used for half a dozen areas at most.

    """

class ICollegeHomepage(Interface):
    """
        Marker interface for the college homepage in order to return structured
        data for the college.
    """

class ISkipSection(Interface):
    """
        Marker interface where we want to 'skip' this item in the traversal to
        determine the 'section'.  This is used in cases where "section C within
        section B within section A" needs to have a section title of A, not B.

        Apply this interface to section B, and it will be skipped in the logic.
    """

class ISearchSection(Interface):
    """
        Specifies that this is the item to appear in the section search.
    """

try:

    from Products.CMFPlone.interfaces.syndication import ISyndicatable

except ImportError:

    class ISyndicatable(Interface):
        pass

# Sections of the site providing this interface have Inspectlet enabled.
class IInspectletEnabled(Interface):
    pass

# Marker interface to enable data table behavior.
class IDataTables(Interface):
    pass