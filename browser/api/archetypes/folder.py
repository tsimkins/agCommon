from .. import BaseView

class FolderView(BaseView):

    def getContents(self):
        return self.context.listFolderContents()

    def getData(self, recursive=True):
        data = self.getBaseData()

        # Check for presence of default page that's a collection, and if that's
        # the case, return that item's data
        context = self.context
        default_page_id = context.getDefaultPage()
        
        if default_page_id and default_page_id in context.objectIds():
            return context[default_page_id].restrictedTraverse('@@api-json').getData(recursive=recursive)

        if recursive:
            contents = self.getContents()
            
            if contents:
                data['contents'] = []
                
                for o in contents:
    
                    api_json = o.restrictedTraverse('@@api-json')
    
                    data['contents'].append(api_json.getFilteredData(recursive=False))

        return data