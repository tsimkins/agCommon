from folder import FolderView

class TopicView(FolderView):

    def getContents(self):
        return self.context.queryCatalog(full_objects=True)