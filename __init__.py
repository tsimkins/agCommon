# Register our skins directory - this makes it available via portal_skins.

from zope.component import getSiteManager
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import registerDirectory
from Products.PythonScripts.Utility import allow_module
from zope.component.interfaces import ComponentLookupError
from Products.CMFCore.WorkflowCore import WorkflowException
from subprocess import Popen,PIPE
from zLOG import LOG, INFO, ERROR
from zope.component import getUtility
from Acquisition import aq_inner, aq_chain
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.i18n.normalizer import FILENAME_REGEX
from collective.contentleadimage.config import IMAGE_FIELD_NAME
from Products.Archetypes.Field import ImageField
from Products.Archetypes.Field import HAS_PIL
from agsci.w3c.colors import split_rgb
from DateTime import DateTime
from datetime import datetime, tzinfo
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from zope.interface import alsoProvides
from zope.component.hooks import getSite
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager
from AccessControl.User import UnrestrictedUser as BaseUnrestrictedUser

import colorsys
import os
import pytz
import re

from Products.Five.utilities.interfaces import IMarkerInterfaces
from agsci.UniversalExtender.interfaces import IUniversalPublicationExtender, IFilePublicationExtender, ITileFolder, IVideoPage, IVideoPlaylist

MAX_HOMEPAGE_IMAGE_WIDTH = 950.0
MAX_HOMEPAGE_IMAGE_HEIGHT = 360.0

ATTEMPTS = 100

GLOBALS = globals()
registerDirectory('skins', GLOBALS)

default_search_destination='site'

def getDefaultSearchDestination(context=None):
    if context:
        if getContextConfig(context, 'show_college_search', False):
            default = 'college'
    
        elif getContextConfig(context, 'show_section_search', False):
            default = 'section'

    return default_search_destination


def getSearchConfig(context=None, path='', q='', section_title=None, site_title=None):

    default=getDefaultSearchDestination(context)

    searches = [
                    {
                        'key' : 'college',
                        'url' :  'http://cse.google.com/cse?cx=009987215249396987893:cmobqlykeyk&q=%s' % q,
                        'description' : 'Search The College'
                    },
                    {
                        'key' : 'site',
                        'url' :  'search?SearchableText=%s' % q,
                        'description' : 'Search This Site'
                    },
                    {
                        'key' : 'section',
                        'url' :  'search?SearchableText=%s&path=%s' % (q, path),
                        'description' : 'Search This Section'
                    },
                    {
                        'key' : 'psu-web',
                        'url' :  'http://www.psu.edu/search/gss?query=%s' % q,
                        'description' : 'Search Penn State'
                    },
                    {
                        'key' : 'psu-people',
                        'url' :  'http://www.psu.edu/cgi-bin/ldap/ldap_query.cgi?cn=%s' % q,
                        'description' : 'Search Penn State People'
                    },
                    {
                        'key' : 'psu-dept',
                        'url' :  'http://www.psu.edu/cgi-bin/ldap/dept_query.cgi?dept_name=%s' % q,
                        'description' : 'Search Penn State Departments'
                    },
                ]

    # Dynamically add attributes
    for i in searches:
        key = i.get('key', '')
        
        # If it's the default search engine, add a attribute of selected=True
        i['selected'] = (key == default)
        
        # If there's no path (i.e. not a section) and it's the section search engine,
        # add an attribute of disabled=True
        i['disabled'] = (key == 'section' and not path)
        
        # Override site and section title if provided.
        if key == 'site' and site_title:
            i['description'] = 'Search %s' % site_title
        elif key == 'section' and section_title:
            i['description'] = 'Search %s' % section_title
        
    return searches

def getSearchEngineURL(choice=default_search_destination, path='', q=''):
    searches = getSearchConfig(path=path, q=q)
    
    search_engine_data = dict([(x.get('key', None), x) for x in searches])
    
    search_engine = search_engine_data.get(choice, search_engine_data.get(default_search_destination, {}))
    
    return search_engine.get('url', '')
    

# Allow us to use this module in scripts

