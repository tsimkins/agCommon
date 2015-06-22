from .. import BaseView
from Products.agCommon.person import isAlias, getProfileURL

class PersonView(BaseView):

    def getData(self, recursive=False):
        
        if isAlias(self.context):
            return {'ERROR' : 
                '%s is alias to %s' % (self.context.getId(), getProfileURL(self.context)) }
    
        data = self.getBaseData()

        data['first_name'] = self.context.getFirstName()
        data['middle_name'] = self.context.getMiddleName()
        data['last_name'] = self.context.getLastName()
        data['suffix'] = self.context.getSuffix()
        data['job_titles'] = self.context.getJobTitles()
        data['email'] = self.context.getEmail()
        data['office_phone'] = self.context.getOfficePhone()    
        data['office_address'] = self.context.getOfficeAddress()
        data['office_city'] = self.context.getOfficeCity()
        data['office_state'] = self.context.getOfficeState()
        data['office_postal_code'] = self.context.getOfficePostalCode()
        data['department_research_areas'] = getattr(self.context, 'department_research_areas', [])
        data['extension_areas'] = getattr(self.context, 'extension_areas', [])

        return data