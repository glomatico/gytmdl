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
    def __init__(self, cookies_location, final_path, temp_path):
        self.ytmusic = YTMusic()
        self.cookies_location = Path(cookies_location)
        self.final_path = Path(final_path)
        self.temp_path = Path(temp_path)
    

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
            track_number = 1
            for video in ydl_extract_info['entries']:
                download_info.append({
                    'title': video['title'],
                    'track_number': track_number,
                    'video_id': video['id']
                })
                track_number += 1
        if 'watch' in ydl_extract_info['webpage_url_basename']:
            download_info.append({
                'title': ydl_extract_info['title'],
                'track_number': None,
                'video_id': ydl_extract_info['id']
            })
        return download_info
    

    def get_artist(self, ytmusic_artist):
        if len(ytmusic_artist) == 1:
            return ytmusic_artist[0]['name']
        artist = ', '.join([artist['name'] for artist in ytmusic_artist][:-1])
        artist += f' & {ytmusic_artist[-1]["name"]}'
        return artist
    

    def get_tags(self, video_id, track_number):
        ytmusic_watch_playlist = self.ytmusic.get_watch_playlist(video_id)
        if not ytmusic_watch_playlist['tracks'][0]['length'] or not ytmusic_watch_playlist['tracks'][0].get('album'):
            raise Exception('Not a YouTube Music video or track unavailable')
        ytmusic_album = self.ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
        album = ytmusic_album['title']
        album_artist = self.get_artist(ytmusic_album['artists'])
        artist = self.get_artist(ytmusic_watch_playlist['tracks'][0]['artists'])
        comment = f'https://music.youtube.com/watch?v={video_id}'
        cover = requests.get(f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}=w600').content
        try:
            lyrics_id = self.ytmusic.get_lyrics(ytmusic_watch_playlist['lyrics'])
            lyrics = lyrics_id['lyrics']
        except:
            lyrics = None
        title = ytmusic_watch_playlist['tracks'][0]['title']
        total_tracks = ytmusic_album['trackCount']
        year = ytmusic_album['year']
        if not track_number:
            track_number = 1
            for video in self.get_ydl_extract_info(f'https://www.youtube.com/playlist?list={ytmusic_album["audioPlaylistId"]}')['entries']:
                if video['id'] == video_id:
                    if ytmusic_album['tracks'][track_number - 1]['isExplicit']:
                        rating = 1
                    else:
                        rating = 0
                    break
                track_number += 1
        else:
            if ytmusic_album['tracks'][track_number - 1]['isExplicit']:
                rating = 1
            else:
                rating = 0
        tags = {
            '\xa9alb': [album],
            'aART': [album_artist],
            '\xa9ART': [artist],
            '\xa9cmt': [comment],
            'covr': [MP4Cover(cover, MP4Cover.FORMAT_JPEG)],
            'rtng': [rating],
            'stik': [1],
            '\xa9nam': [title],
            'trkn': [(track_number, total_tracks)],
            '\xa9day': [year]
        }
        if lyrics:
            tags['\xa9lyr'] = [lyrics]
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
    

    def download(self, video_id, temp_location, itag):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'overwrites': True,
            'fixup': 'never',
            'format': itag,
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
            'title=placeholder',
            '-new',
            temp_location_fixed
        ])
        final_location.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy(temp_location_fixed, final_location)
    

    def apply_tags(self, final_location, tags):
        file = MP4(final_location).tags
        for key, value in tags.items():
            file[key] = value
        file.save(final_location)
    

    def cleanup(self):
        shutil.rmtree(self.temp_path)


if __name__ == '__main__':
    if not shutil.which('MP4Box'):
        print('MP4Box is not on PATH.')
        exit(1)
    parser = ArgumentParser(description = 'A Python script to download YouTube Music tracks with YouTube Music tags.')
    parser.add_argument(
        'url',
        help='YouTube Music track/album/playlist URL(s).',
        nargs='+',
        metavar='<url>'
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
    gytmdl = Gytmdl(args.cookies_location, args.final_path, args.temp_path)
    download_queue = []
    error_count = 0
    for i in range(len(args.url)):
        try:
            download_queue.append(gytmdl.get_download_queue(args.url[i]))
        except KeyboardInterrupt:
            exit(0)
        except:
            error_count += 1
            print(f'* Failed to check URL {i + 1}.')
            if args.print_exceptions:
                traceback.print_exc()
    if not download_queue:
        print('* Failed to check all URLs.')
        exit(1)
    for i in range(len(download_queue)):
        for j in range(len(download_queue[i])):
            print(f'Downloading "{download_queue[i][j]["title"]}" (track {j + 1} from URL {i + 1})...')
            try:
                tags = gytmdl.get_tags(download_queue[i][j]['video_id'], download_queue[i][j]['track_number'])
                temp_location = gytmdl.get_temp_location(download_queue[i][j]['video_id'])
                gytmdl.download(download_queue[i][j]['video_id'], temp_location, args.itag)
                temp_location_fixed = gytmdl.get_temp_location_fixed(download_queue[i][j]['video_id'])
                final_location = gytmdl.get_final_location(tags)
                fixup = gytmdl.fixup(final_location, temp_location, temp_location_fixed)
                gytmdl.apply_tags(final_location, tags)
            except KeyboardInterrupt:
                exit(0)
            except:
                error_count += 1
                print(f'* Failed to download "{download_queue[i][j]["title"]}" (track {j + 1} from URL {i + 1})...')
                if args.print_exceptions:
                    traceback.print_exc()
            if not args.skip_cleanup:
                gytmdl.cleanup()
    print(f'Finished ({error_count} error(s)).')
        