allow_module('Products.agCommon')
allow_module('feedparser')
allow_module('premailer')
allow_module('datetime')
allow_module('datetime.datetime')
allow_module('Products.feedSync')
allow_module('Products.feedSync.sync')
allow_module('Products.feedSync.cvent')
allow_module('Products.feedSync.cvent.api')
allow_module('Products.feedSync.tags')
allow_module('Products.feedSync.cvent.importEvents')
allow_module('Products.CMFCore.utils')
allow_module('Products.CMFCore.utils.getToolByName')
allow_module('urllib2')
allow_module('urllib')
allow_module('zope.component')
allow_module('zope.component.getSiteManager')
allow_module('csv')

allow_module('Products.ZCatalog.Lazy')
allow_module('Products.GlobalModules')
allow_module('Products.GlobalModules.makeHomePage')
allow_module('Products.GlobalModules.makePhotoFolder')
allow_module('Products.GlobalModules.fixPhoneNumber')

allow_module('ZODB.POSException')
allow_module('ZODB.POSException.POSKeyError')

allow_module('re')
allow_module('re.sub')
allow_module('re.compile')
allow_module('re.search')
allow_module('re.match')
allow_module('re.I')
allow_module('re.M')

# Precompile phoneRegex
phoneRegex = re.compile("^\s*(?:1[\.\- ]*)*\(*(\d{3})\)*[\.\- ]*(\d{3})[\.\- ]*(\d{4})\s*$")

#Ploneify
def ploneify(toPlone, isFile=False):
    if not isFile:
        ploneString = re.sub("[^A-Za-z0-9]+", "-", toPlone).lower()
    else:
        ploneString = re.sub("[^A-Za-z0-9\.]+", "-", toPlone).lower()
    ploneString = re.sub("-$", "", ploneString)
    ploneString = re.sub("^-", "", ploneString)
    return ploneString


# auto-calculate gradient - returns a darker, more saturated version of the color
def calculateGradient(startColor):
    def toHex(dec):
        return str('%X' % int(dec)).zfill(2)

    def vdiff(v):
        if v > 0.8:
            return 0.9
        elif v < 0.2:
            return 0.5
        else:
            return 0.75

    (r,g,b) = [x/255.0 for x in split_rgb(startColor)]
    (h,s,v) = colorsys.rgb_to_hsv(r,g,b)
    (r_new, g_new, b_new) = [toHex(255*x) for x in colorsys.hsv_to_rgb(h,min(1, 1.2*s),vdiff(v)*v)]

    return '%s%s%s' % (r_new, g_new, b_new)


# auto-calculate gradient color for r/g/b
def calculateGradientColor(color, c):

    def subtract_percent(s, p=20):
    
        if p > 100:
            p=100
            
        if p < 0:
            p=0
    
        dec = s * (100-p)/100
        return str('%X' % int(dec)).zfill(2)

    d = split_rgb(color)

    v = d[c]
    
    v_percent = float(sum(d.values()))/(3*255)

    v_modify = 1

    if v_percent >= .6 or v_percent <= .3:
        v_modify = .8

    if v == min(d.values()):
        return subtract_percent(v, 70*v_modify)
    elif v == max(d.values()):
        return subtract_percent(v, 20*v_modify)
    else:
        return subtract_percent(v, 50*v_modify)


# Given start and end colors (optionally width and height) returns a gradient png

def gradientBackground(request):
    
    startColor = request.form.get("startColor", 'FFFFFF')
    endColor = request.form.get("endColor")
    orientation = request.form.get("orientation", 'v').lower()[0]
    
    try:
        height = str(int(request.form.get("height", '600')))
    except ValueError:
        height = '600';

    try:
        width = str(int(request.form.get("width", '1')))
    except ValueError:
        width = '1';
    
    # Validate we have a color code
    colorRegex = "^[0-9A-Fa-f]{3,6}$"
    
    if not re.match(colorRegex, startColor):
        startColor = 'FFFFFF'

    def sum_colors(d):
        return sum(d.values())
    
    if not endColor or not re.match(colorRegex, endColor):
        endColor = calculateGradient(startColor)

    if orientation == 'h': 
        png = Popen(['convert', '-size', '%sx%s'%(height, width), 'gradient:#%s-#%s'%(str(startColor), str(endColor)), '-rotate', '270', 'png:-'], stdout=PIPE)
    else:
        png = Popen(['convert', '-size', '%sx%s'%(width, height), 'gradient:#%s-#%s'%(str(startColor), str(endColor)), 'png:-'], stdout=PIPE)

    return "".join(png.stdout.readlines())

