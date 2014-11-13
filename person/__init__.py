#!/usr/bin/python

from Products.agCommon.person.ldap import ldapPersonLookup
from HTMLParser import HTMLParseError

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite


def createPerson(psu_id):

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
                        userpref_wysiwyg_editor='Kupu'
                        )

    o = context[person_id]

    o.at_post_create_script()
    o.unmarkCreationFlag()
    
    return o

    