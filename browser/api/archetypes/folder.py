from .. import BaseView

class FolderView(BaseView):

    def getContents(self):
        return self.context.listFolderContents()

    def getData(self, recursive=True):
        data = self.getBaseData()

        if recursive:
            contents = self.getContents()
            
            if contents:
                data['contents'] = []
                
                for o in contents:
    
                    api_json = o.restrictedTraverse('@@api-json')
    
                    data['contents'].append(api_json.getFilteredData(recursive=False))

        return data