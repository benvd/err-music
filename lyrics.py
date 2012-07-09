from errbot.botplugin import BotPlugin
from errbot.jabberbot import botcmd

from BeautifulSoup import BeautifulSoup
import urllib
import re


class Lyrics(BotPlugin):

    @botcmd
    def lyrics(self, mess, args):
        """Fetches lyrics from the given artist and song.
        !lyrics Rick Astley : Never Gonna Give You Up"""
        try:
            artist, title = args.split(':')
        except ValueError:
            return 'usage: !lyrics artist : title'

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
            print 'Lyrics not found.'