# Legacy method that is no longer used.
def bodyBackground(context, request):
    return None    
    
# Given a context, gets a list of all images and returns a JavaScript snippet
# that randomly picks one of them.

def getHomepageImage(context, maxWidth=MAX_HOMEPAGE_IMAGE_WIDTH, maxHeight=MAX_HOMEPAGE_IMAGE_HEIGHT):

    (backgrounds, backgroundHeights) = getBackgroundImages(context)
    
    if not len(backgrounds):
        backgrounds = ['homepage_placeholder.jpg']
        backgroundHeights = ['%d' % maxHeight]
    
    return """

    var homepageBackgroundHeight = 0;
    var maxHomepageImageWidth = %d;

    function setHomepageImage() {
        homepageImage = jq("body.template-document_homepage_view #homepageimage");
        breadcrumbs = jq("body.template-document_homepage_view #portal-breadcrumbs");
        if (homepageImage.length)
        {
            var backgrounds = "%s".split(";");
            var backgroundHeights = "%s".split(";");
            var randomnumber = Math.floor(Math.random()*backgrounds.length);

            homepageBackgroundHeight = backgroundHeights[randomnumber];

            homepageImage.css('background-image', "url(" + backgrounds[randomnumber] + ")");
            homepageImage.css("height", backgroundHeights[randomnumber] + 'px');

            homepageImage.addClass("image");

            scaleHomepageImage();
            
        }
    }

    function scaleHomepageImage() {
        var homepageImage = jq("#homepageimage");

        if (homepageImage)
        {
            var ratio = homepageImage.width()/maxHomepageImageWidth; // Homepage image ratio
            var newHeight = ratio*homepageBackgroundHeight;
            homepageImage.css("height", newHeight + 'px');
        }
        
    }

    jq(document).ready(
        function () {
            setHomepageImage();
        }
    );
    
    jq(window).resize(
        function () {
            scaleHomepageImage();
        }
    );

    """ % (maxWidth, ";".join(backgrounds), ";".join(backgroundHeights))

def getPortletHomepageImage(context, homepage_type="portlet"):
    return getPanoramaHomepageImage(context, homepage_type="portlet")

def getPanoramaHomepageImage(context, homepage_type="document"):

    (backgrounds, backgroundHeights) = getBackgroundImages(context, maxHeight=250)
    
    if len(backgrounds):
    
        return """
    jq(document).ready(
        function () {
            portalColumns = jq("body.template-%(homepage_type)s_homepage_view #portal-columns");
            visualPortalWrapper = jq("body.template-%(homepage_type)s_homepage_view #visual-portal-wrapper");
            breadcrumbs = jq("body.template-%(homepage_type)s_homepage_view #portal-breadcrumbs");
            
            if (portalColumns && visualPortalWrapper)
            {
                var backgrounds = "%(backgrounds)s".split(";");
                var backgroundHeights = "%(heights)s".split(";");
                var randomnumber = Math.floor(Math.random()*backgrounds.length) ;

                if (backgrounds.length) 
                {
                    var homepageImage = jq('<div id="panorama-homepage-image"><!-- --></div>');
                                    
                    homepageImage.insertBefore(portalColumns);
                    
                    homepageImage.css("backgroundImage", "url(" + backgrounds[randomnumber] + ")");
                    homepageImage.css("paddingTop", backgroundHeights[randomnumber] + 'px');
            
                    if (breadcrumbs.length)
                    {
                        breadcrumbs.detach();
                        breadcrumbs.insertBefore(homepageImage);
                        breadcrumbs.addClass("homepage");
                    }
                    else
                    {
                        homepageImage.addClass("nobreadcrumbs");
                    }
                }
            }
        }
    );
    """ % {'homepage_type' : homepage_type, 'backgrounds' :  ";".join(backgrounds), 'heights' : ";".join(backgroundHeights)}

