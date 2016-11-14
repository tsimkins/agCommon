#!/usr/bin/python

from Products.CMFCore.utils import getToolByName
from Products.agCommon.browser.api import getAPIData
from Products.agCommon.person.ldap import ldapPersonLookup
from HTMLParser import HTMLParseError
import urllib2
from DateTime import DateTime

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite


def createPerson(psu_id, profile_url = None):

    site = getSite()
    
    directory_type = "FSDFacultyStaffDirectory"
    
    if 'directory' not in site.objectIds():
        raise KeyError("%s not found." % directory_type)

    context = site['directory']
    
    if context.portal_type != directory_type:
        raise TypeError("Directory portal_type of %s not %s"  % (context.portal_type, directory_type))

    if psu_id in context.objectIds():
        raise ValueError("%s already in directory." % psu_id)

    data = ldapPersonLookup(psu_id)
    
    # Set default to TinyMCE
    default_editor = 'TinyMCE'
    
    # Figure out what editor from Portal Properties
    portal_properties = getToolByName(site, 'portal_properties')
    
    try:
        site_properties = portal_properties.site_properties
    except AttributeError:
        pass
    else:
        default_editor = site_properties.getProperty('default_editor')
    
    person_id = context.invokeFactory(type_name="FSDPerson", id=data.get('psu_id'), 
                        firstName=data.get('first_name'), 
                        lastName=data.get('last_name'),
                        suffix=data.get('suffix'), email=data.get('email'), 
                        officeAddress=data.get('office_address'), 
                        officeCity=data.get('city'), 
                        officeState=data.get('state'), 
                        officePostalCode=data.get('zip'), 
                        officePhone=data.get('phone'), 
                        faxNumber=data.get('faxNumber'), 
                        biography=data.get('biography'),
                        jobTitles=data.get('job_title'), 
                        userpref_wysiwyg_editor=default_editor,
                        )

    o = context[person_id]

    o.at_post_create_script()
    o.unmarkCreationFlag()
    
    if profile_url:
        o.primary_profile = profile_url
        o.setLayout('person_redirect_view')
        syncPerson(o, force=True, full=True)

    o.reindexObject()
    
    return o

def getProfileURL(o):
    return getattr(o, 'primary_profile', '')

def isAlias(o):
    # Determine if an alias by profile URL and view
    return (getProfileURL(o) and o.getLayout() in ['person_redirect_view'])

def syncPerson(o, force=False, full=False):

    # Skip if we're not an alias
    if not isAlias(o):
        print "Not an alias: %s" % o.getId()
        return False

    profile_url = getProfileURL(o)

    try:
        data = getAPIData(profile_url)
    except ValueError:
        print "getAPIData Error: %s" % profile_url
        return False

    # Pull selected data from JSON
    modification_date = DateTime(data.get('modified', DateTime()))
    item_type = data.get('type', '')
    image_url = data.get('image_url', '')
            
    # Skip updates if alias modification date is after, and we're not
    # forcing the sync.
    if modification_date <= o.modified() and not force:
        print "Alias modification date after original: %s" % o.getId()
        return False

    # Check to make sure we're a person       
    if item_type != 'Person':
        print "Not a person: %s" % o.getId()
        return False

    if image_url:
        try:
            image_data = urllib2.urlopen(image_url).read()
        except:
            # Ignore errors
            pass
        else:
            o.setImage(image_data)

    # Basic data
    o.setFirstName(data.get('first_name', ''))
    o.setMiddleName(data.get('middle_name', ''))
    o.setLastName(data.get('last_name', ''))
    o.setSuffix(data.get('suffix_name', ''))
    o.setEmail(data.get('email', ''))
    o.setOfficePhone(data.get('office_phone', ''))    
    o.setOfficeAddress(data.get('office_address', ''))
    o.setOfficeCity(data.get('office_city', ''))
    o.setOfficeState(data.get('officestate', ''))
    o.setOfficePostalCode(data.get('office_postal_code', ''))

    # If "full" (e.g. full sync of all fields) is specified.
    # This prevents department-specific attributes (job title, areas of 
    # expertise, and classifications) from being overridden unless explicitly
    # requested.
    
    if full:
        o.setJobTitles(data.get('job_titles', []))
        o.department_research_areas = data.get('department_research_areas', [])
        o.extension_areas = data.get('extension_areas', [])
    
        # Classifications
        classification_names = data.get('directory_classifications', [])
        classification_names_to_add = set(classification_names) - set(o.getClassificationNames())
    
        if classification_names_to_add:        
            directory = o.aq_parent
            classifications_to_add = [x.UID for x in directory.getClassifications() if x.Title in classification_names_to_add]
            current_classifications = o.getRawClassifications()
            current_classifications.extend(classifications_to_add)
            o.setClassifications(current_classifications)

    o.reindexObject()

    print "Updated: %s" % o.getId()
    return True
