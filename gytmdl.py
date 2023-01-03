from ytmusicapi import YTMusic
from pathlib import Path
from yt_dlp import YoutubeDL
import requests
import subprocess
from mutagen.mp4 import MP4, MP4Cover
import shutil
from argparse import ArgumentParser
import traceback

class Gytmdl:
    def __init__(self, cookies_location, itag, final_path, temp_path, skip_cleanup):
        self.ytmusic = YTMusic()
        self.cookies_location = Path(cookies_location)
        self.itag = itag
        self.final_path = Path(final_path)
        self.temp_path = Path(temp_path)
        self.skip_cleanup = skip_cleanup
    

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
            for video in ydl_extract_info['entries']:
                download_info.append({
                    'title': video['title'],
                    'video_id': video['id']
                })
        if 'watch' in ydl_extract_info['webpage_url_basename']:
            download_info.append({
                'title': ydl_extract_info['title'],
                'video_id': ydl_extract_info['id']
            })
        return download_info
    

    def get_artist(self, ytmusic_artist):
        if len(ytmusic_artist) == 1:
            return ytmusic_artist[0]['name']
        artist = ', '.join([artist['name'] for artist in ytmusic_artist][:-1])
        artist += f' & {ytmusic_artist[-1]["name"]}'
        return artist
    

    def get_ytmusic_watch_playlist(self, video_id):
        ytmusic_watch_playlist = self.ytmusic.get_watch_playlist(video_id)
        if not ytmusic_watch_playlist['tracks'][0]['length'] or not ytmusic_watch_playlist['tracks'][0].get('album'):
            return None
        return ytmusic_watch_playlist
    

    def search_track(self, title):
        return self.ytmusic.search(title, 'songs')[0]['videoId']
    

    def get_tags(self, ytmusic_watch_playlist):
        video_id = ytmusic_watch_playlist['tracks'][0]['videoId']
        ytmusic_album = self.ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
        tags = {
            '\xa9alb': [ytmusic_album['title']],
            'aART': [self.get_artist(ytmusic_album['artists'])],
            '\xa9ART': [self.get_artist(ytmusic_watch_playlist['tracks'][0]['artists'])],
            '\xa9cmt': [f'https://music.youtube.com/watch?v={video_id}'],
            'covr': [MP4Cover(requests.get(f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}=w600').content, MP4Cover.FORMAT_JPEG)],
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
        return self.temp_path / f'{video_id}.m4a'
    

    def get_temp_location_fixed(self, video_id):
        return self.temp_path / f'{video_id}_fixed.m4a'
    

    def get_final_location(self, tags):
        return self.final_path / self.get_sanizated_string(tags['aART'][0], True) / self.get_sanizated_string(tags['©alb'][0], True) / (self.get_sanizated_string(f'{tags["trkn"][0][0]:02d} {tags["©nam"][0]}', False) + '.m4a')
    

    def download(self, video_id, temp_location):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'overwrites': True,
            'fixup': 'never',
            'format': self.itag,
            'outtmpl': str(temp_location)
        }
        if self.cookies_location.exists():
            ydl_opts['cookiefile'] = str(self.cookies_location)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download('music.youtube.com/watch?v=' + video_id) 
    

    def fixup(self, final_location, temp_location, temp_location_fixed):
        subprocess.check_output([
            'MP4Box',
            '-quiet',
            '-add',
            temp_location,
            '-itags',
            'album=placeholder',
            '-new',
            temp_location_fixed
        ])
        final_location.parent.mkdir(exist_ok = True, parents = True)
        shutil.copy(temp_location_fixed, final_location)
    

    def apply_tags(self, final_location, tags):
        file = MP4(final_location).tags
        for key, value in tags.items():
            file[key] = value
        file.save(final_location)
    

    def cleanup(self):
        if not self.skip_cleanup and self.temp_path.exists():
            shutil.rmtree(self.temp_path)


if __name__ == '__main__':
    if not shutil.which('MP4Box'):
        raise Exception('MP4Box is not on PATH.')
    parser = ArgumentParser(description = 'A Python script to download YouTube Music tracks with YouTube Music tags.')
    parser.add_argument(
        'url',
        help='YouTube Music track/album/playlist URL(s).',
        nargs='*',
        metavar='<url>'
    )
    parser.add_argument(
        '-u',
        '--urls-txt',
        help = 'Read URLs from a text file.',
        nargs = '?',
        metavar = '<txt_file>'
    )
    parser.add_argument(
        '-i',
        '--itag',
        default = '140',
        choices = ['141', '140'],
        help = 'Itag (quality). Valid itags are 141 (256kbps AAC m4a) and 140 (128kbps AAC m4a).',
        metavar = '<itag>'
    )
    parser.add_argument(
        '-t',
        '--temp-path',
        default = 'temp',
        help = 'Temp path.',
        metavar = '<temp_path>'
    )
    parser.add_argument(
        '-f',
        '--final-path',
        default = 'YouTube Music',
        help = 'Final path.',
        metavar = '<final_path>'
    )
    parser.add_argument(
        '-c',
        '--cookies-location',
        default = 'cookies.txt',
        help = 'Cookies location.',
        metavar = '<cookies_location>'
    )
    parser.add_argument(
        '-s',
        '--skip-cleanup',
        action = 'store_true',
        help = 'Skip cleanup.'
    )
    parser.add_argument(
        '-p',
        '--print-exceptions',
        action = 'store_true',
        help = 'Print exceptions.'
    )
    args = parser.parse_args()
    dl = Gytmdl(args.cookies_location, args.itag, args.final_path, args.temp_path, args.skip_cleanup)
    if not args.url and not args.urls_txt:
        parser.error('you must specify an url or a text file using -u/--urls-txt.')
    if args.urls_txt:
        with open(args.urls_txt, 'r', encoding = 'utf8') as f:
            args.url = f.read().splitlines()
    download_queue = []
    error_count = 0
    for i in range(len(args.url)):
        try:
            download_queue.append(dl.get_download_queue(args.url[i].strip()))
        except KeyboardInterrupt:
            exit(0)
        except:
            error_count += 1
            print(f'* Failed to check URL {i + 1}.')
            if args.print_exceptions:
                traceback.print_exc()
    for i in range(len(download_queue)):
        for j in range(len(download_queue[i])):
            print(f'Downloading "{download_queue[i][j]["title"]}" (track {j + 1} from URL {i + 1})...')
            try:
                ytmusic_watch_playlist = dl.get_ytmusic_watch_playlist(download_queue[i][j]['video_id'])
                if ytmusic_watch_playlist is None:
                    download_queue[i][j]['video_id'] = dl.search_track(download_queue[i][j]['title'])
                    ytmusic_watch_playlist = dl.get_ytmusic_watch_playlist(download_queue[i][j]['video_id'])
                tags = dl.get_tags(ytmusic_watch_playlist)
                temp_location = dl.get_temp_location(download_queue[i][j]['video_id'])
                dl.download(download_queue[i][j]['video_id'], temp_location)
                temp_location_fixed = dl.get_temp_location_fixed(download_queue[i][j]['video_id'])
                final_location = dl.get_final_location(tags)
                fixup = dl.fixup(final_location, temp_location, temp_location_fixed)
                dl.apply_tags(final_location, tags)
            except KeyboardInterrupt:
                exit(0)
            except:
                error_count += 1
                print(f'* Failed to download "{download_queue[i][j]["title"]}" (track {j + 1} from URL {i + 1}).')
                if args.print_exceptions:
                    traceback.print_exc()
            dl.cleanup()
    print(f'Done ({error_count} error(s)).')