def getSubsiteHomepageImage(context):
    return getHomepageImage(context)


def getBackgroundImages(context, 
                        maxWidth=MAX_HOMEPAGE_IMAGE_WIDTH, 
                        maxHeight=MAX_HOMEPAGE_IMAGE_HEIGHT):
    backgrounds = []
    backgroundHeights = []
    
    for myImage in context.listFolderContents(contentFilter={"portal_type" : "Image"}):
        backgrounds.append(myImage.absolute_url())

        # Initial scale for image to fit.  Note this is opposite of the dynamic calculation    
        ratio = maxWidth/myImage.getWidth()  
        
        imageHeight = myImage.getHeight()*ratio
        
        if imageHeight > maxHeight:
            imageHeight = maxHeight
    
        backgroundHeights.append('%d' % imageHeight)
        
    return (backgrounds, backgroundHeights)

def makePage(context):
    print context.portal_type
    print context.archetype_name
    context.archetype_name = 'Page'
    context.portal_type = 'Document'
    context.setLayout("document_view")
    context.reindexObject()
    print context.portal_type
    print context.archetype_name
    print "OK"

def makeHomePage(context):
    print context.portal_type
    print context.archetype_name
    context.archetype_name = 'Home Page'
    context.portal_type = 'HomePage'
    context.setLayout("document_homepage_view")
    context.reindexObject()
    print context.portal_type
    print context.archetype_name
    print "OK"

def makePhotoFolder(context):
    print context.portal_type
    print context.archetype_name
    context.archetype_name = 'Photo Folder'
    context.portal_type = 'PhotoFolder'
    context.reindexObject()
    print context.portal_type
    print context.archetype_name
    print "OK"

def findEmptyFolders(context, daysback=183):

    # Finds published empty folders that have were published more than [daysback] days ago.
    # default for daysback is 6 months.  Ignores year folders.

    data = []
    
    portal_catalog = getToolByName(context, "portal_catalog")

    results = portal_catalog.searchResults({'portal_type' : 'Folder', 'review_state' : 'published', 'effective' : {'query': [DateTime() - daysback,], 'range' : 'max'} })

    for r in results:
        if r.id in [str(x) for x in range(1950,2100)] or r.id in ['news', 'events', 'images', 'background-images', 'files']:
            continue
        o = r.getObject()
        if not o.listFolderContents():
            data.append(o)

    return data



def folderToPage(folder):
    # Title, Description, Body Text, Author, Tags, Effective Date, Lead Image, Lead Image Caption
    wftool = getToolByName(folder, "portal_workflow")
    
    folder_id = folder.id
    folder_title = folder.Title()
    folder_description = folder.Description()
    folder_text = folder.folder_text()
    folder_creator = folder.getRawCreators()
    folder_contributors = folder.getRawContributors()
    folder_subject = folder.Subject()
    folder_effective_date = folder.effective()
    folder_excludeFromNav = folder.getExcludeFromNav()
    
    leadImage = folder.getField('leadImage', None).get(folder);
    leadImage_caption = folder.getField('leadImage_caption', None).get(folder);

    if wftool.getInfoFor(folder, 'review_state') != 'private':
        wftool.doActionFor(folder, 'retract')

    folder_parent = folder.getParentNode()
    


    # Backup as [parent UUID]___[folder id].zexp
    folder_parent.manage_exportObject(id=folder_id, download=False)
    
    try:
        UID = folder_parent.UID()
    except AttributeError:
        UID="0"*len(folder.UID())
    
    zope_dir = "/usr/local/plone/zeocluster/var"
    
    exported_ok = False
    
    for c in range(1,4):
        export_dir = "%s/client%d" % (zope_dir, c)
        old_filename = '%s.zexp' % folder_id
        new_filename = '%s___%s.zexp' % (UID, folder_id)
        if old_filename in os.listdir(export_dir):
            os.rename('%s/%s' % (export_dir, old_filename), '%s/%s' % (export_dir, new_filename))
            exported_ok = True

    if exported_ok:
        try:
            folder_parent.manage_delObjects(ids=[folder_id])
        except LinkIntegrityNotificationException:
            pass

    else:
        folder_parent.manage_renameObject(folder_id, '%s-converted-folder' % folder_id)    
    
    folder_parent.invokeFactory(id=folder_id, type_name="Document", title=folder_title, description = folder_description, text=folder_text, subject=folder_subject)
    
    page = getattr(folder_parent, folder_id)
    page.setCreators(folder_creator)
    page.setContributors(folder_contributors)
    
    page.setEffectiveDate(folder_effective_date)
    
    if leadImage:
        page_leadImage_field = page.getField('leadImage', None);
        page_leadImage_field.set(page, leadImage)

    if leadImage_caption:
        page_leadImage_caption_field = page.getField('leadImage_caption', None);
        page_leadImage_caption_field.set(page, leadImage_caption)

    if folder_excludeFromNav:
        page.setExcludeFromNav(True)

    if wftool.getInfoFor(page, 'review_state') != 'published':
        wftool.doActionFor(page, 'publish')

    page.reindexObject()
    
   
