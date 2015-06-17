from .. import BaseView

class DirectoryView(BaseView):

    def getContents(self):
        return self.context.getPeople()
        
    def getData(self, recursive=True):
        data = self.getBaseData()
        
        if recursive:
            contents = self.getContents()
            
            if contents:
                data['contents'] = []
                
                for o in contents:
                    # Skip if this is an 'alias'
                    if getattr(o, 'primary_profile', ''):
                        continue
    
                    api_json = o.restrictedTraverse('@@api-json')
    
                    item_data = api_json.getFilteredData(recursive=False)
    
                    if item_data.get('review_state', '') == 'active':
                        data['contents'].append(item_data)

        return data