import shutil
import subprocess
from pathlib import Path
import functools
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL
import requests
from mutagen.mp4 import MP4, MP4Cover


class Gytmdl:
    def __init__(self, cookies_location, itag, final_path, temp_path, overwrite, skip_cleanup):
        self.ytmusic = YTMusic()
        self.cookies_location = Path(cookies_location)
        self.itag = itag
        self.final_path = Path(final_path)
        self.temp_path = Path(temp_path)
        self.overwrite = overwrite
        self.skip_cleanup = skip_cleanup
    

    @functools.lru_cache()
    def get_ydl_extract_info(self, url):
        with YoutubeDL({
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }) as ydl:
            return ydl.extract_info(url, download = False)
    

    def get_download_queue(self, url):
        download_info = []
        ydl_extract_info = self.get_ydl_extract_info(url)
        if not 'youtube' in ydl_extract_info['webpage_url']:
            raise Exception('Not a YouTube URL')
        if 'MPREb_' in ydl_extract_info['webpage_url_basename']:
            ydl_extract_info = self.get_ydl_extract_info(ydl_extract_info['url'])
        if 'playlist' in ydl_extract_info['webpage_url_basename']:
            download_info.extend(ydl_extract_info['entries'])
        if 'watch' in ydl_extract_info['webpage_url_basename']:
            download_info.append(ydl_extract_info)
        return download_info
    

    def get_artist(self, artist_list):
        if len(artist_list) == 1:
            return artist_list[0]['name']
        artist = ', '.join([i['name'] for i in artist_list][:-1])
        artist += f' & {artist_list[-1]["name"]}'
        return artist
    

    def get_ytmusic_watch_playlist(self, video_id):
        ytmusic_watch_playlist = self.ytmusic.get_watch_playlist(video_id)
        if not ytmusic_watch_playlist['tracks'][0]['length'] or not ytmusic_watch_playlist['tracks'][0].get('album'):
            return None
        return ytmusic_watch_playlist
    

    def search_track(self, title):
        return self.ytmusic.search(title, 'songs')[0]['videoId']
    
    
    @functools.lru_cache()
    def get_ytmusic_album(self, browse_id):
        return self.ytmusic.get_album(browse_id)
    

    @functools.lru_cache()
    def get_cover(self, url):
        return requests.get(url).content
    

    def get_tags(self, ytmusic_watch_playlist):
        video_id = ytmusic_watch_playlist['tracks'][0]['videoId']
        ytmusic_album = self.ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
        tags = {
            '\xa9alb': [ytmusic_album['title']],
            'aART': [self.get_artist(ytmusic_album['artists'])],
            '\xa9ART': [self.get_artist(ytmusic_watch_playlist['tracks'][0]['artists'])],
            '\xa9cmt': [f'https://music.youtube.com/watch?v={video_id}'],
            'covr': [MP4Cover(self.get_cover(f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}=w600'), MP4Cover.FORMAT_JPEG)],
            '\xa9nam': [ytmusic_watch_playlist['tracks'][0]['title']],
            '\xa9day': [ytmusic_album['year']],
            'stik': [1]
        }
        try:
            lyrics = self.ytmusic.get_lyrics(ytmusic_watch_playlist['lyrics'])['lyrics']
            if lyrics is not None:
                tags['\xa9lyr'] = [lyrics]
        except:
            pass
        total_tracks = ytmusic_album['trackCount']
        track_number = 1
        for video in self.get_ydl_extract_info(f'https://www.youtube.com/playlist?list={ytmusic_album["audioPlaylistId"]}')['entries']:
            if video['id'] == video_id:
                if ytmusic_album['tracks'][track_number - 1]['isExplicit']:
                    tags['rtng'] = [1]
                else:
                    tags['rtng'] =  [0]
                break
            track_number += 1
        tags['trkn'] = [(track_number, total_tracks)]
        return tags
    

    def get_sanizated_string(self, dirty_string, is_folder):
        for character in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', ';']:
            dirty_string = dirty_string.replace(character, '_')
        if is_folder:
            dirty_string = dirty_string[:40]
            if dirty_string[-1:] == '.':
                dirty_string = dirty_string[:-1] + '_'
        else:
            dirty_string = dirty_string[:36]
        return dirty_string.strip()

    
    def get_temp_location(self, video_id):
        return self.temp_path / f'{video_id}.mp4'
    

    def get_fixed_location(self, video_id):
        return self.temp_path / f'{video_id}_fixed.m4a'
    

    def get_final_location(self, tags):
        return self.final_path / self.get_sanizated_string(tags['aART'][0], True) / self.get_sanizated_string(tags['©alb'][0], True) / (self.get_sanizated_string(f'{tags["trkn"][0][0]:02d} {tags["©nam"][0]}', False) + '.m4a')
    

    def download(self, video_id, temp_location):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'overwrites': self.overwrite,
            'fixup': 'never',
            'format': self.itag,
            'outtmpl': str(temp_location)
        }
        if self.cookies_location.exists():
            ydl_opts['cookiefile'] = str(self.cookies_location)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download('music.youtube.com/watch?v=' + video_id) 
    

    def fixup(self, temp_location, fixed_location):
        fixup = [
            'ffmpeg',
            '-loglevel',
            'error',
            '-i',
            temp_location
        ]
        if self.itag == '251':
            fixup.extend([
                '-f',
                'mp4'
            ])
        subprocess.run(
            [
                *fixup,
                '-c',
                'copy',
                fixed_location
            ],
            check = True
        )
    

    def make_final(self, final_location, fixed_location, tags):
        final_location.parent.mkdir(parents = True, exist_ok = True)
        shutil.copy(fixed_location, final_location)
        file = MP4(final_location)
        file.clear()
        file.update(tags)
        file.save(final_location)
    

    def cleanup(self):
        if not self.skip_cleanup and self.temp_path.exists():
            shutil.rmtree(self.temp_path)
