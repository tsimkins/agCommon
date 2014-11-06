from AccessControl import ClassSecurityInfo
from StringIO import StringIO
import csv
from Products.CMFCore import permissions
from zope.interface import implements, Interface
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime
from Products.agCommon import getContextConfig
import HTMLParser

try:
    from zope.app.component.hooks import getSite
except ImportError:
    from zope.component.hooks import getSite

class IRegistrationView(Interface):

    def getEventUID(self):
        pass

    def getEventByUID(self):
        pass
       
    def canViewRegistrations(self, event):
        pass

    def allowRegistration(self, event):
        pass

    def registrationURL(self):
        pass

    def getRegistrations(self, show_titles=True):
        pass

    def getAttendeeCount(self):
        pass

    def unescapeHTML(self, e):
        pass

class RegistrationView(BrowserView):

    implements(IRegistrationView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def getEventUID(self):
        if self.context.portal_type == 'Event':
            return self.context.UID()
        else:
            return self.request.form.get('uid')

    def getEventByUID(self):
        uid = self.getEventUID()
        
        if uid:
            portal_catalog = getToolByName(self.context, "portal_catalog")
            results = portal_catalog.searchResults({'portal_type' : 'Event', 'UID' : uid})
            if results:
                r = results[0]
                o = r.getObject()
                return o
        return None

    def canViewRegistrations(self, event):
        mt = getToolByName(self.context, 'portal_membership')
        member = mt.getAuthenticatedMember()

        if member.has_role('Event Registration Viewer', event):
            return True
        elif mt.checkPermission('Modify portal content', event):
            return True
        else:
            return False
            
    def allowRegistration(self, event):
        if not event:
            return False

        if not self.registrationForm:
            return False

        now = DateTime()
        
        if hasattr(event, 'free_registration_deadline'):
            registration_deadline = getattr(event, 'free_registration_deadline')
            if registration_deadline:
                return (now < registration_deadline)

        if now > event.end():
            return False

        if hasattr(event, 'free_registration_attendee_limit'):
            attendee_limit = getattr(event, 'free_registration_attendee_limit')
            if attendee_limit:
                attendeeCount = self.getAttendeeCount()
                if attendeeCount >= attendee_limit:
                    return False

        return True

    def getAttendeeCount(self):
        return len(self.getRegistrations(show_titles=False))

    @property
    def registrationURL(self):
        form = self.registrationForm
        if form:
            return form.absolute_url()
        else:
            return None

    @property
    def registrationForm(self):
        url = getContextConfig(self.context, 'registration_url')

        if url:
            url = url.replace('${portal_url}', '')
            if url.startswith('/'):
                url = url[1:]
        else:
            url = "register"
        
        try:
            return self.context.restrictedTraverse(url)
        except AttributeError:
            return None

    def getRegistrations(self, show_titles=True):
        r_form = self.registrationForm

        if not r_form or 'save-data' not in r_form.objectIds():
            return []
            
        save_data = r_form['save-data']
        uid = self.getEventUID()
        
        data = []
        
        if uid and save_data:
            if show_titles:
                data.append(save_data.getColumnTitles()[1:])
            for r in save_data.getSavedFormInput():
                if r[0] == uid:
                    data.append(r[1:])     

        return data

    def unescapeHTML(self, e):
        h = HTMLParser.HTMLParser()
        return h.unescape(e)
        

class DownloadCSVView(RegistrationView):
    security = ClassSecurityInfo()
    security.declareProtected(permissions.ModifyPortalContent, '__call__')

    def __call__(self):
        out = StringIO()
        writer = csv.writer(out)
        event = self.getEventByUID()
        
        registrations = self.getRegistrations()
        
        if event and self.canViewRegistrations(event) and registrations:
            filename = "%s.csv" % event.getId()
            for r in registrations:
                writer.writerow(r)
        else:
           filename = "error.csv"
           writer.writerow(["Error retrieving registration information. Either event does not exist, or you do not have the appropriate permissions."])
    
        self.request.response.setHeader('Content-Type', 'text/csv')
        self.request.response.setHeader('Content-Disposition', 'attachment; filename="%s"' % filename)
        

        return out.getvalue()
