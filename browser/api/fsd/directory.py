from .. import BaseView

class DirectoryView(BaseView):

    def getPeople(self):
        return self.context.getPeople()
        
    def getData(self):
        data = self.getBaseData()

        people = self.getPeople()
        
        if people:
            data['people'] = []
            
            for o in people:
                # Skip if this is an 'alias'
                if getattr(o, 'primary_profile', ''):
                    continue

                api_json = o.restrictedTraverse('@@api-json')

                person_data = api_json.getFilteredData()

                if person_data.get('review_state', '') == 'active':
                    data['people'].append(person_data)

        return data