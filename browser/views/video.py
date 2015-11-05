from Products.Five import BrowserView
from urllib import urlencode

class VideoView(BrowserView):

    default_player_format = "7b98096a0c154cf8a2b0293a7c278d48"

    def media_id(self):
        return getattr(self.context, 'media_id', '')    

    def player_format(self):

        v = getattr(self.context, 'player_format', self.default_player_format)
        
        if not v:
            return self.default_player_format
        
        return v

    def getPlayerConfig(self):
        return {
            'playerForm' : self.player_format(),
            'mediaId' : self.media_id(),
        }

    def flashVars(self):
        return urlencode(self.getPlayerConfig())

    def showPlayer(self):
        return (not not self.media_id())


class VideoPlaylistView(VideoView):

    def getPlayerConfig(self):
        return {
            'playerForm' : self.player_format(),
            'channelId' : self.playlist_id(),
            'deepLink' : 'true',
        }

    def playlist_id(self):
        return getattr(self.context, 'playlist_id', '')  

    def showPlayer(self):
        return (not not self.playlist_id())