def pageToFolder(page):
    # Title, Description, Body Text, Author, Tags, Effective Date

    portal = getSiteManager(page)
    wftool = getToolByName(portal, "portal_workflow")
    
    page_id = page.id
    page_title = page.Title()
    page_description = page.Description()
    page_text = page.getText()
    page_owner = page.getOwner()
    page_subject = page.Subject()
    page_effective_date = page.EffectiveDate()

    if wftool.getInfoFor(page, 'review_state') != 'private':
        wftool.doActionFor(page, 'retract')
    
    page_parent = page.getParentNode()
    
    page_parent.manage_renameObject(page_id, '%s-page' % page_id)

    page_parent.invokeFactory(id=page_id, type_name="Folder", title=page_title, description = page_description, folder_text=page_text, subject=page_subject)
    
    folder = getattr(page_parent, page_id)
        
    folder.changeOwnership(page_owner)
    
    folder.setEffectiveDate(page_effective_date)

    if wftool.getInfoFor(folder, 'review_state') != 'published':
        wftool.doActionFor(folder, 'publish')

    folder.reindexObject()
    
def scrubPhone(i, return_original=True):
    match = phoneRegex.match(i)
    
    if match:
        return "-".join(match.groups())
    elif return_original:
        return i
    else:
        return ''


def fixPhoneNumber(myPerson):

    phone = myPerson.getOfficePhone()
    newPhone = scrubPhone(phone)

    if newPhone != phone:
        myPerson.setOfficePhone(newPhone)
        myPerson.reindexObject()
        return "%s: from %s to %s" % (myPerson.id, phone, newPhone)
    else:
        return "%s: Phone OK" % myPerson.id

# Intended to be used at the site root.  Returns a list of Plone sites.
def getPloneSites(context, recursive=True):

    ploneSites = []

    for myKey in context.keys():
        myChild = getattr(context, myKey)

        try:
            myType = myChild.meta_type

        except AttributeError:
           pass

        else:
           if myType == 'Plone Site':
               ploneSites.append(myChild)
           elif recursive and myType == 'Folder':
               ploneSites.extend(getPloneSites(myChild, recursive=False))

    return ploneSites
    
# Reinstall agCommon and agCommonPolicy on Plone sites
def reinstallAgCommon(site):

    toInstall = [
            'agCommon', 'agCommonPolicy', 
    ]

  
    LOG('agCommon.reinstallAgCommon', INFO,  "-"*50  )  
    LOG('agCommon.reinstallAgCommon', INFO,  "Starting reinstall on %s" % site  )  
    LOG('agCommon.reinstallAgCommon', INFO,  "-"*50  )  
        
    try:
        qi = getToolByName(site, 'portal_quickinstaller')
    except AttributeError:
        LOG('agCommon.reinstallAgCommon', ERROR,  "AttributeError for portal_quickinstaller" )
        return False
        
    toReinstall = []

    for product in toInstall:
    
        LOG('agCommon.reinstallAgCommon', INFO, "Attempting to install %s on site %s" % (product, site.get('id', 'Unknown')))
    
        if not qi.isProductInstalled(product):
            if qi.isProductInstallable(product):
                try:
                    qi.installProduct(product)
                    LOG('agCommon.reinstallAgCommon', INFO,  "Installed product %s" % product)
                except WorkflowException, e:
                    LOG('agCommon.reinstallAgCommon', ERROR,  "WorkflowException: (Workflow is in single state).  This causes an error: %s" % e)
                except ComponentLookupError, e:
                    LOG('agCommon.reinstallAgCommon', ERROR,  "ComponentLookupError: %s" % e)
            else:
                LOG('agCommon.reinstallAgCommon', INFO,  "Product %s not installable" % product)
        else:
            LOG('agCommon.reinstallAgCommon', INFO,  "Product %s already installed -- Must reinstall." % product  )
            toReinstall.append(product)  

    try:
        qi.reinstallProducts(toReinstall)
        LOG('agCommon.reinstallAgCommon', INFO,  "Reinstalling products [%s]" % ", ".join(toReinstall)  )
    except ComponentLookupError, e:
        LOG('agCommon.reinstallAgCommon', ERROR,  "ComponentLookupError: %s" % e  )


