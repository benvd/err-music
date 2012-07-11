from datetime import timedelta
import logging
from config import CHATROOM_PRESENCE
from errbot.botplugin import BotPlugin
from errbot.jabberbot import botcmd

from BeautifulSoup import BeautifulSoup
import urllib
import re
import pylast

API_KEY = '094e0ec812010881ef9fece6a7d5ed2a'
API_SECRET = '8797b1ccf8c6b9cfe5a9c7cc54719168'

class Music(BotPlugin):

    @botcmd
    def lyrics(self, mess, args):
        """Fetches lyrics from the given artist and song.
        !lyrics Rick Astley : Never Gonna Give You Up"""
        try:
            artist, title = args.split(':')
        except ValueError:
            return 'usage: !lyrics artist : title'

        self.send(mess.getFrom(), '/me is looking for your lyrics...', message_type='groupchat')

        artist = artist.strip().replace(' ', '_').title()
        title = title.strip().replace(' ', '_').title()

        artist = urllib.quote(artist)
        title = urllib.quote(title)

        lyrics = urllib.urlopen('http://lyricwiki.org/%s:%s' % (artist, title))
        text = lyrics.read()
        soup = BeautifulSoup(text)
        lyrics = soup.findAll(attrs={'class': 'lyricbox'})

        if lyrics:
            lyrics = lyrics[0].renderContents()
            lyrics = lyrics.replace('<br />', '\n')
            lyrics = re.sub('<[^<]*?/?>', '', lyrics)                        # strip html tags
            lyrics = re.sub('<!--.*-->', '', lyrics, flags=re.DOTALL)        # strip html comments
            lyrics = re.sub(' ?Send.*?Ringtone to your Cell ?', '', lyrics)  # strip ads

            # parse HTML entities
            entities = BeautifulSoup(lyrics, convertEntities=BeautifulSoup.HTML_ENTITIES)
            return entities.renderContents()
        else:
            return 'Lyrics not found.'

    @botcmd
    def whosings(self, mess, args):
        """
        Return top 5 artist suggestions for a song name
        """
        if not args:
            return 'give me a song name dude!'

        self.send(mess.getFrom(), '/me is looking for artists...', message_type='groupchat')

        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
        p = network.search_for_track('', args).get_next_page()
        return_val = u'Top results:\n'
        for item in p[:5]:

            artist = item.get_artist()
            artist_name = artist.get_name() if artist else 'Unknown'

            alb = item.get_album()
            album_name = alb.get_name() if alb else '<>'

            duration = item.get_duration()
            duration_str = str(timedelta(milliseconds=duration)) if duration else ''

            return_val += u'%s %s by %s (in %s)\n' % (item.get_title(), duration_str, artist_name, album_name)

        return return_val.strip('\n')

    @botcmd()
    def topalbums(self, mess, args):
        """
        Return top 5 albums by artist
        """
        if not args:
            return 'give me a name of an artist.'

        self.send(mess.getFrom(), '/me is searching for to albums by %s...' % args, message_type='groupchat')

        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
        artist = network.get_artist(args)
        if not artist:
            return 'Artist not found...'

        top_albums = artist.get_top_albums()[:5]
        ans = u''
        for a in top_albums:
            ans += a.item.get_name() + u'\n'

        return ans


    @botcmd()
    def toptracks(self, mess, args):
        """
        Return top 10 tracks by artist
        """
        if not args:
            return 'give me a name of an artist.'

        self.send(mess.getFrom(), '/me is searching for to tracks by %s...' % args, message_type='groupchat')
        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
        artist = network.get_artist(args)
        if not artist:
            return 'Artist not found...'

        top_tracks = artist.get_top_tracks()[:10]
        ans = u''
        for tt in top_tracks:
            ans += tt.item.get_name() + u'\n'

        return ans


    def get_similar_tracks(self, network, track, artist=None):

        if not artist:
            artist = ''
        tracks = network.search_for_track(artist, track).get_next_page()
        if tracks:
            for t in tracks:
                try:
                    similar = t.get_similar()[:10]
                    if similar:
                        ans = u''
                        for s in similar:
                            ans += u'%s / %s\n' % (s.item.get_name(), s.item.get_artist().get_name())

                        return ans.strip('\n')
                except : #baaa last.fm errors...
                    pass

        return 'Could not find anything similar to \'%s\'' % track



    @botcmd(split_args_with=':')
    def recommend(self, mess, args):
        """
        Get 10 similar artists or songs
        If artist:track were supplied, will look for similar songs.
        Else will try artists an d if none, will try songs.
        """
        if not args:
            return 'give me a name of something to recommend stuff by - either an artist or a track or both- artist:track.'

        self.send(mess.getFrom(), '/me is searching for recommendations...', message_type='groupchat')
        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

        if len(args) == 2:
            artist = args[0]
            track = args[1]
            return self.get_similar_tracks(network, track, artist)

        artists = network.search_for_artist(args[0]).get_next_page()
        if artists:
            similar = artists[0].get_similar(limit=10)
            if similar:
                ans = u''
                for s in similar:
                    ans += s.item.get_name() + u'\n'
                return ans.strip('\n')

        return self.get_similar_tracks(network, args[0])


    @botcmd(split_args_with=':')
    def album(self, mess, args):
        """
        Show album info
        """
        artist = '' if len(args) == 1 else args[0]
        title = args[0] if len(args) == 1 else args[1]

        if not artist or not title:
            return 'Dude, I need the name of the album and the artist who made it... artist:album'

        self.send(mess.getFrom(), '/me is searching album info...', message_type='groupchat')

        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
        album = network.get_album(artist, title)
        if not album:
            return 'Could not find your album'

        ans = u''
        release_date = album.get_release_date()
        if release_date:
            ans = u'%s Released %s\n' % (album.get_title(), release_date)

        summary = album.get_wiki_summary()
        if summary:
            remove_html_tags = re.compile(r'<.*?>')
            too_many_spaces = re.compile(r'  +')
            ans += too_many_spaces.sub(' ', remove_html_tags.sub(' ', summary))

        if not ans.strip():
            return 'No info found for album %s' % title
        return ans


    @botcmd()
    def aboutartist(self, mess, args):
        """
        Show artist info
        """
        if not args:
            return 'Usage: !aboutartist artist_name'

        self.send(mess.getFrom(), '/me is searching for artist info...', message_type='groupchat')

        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
        artist = network.search_for_artist(args).get_next_page()
        if artist:
            remove_html_tags = re.compile(r'<.*?>')
            too_many_spaces = re.compile(r'  +')
            return too_many_spaces.sub(' ', remove_html_tags.sub(' ', artist[0].get_bio_summary()))

        return 'No info found for %s' % args




