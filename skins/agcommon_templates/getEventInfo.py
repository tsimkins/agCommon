request = container.REQUEST

from Products.CMFCore.utils import getToolByName
portal_catalog = getToolByName(context, "portal_catalog")

event_info = {  'event-name' : None,
                'event-description' : None,
                'event-date' : None,
                'event-organizer-email' : None,
                'more-information' : None,
                'contact-name' : None,
                'contact-email' : None,
                'contact-phone' : None,
                'event-primary-program' : None,
                'event-programs' : None,
                'event-topics' : None,
                'event-county' : None,
                'event-zip-code' : None,
                'event-course' : None,
                'event-location' : None,
                'event-location-url' : None,
                'confirmation-message' : None,
              }


uid = request.form.get('uid', None)

if uid:
    results = portal_catalog.searchResults({'portal_type' : 'Event', 'UID' : uid})
    if results:
        r = results[0]
        o = r.getObject()
        if hasattr(o, 'free_registration') and o.free_registration:
            # From Email
            from_email = getattr(o, 'contactEmail', 'do.not.reply@psu.edu')
            if from_email:
                from_email = "Penn State Extension <%s>" % from_email
            else:
                from_email = "Penn State Extension <do.not.reply@psu.edu>"

            # Topics and Primary Topic
            topics = ['']
            primary_topic = ''

            if hasattr(r, 'extension_topics') and r.extension_topics:
                topics = list(r.extension_topics)
                if len(topics) > 1:
                    p = o.getParentNode()
                    if hasattr(p, 'extension_topics') and len(p.extension_topics) == 1:
                        primary_topic = p.extension_topics[0]
                else:
                    primary_topic = topics[0]

            # Subtopics
            subtopics = ['']

            if hasattr(r, 'extension_subtopics') and r.extension_subtopics:
                subtopics = list(r.extension_subtopics)

            # Course
            course = ''
            if hasattr(r, 'extension_courses') and r.extension_courses:
                course = r.extension_courses[0]

            # County
            county = ''
            if hasattr(r, 'extension_counties') and r.extension_counties:
                counties = list(r.extension_counties)
                if len(counties) > 1:
                    p = o.getParentNode()
                    if hasattr(p, 'extension_counties') and len(p.extension_counties) == 1:
                        county = p.extension_counties[0]
                else:
                    county = counties[0]

            # ZIP Code
            zip_code = ''

            if hasattr(o, 'zip_code') and o.zip_code:
                zip_code = unicode(o.zip_code).strip()

            # Location
            location = ''
            map_link = ''

            if hasattr(o, 'location') and o.location:
                location = unicode(o.location).strip()

            if hasattr(o, 'map_link') and o.map_link:
                map_link = unicode(o.map_link).strip()

            # Confirmation Message

            confirmation_message = ''

            if hasattr(o, 'free_registration_confirmation_message') and \
                       o.free_registration_confirmation_message:
                confirmation_message = o.free_registration_confirmation_message
                confirmation_message = unicode(confirmation_message).replace("\n", " ").replace("\r", " ")

            event_info = { 'event-name' : o.Title(),
                           'event-description' : o.Description(),
                           'event-date' : r.start.strftime('%m/%d/%Y %I:%M %p'),
                           'event-organizer-email' : o.free_registration_email or None,
                           'more-information' : o.absolute_url(),
                           'contact-email' : o.contactEmail or None,
                           'contact-name' : o.contactName or None,
                           'contact-phone' : o.contactPhone or None,
                           'from-email' : from_email,
                           'event-primary-program' : primary_topic,
                           'event-programs' : ";".join(topics),
                           'event-topics' : ";".join(subtopics),
                           'event-county' : county,
                           'event-zip-code' : zip_code,
                           'event-course' : course,
                           'event-location' : location,
                           'event-location-url' : map_link,
                           'confirmation-message' : confirmation_message,
                         }

for k in event_info.keys():
    request.form[k] = event_info[k]

return event_info