def sortFolder(context):
    folderContents = context.listFolderContents()
    for obj in sorted(folderContents, key=lambda x: x.Title().lower(), reverse=True):
        context.moveObjectsToTop(ids=[obj.id])
    for obj in folderContents:
        obj.reindexObject()
        


# Replace from_tag with new_tag
def replaceTag(context, from_tag, to_tag):

    catalog = getToolByName(context, 'portal_catalog')
    results = catalog.searchResults({'Subject' : from_tag})
    items = [x.getObject() for x in catalog.searchResults({'Subject' : from_tag})]
    
    for item in items:
    
        tags = list(item.Subject())
       
        while tags.count(from_tag):
            tags.remove(from_tag)

        if not tags.count(to_tag):
            tags.append(to_tag)
    
        item.setSubject(tags)
        item.reindexObject()
            
    topics = [x.getObject() for x in catalog.searchResults({'portal_type' : 'Topic'})]
    
    for t in topics:
        for o in t.objectIds():
            if o.count('Subject'):
                
                tags = list(t[o].value)

                if from_tag in tags:
                    
                    while tags.count(from_tag):
                        tags.remove(from_tag)
            
                    if not tags.count(to_tag):
                        tags.append(to_tag)
                        
                    t[o].setValue(tuple(tags))
                    t[o].reindexObject()

# Stolen from plone.app.content.namechooser because the "check_id" in portal_skins/plone_scripts
# isn't picking up the duplicates.
def findUniqueId(context, name):
    """Find a unique name in the parent folder, based on the given id, by
    appending -n, where n is a number greater than 1, or just the id if
    it's ok.
    """
    parent = aq_inner(context)
    parent_ids = parent.objectIds()
    check_id = lambda id: id in parent_ids

    if not check_id(name):
        return name

    ext  = ''
    m = FILENAME_REGEX.match(name)
    if m is not None:
        name = m.groups()[0]
        ext  = '.' + m.groups()[1]

    idx = 1
    while idx <= ATTEMPTS:
        new_name = "%s-%d%s" % (name, idx, ext)
        if not check_id(new_name):
            return new_name
        idx += 1

    raise ValueError("Cannot find a unique name based on %s after %d attemps." % (name, ATTEMPTS,))

def cleverInvokeFactory(context, **kwargs):

    item_title = kwargs['title']
    normalizer = getUtility(IIDNormalizer)
    item_id = normalizer.normalize(item_title)
    item_id = findUniqueId(context, item_id)
    return context.invokeFactory(id=item_id, **kwargs)

def calculateDimensions(imageObj, max_size=(1200,900)):

    if imageObj.width > max_size[0] or imageObj.height > max_size[1]:

        factor = min(float(max_size[0])/float(imageObj.width),
                        float(max_size[1])/float(imageObj.height))

        w = int(factor*imageObj.width)
        h = int(factor*imageObj.height)
        return(w,h)

    else:
        return (imageObj.width, imageObj.height)



