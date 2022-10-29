from yt_dlp import YoutubeDL
import requests
from pathlib import Path
import os
import music_tag
from mutagen.mp4 import MP4, MP4Cover
import shutil
import argparse
from ytmusicapi import YTMusic


def get_ydl_extract_info(url):
    with YoutubeDL({
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True
    }) as ydl:
        return ydl.extract_info(url)


def get_download_info(url):
    download_info = []
    ydl_extract_info = get_ydl_extract_info(url)
    if not 'youtube' in ydl_extract_info['webpage_url']:
        raise Exception()
    if 'MPREb_' in ydl_extract_info['webpage_url_basename']:
        url = ydl_extract_info['url']
    if 'playlist' in url:
        track_number = 1
        for video in ydl_extract_info['entries']:
            download_info.append({
                'title': video['title'],
                'track_number': track_number,
                'video_id': video['id']
            })
            track_number += 1
    if 'watch' in url:
        download_info.append({
            'title': ydl_extract_info['title'],
            'track_number': None,
            'video_id': ydl_extract_info['id']
        })
    return download_info


def get_artist(ytmusic_artist):
    if len(ytmusic_artist) == 1:
        return ytmusic_artist[0]['name']
    temp_artist = []
    for i in range(len(ytmusic_artist)):
        temp_artist.append(ytmusic_artist[i]['name'])
    artist = ', '.join(temp_artist[:-1])
    artist += f' & {temp_artist[-1]}'
    return artist


def get_tags(video_id, track_number):
    ytmusic_watch_playlist = ytmusic.get_watch_playlist(video_id)
    if not ytmusic_watch_playlist['tracks'][0]['length'] or not ytmusic_watch_playlist['tracks'][0].get('album'):
        raise Exception()
    ytmusic_album = ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
    album = ytmusic_album['title']
    album_artist = get_artist(ytmusic_album['artists'])
    artist = get_artist(ytmusic_watch_playlist['tracks'][0]['artists'])
    comment = f'https://music.youtube.com/watch?v={video_id}'
    cover = requests.get(f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}=w1200').content
    try:
        lyrics_id = ytmusic.get_lyrics(ytmusic_watch_playlist['lyrics'])
        lyrics = lyrics_id['lyrics']
    except:
        lyrics = None
    title = ytmusic_watch_playlist['tracks'][0]['title']
    total_tracks = ytmusic_album['trackCount']
    year = ytmusic_album['year']
    if not track_number:
        track_number = 1
        for video in get_ydl_extract_info(f'youtube.com/playlist?list={ytmusic_album["audioPlaylistId"]}'):
            if video['id'] == video_id:
                if ytmusic_album['tracks'][track_number - 1]['isExplicit']:
                    rating = 4
                else:
                    rating = 0
                break
            track_number += 1
    else:
        if ytmusic_album['tracks'][track_number - 1]['isExplicit']:
            rating = 4
        else:
            rating = 0
    return {
        'album': album,
        'album_artist': album_artist,
        'artist': artist,
        'comment': comment,
        'cover': cover,
        'lyrics': lyrics,
        'rating': rating,
        'total_tracks': total_tracks,
        'track_number': track_number,
        'title': title,
        'video_id': video_id,
        'year': year
    }


def get_sanizated_string(dirty_string, is_folder = False):
    illegal_characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for character in illegal_characters:
        dirty_string = dirty_string.replace(character, '_')
    if is_folder and dirty_string[-1:] == '.':
            dirty_string = dirty_string[:-1] + '_'
    sanizated_string = dirty_string
    return sanizated_string


def get_download_location(tags, itag):
    if itag == '251':
        file_extension = 'opus'
    else:
        file_extension = 'm4a'
    download_location = Path(f'YouTube Music/{get_sanizated_string(tags["album_artist"], True)}/{get_sanizated_string(tags["album"], True)}/{tags["track_number"]:02d} {get_sanizated_string(tags["title"])}.{file_extension}')
    return download_location


def download(video_id, download_location, itag):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
        'fixup': 'never',
        'format': itag,
        'outtmpl': str(download_location.with_suffix('.temp')),
    }
    if os.path.isfile('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download('music.youtube.com/watch?v=' + video_id)
    

def fixup(download_location):
    os.system(f'ffmpeg -loglevel 0 -y -i "{download_location.with_suffix(".temp")}" -c copy -map_metadata -1 -fflags bitexact "{download_location}"')
    os.remove(download_location.with_suffix('.temp'))


def apply_tags(download_location, tags):
    if download_location.suffix == '.opus':
        file = music_tag.load_file(download_location)
        file['album'] = tags['album']
        file['album_artist'] = tags['album_artist']
        file['artist'] = tags['artist']
        file['comment'] = tags['comment']
        file['artwork'] = tags['cover']
        if tags['lyrics'] is not None:
            file['lyrics'] = tags['lyrics']
        file['total_tracks'] = tags['total_tracks']
        file['track_number'] = tags['track_number']
        file['track_title'] = tags['title']
        file['year'] = tags['year']
        file.save()
    else:
        file = MP4(download_location).tags
        file['\xa9alb'] = tags['album']
        file['aART'] = tags['album_artist']
        file['\xa9ART'] = tags['artist']
        file['\xa9cmt'] = tags['comment']
        file['covr'] = [MP4Cover(tags['cover'], imageformat=MP4Cover.FORMAT_JPEG)]
        if tags['lyrics'] is not None:
            file['\xa9lyr'] = tags['lyrics']
        file['\xa9nam'] = tags['title']
        file['stik'] = [1]
        file['trkn'] = [(tags['track_number'], tags['total_tracks'])]
        file['rtng'] = [tags['rating']]
        file['\xa9day'] = tags['year']
        file.save(download_location)


if __name__ == '__main__':
    if not shutil.which('ffmpeg'):
        print('FFmpeg is not on PATH.')
        exit(1)
    ytmusic = YTMusic()
    parser = argparse.ArgumentParser(description = 'A Python script to download YouTube Music tracks with YouTube Music tags.')
    parser.add_argument(
        'url',
        help='Download YouTube Music track/album/playlist.',
        nargs='+',
        metavar='<url 1> <url 2> <url 3> ...'
    )
    parser.add_argument(
        '-i',
        '--itag',
        default = '140',
        help = 'Set itag (quality). Valid itags are 141 (256kbps AAC m4a), 251 (128bps Opus opus) and 140 (128kbps AAC m4a).',
        metavar = '<itag>'
    )
    args = parser.parse_args()
    itag = args.itag
    url = args.url

    download_info = []
    for i in range(len(url)):
        try:
            print(f'Checking URL ({i + 1} of {len(url)})...')
            download_info += get_download_info(url[i])
        except KeyboardInterrupt:
            exit(0)
        except:
            pass
    if not download_info:
        print('No valid URL entered.')
        exit(1)
    error_count = 0
    for i in range(len(download_info)):
        try:
            print(f'Downloading "{download_info[i]["title"]}" ({i + 1} of {len(download_info)})...')
            tags = get_tags(download_info[i]['video_id'], download_info[i]['track_number'])
            download_location = get_download_location(tags, itag)
            download(download_info[i]['video_id'], download_location, itag)
            fixup(download_location)
            apply_tags(download_location, tags)
        except KeyboardInterrupt:
            exit(0)
        except:
            error_count += 1
            print(f'* Failed to dowload "{download_info[i]["title"]}" ({i + 1} of {len(download_info)}).')
    print(f'All done ({error_count} error(s)).')    