def rescaleOriginal(context, max_size=(1200,900), dry_run=True):

    """
    Steps:
        * If Image, use own data --or--
        * If News Item, use image field --or--
        * Use leadImage field
        * Determine if it's greater than max dimensions (size)
        * If yes, scale it down and reset
    """
    if not HAS_PIL:
        return False

    portal_type = context.portal_type

    if portal_type == 'Image':
        imageObj = context
        imageField = ImageField()

    else:

        if portal_type == 'News Item':
            imageField = context.getField('image')
        else:
            imageField = context.getField(IMAGE_FIELD_NAME)

        imageObj = imageField.get(context)
        
    if not imageObj:
        status = False
        width = height = 0
        new_dimensions = (0,0)
    elif imageObj.content_type not in ('image/jpeg', 'image/png', 'image/gif'):
        status = False
        width = height = 0
        new_dimensions = (0,0)
        LOG('Products.agCommon.rescaleOriginal', INFO, "Invalid image type %s for %s" % (imageObj.content_type, context.absolute_url()) )
    else:

        width = imageObj.width
        height = imageObj.height
        
        new_dimensions = calculateDimensions(imageObj, max_size=max_size)
        
        if (width, height) > new_dimensions:
            if not dry_run:
                if isinstance(imageObj.data, str):
                    imageData = imageObj.data
                else:
                    imageData = imageObj.data.data

                (resizedImage, format) = imageField.scale(imageData, *new_dimensions)

                if portal_type == 'Image':
                    context.setImage(resizedImage.read())
            
                else:
                    imageField.set(context, resizedImage.read())

            status = True

        else:
            status = False

    return (status, portal_type, context.absolute_url(), (width, height), new_dimensions)
     
def findOversizedImages(context,  dry_run=True):
    
    rv = []
    
    portal_catalog = getToolByName(context, 'portal_catalog')
    
    results = [x for x in portal_catalog.searchResults({'hasContentLeadImage' : True})]
    results.extend([x for x in portal_catalog.searchResults({'portal_type' : ['News Item', 'Image']})])
    
    for r in results:
        obj = r.getObject()
        try:
            if obj.portal_type == 'Image':
                rr = rescaleOriginal(obj, max_size=(1200,1200), dry_run=dry_run)
            else:
                rr = rescaleOriginal(obj, dry_run=dry_run)
                
            if rr[0]:
                rv.append(rr)
        except AttributeError:
            LOG('Products.agCommon.findOversizedImages', ERROR, "AttributeError for %s" % obj.absolute_url())
    return rv
        
def recreateScales(obj):

    try:
        state = obj._p_changed
    except ConflictError:
        raise
    except Exception:
        state = 0

    field = obj.getField('image')
    
    if field is None:
        field = obj.getField(IMAGE_FIELD_NAME)
    
    if field is not None:
        field.removeScales(obj)
        field.createScales(obj)

    if state is None:
        obj._p_deactivate()

# Context configuration
from zope.globalrequest import getRequest
from zope.annotation.interfaces import IAnnotations

# Writes a debug message
def debug(msg):
    from datetime import datetime
    f = open("/tmp/debug.log", 'a')
    f.write(str(datetime.now()) + ' | ' + msg)
    f.write('\n')
    f.close()


# This is intended to prevent multiple passes up the tree.
# It handles cascading configurations that we use in multiple places
# Passed a context, this retrieves a hardcoded list of properties, by
# walking the acquisition chain, and fills a dict as it encounters those
# properties.

def _getContextConfig(context):

    # Properties we'd like to retrieve
    properties = [
        'custom_class', 
        'enable_subsite_nav', 
        'hide_breadcrumbs', 
        'top-menu', 
        'fbadmins', 
        'fbappid', 
        'fbpageid',
        'show_event_location',
        'footerlinks',
        'site_title',
        'org_title',
        'agenda_view_day',
        'show_date',
        'show_image',
        'show_read_more',
        'show_college_search',
        'show_section_search',
        'registration_url',
        'contact_creators',
        'contact_title',
        'person_portlet_types',
        'provide_translation_widget',
        'hide_addthis',
        'hide_fblike',
    ]
    
    # Convert to dict
    data = dict([(x,None) for x in properties])

    # Walk the tree, looking for attributes
    for i in aq_chain(context):
        for p in data.keys():
            if data[p] == None:
                if hasattr(i, p):
                    data[p] = getattr(i, p, '')
            
        if IPloneSiteRoot.providedBy(i):
            break

        if None not in data.values():
            break

    return data

def getContextConfig(context, attr, default=None):
    key_root = 'cache-agsci.contextconfig'
    key_filled = '%s-%s' % (key_root, 'filled')
    attr_key = '%s-%s' % (key_root, attr)

    request = getRequest()
    cache = IAnnotations(request)
    
    if not cache.get(key_filled):
        for (k,v) in _getContextConfig(context).iteritems():
            key = "%s-%s" % (key_root, k)
            cache[key] = v
            cache[key_filled] = True

    rv = cache.get(attr_key)

    if not rv:
        rv = default

    return rv

def enablePublication(context):
    
    publicationInterface = IUniversalPublicationExtender

    if context.portal_type in ['File']:
        publicationInterface = IFilePublicationExtender

    if not publicationInterface.providedBy(context):
        adapted = IMarkerInterfaces(context)
        adapted.update(add=[publicationInterface])
        return True
    else:
        return False

def enableTileFolder(context):
    
    context.setLayout('folder_summary_view')
    
    if not ITileFolder.providedBy(context):
        adapted = IMarkerInterfaces(context)
        adapted.update(add=[ITileFolder])
        return True
    else:
        return False

def enableVideoPage(context):
    
    if not IVideoPage.providedBy(context):
        adapted = IMarkerInterfaces(context)
        adapted.update(add=[IVideoPage])
        return True
    else:
        return False

def enableVideoPlaylist(context):
    
    if not IVideoPlaylist.providedBy(context):
        adapted = IMarkerInterfaces(context)
        adapted.update(add=[IVideoPlaylist])
        return True
    else:
        return False

def increaseHeadingLevel(text):
    if '<h2' in text:
        for i in reversed(range(1,6)):
            from_header = "h%d" % i
            to_header = "h%d" % (i+1)
            text = text.replace("<%s" % from_header, "<%s" % to_header)
            text = text.replace("</%s" % from_header, "</%s" % to_header)
    return text

def toISO(v):
            
    if isinstance(v, DateTime):
        try:
            tz = pytz.timezone(v.timezone())
        except pytz.UnknownTimeZoneError:
            # Because that's where we are.
            tz = pytz.timezone('US/Eastern') 
    
        tmp_date = datetime(v.year(), v.month(), v.day(), v.hour(), 
                            v.minute(), int(v.second()))

        if tmp_date.year not in [2499, 1000]:
            return tz.localize(tmp_date).isoformat()

    return None

def unprotectRequest(request):
    try:
        from plone.protect.interfaces import IDisableCSRFProtection
    except ImportError:
        return False

    alsoProvides(request, IDisableCSRFProtection)

# Copied almost verbatim from http://docs.plone.org/develop/plone/security/permissions.html

class UnrestrictedUser(BaseUnrestrictedUser):
    """Unrestricted user that still has an id.
    """
    def getId(self):
        """Return the ID of the user.
        """
        return self.getUserName()

def execute_under_special_role(roles, function, *args, **kwargs):
    """ Execute code under special role privileges.

    Example how to call::

        execute_under_special_role("Manager",
            doSomeNormallyNotAllowedStuff,
            source_folder, target_folder)


    @param function: Method to be called with special privileges

    @param roles: User roles for the security context when calling the privileged code; e.g. "Manager".

    @param args: Passed to the function

    @param kwargs: Passed to the function
    """

    portal = getSite()
    sm = getSecurityManager()

    try:
        try:
            # Clone the current user and assign a new role.
            # Note that the username (getId()) is left in exception
            # tracebacks in the error_log,
            # so it is an important thing to store.
            tmp_user = UnrestrictedUser(
                sm.getUser().getId(), '', roles, ''
                )

            # Wrap the user in the acquisition context of the portal
            tmp_user = tmp_user.__of__(portal.acl_users)
            newSecurityManager(None, tmp_user)

            # Call the function
            return function(*args, **kwargs)

        except:
            # If special exception handlers are needed, run them here
            raise
    finally:
        # Restore the old security manager
        setSecurityManager(sm)