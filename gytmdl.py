"""
Glomatico's YouTube Music Downloader
 Python script to download YouTube Music tracks with YouTube Music tags.
"""

import yt_dlp
from ytmusicapi import YTMusic
import requests
import platform
import os
from mutagen.mp4 import MP4, MP4Cover
import music_tag
import argparse


def get_video_id(url):
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        url_details = ydl.extract_info(
            url,
            download=False,
        )
    if 'youtube' in url_details['extractor']:
        if 'MPREb' in url_details['webpage_url_basename']:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url_details = ydl.extract_info(
                    url_details['url'],
                    download=False,
                )
        if 'playlist' in url_details['webpage_url_basename']:
            video_id = []
            for i in range(len(url_details['entries'])):
                video_id.append(url_details['entries'][i]['id'])
            return video_id
        if 'watch' in url_details['webpage_url_basename']:
            return [url_details['id']]
    raise


ytmusic = YTMusic()


def get_tags(video_id, artwork_size):
    watch_playlist = ytmusic.get_watch_playlist(video_id)
    album_details = ytmusic.get_album(watch_playlist['tracks'][0]['album']['id'])
    album = album_details['title']
    album_fixed = album
    if len(album_details['artists']) == 1:
        album_artist = album_details['artists'][0]['name']
    else:
        album_artist_temp = []
        for a in range(len(album_details['artists'])):
            album_artist_temp.append(album_details['artists'][a]['name'])
        album_artist = ", ".join(album_artist_temp[:-1])
        album_artist += " & " + album_artist_temp[-1]
    album_artist_fixed = album_artist
    if len(watch_playlist['tracks'][0]['artists']) == 1:
        artist = watch_playlist['tracks'][0]['artists'][0]['name']
    else:
        artist_temp = []
        for a in range(len(watch_playlist['tracks'][0]['artists'])):
            artist_temp.append(watch_playlist['tracks'][0]['artists'][a]['name'])
        artist = ", ".join(artist_temp[:-1])
        artist += " & " + artist_temp[-1]
    artist_fixed = artist
    artwork = requests.get(album_details['thumbnails'][0]['url'].split('=')[0] + '=w' + artwork_size).content
    try:
        lyrics_id = ytmusic.get_lyrics(watch_playlist['lyrics'])
        lyrics = lyrics_id['lyrics']
    except:
        lyrics = None
    rating = 0
    track_number = 0
    track_number_fixed = 00
    total_tracks = album_details['trackCount']
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        album_playlist_details = ydl.extract_info(
            'https://www.youtube.com/playlist?list='
            + album_details['audioPlaylistId'],
            download=False,
        )
    for i in range(len(album_playlist_details['entries'])):
        if album_playlist_details['entries'][i]['id'] == video_id:
            if album_details['tracks'][i]['isExplicit']:
                rating = 4
            else:
                rating = 0
            track_number = 1 + i
            track_number_fixed = '%02d' % (1 + i)
    track_title = watch_playlist['tracks'][0]['title']
    track_title_fixed = track_title
    year = album_details['year']
    illegal_characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for a in range(len(illegal_characters)):
        album_artist_fixed = album_artist_fixed.replace(illegal_characters[a], '_')
        album_fixed = album_fixed.replace(illegal_characters[a], '_')
        artist_fixed = artist_fixed.replace(illegal_characters[a], '_')
        track_title_fixed = track_title_fixed.replace(illegal_characters[a], '_')
    if album_artist_fixed[-1:] == '.':
        album_artist_fixed = album_artist_fixed[:-1] + '_'
    if album_fixed[-1:] == '.':
        album_fixed = album_fixed[:-1] + '_'
    return {
        'album': album,
        'album_fixed': album_fixed,
        'album_artist': album_artist,
        'album_artist_fixed': album_artist_fixed,
        'artist': artist,
        'artist_fixed': artist_fixed,
        'artwork': artwork,
        'lyrics': lyrics,
        'rating': rating,
        'total_tracks': total_tracks,
        'track_number': track_number,
        'track_number_fixed': track_number_fixed,
        'track_title': track_title,
        'track_title_fixed': track_title_fixed,
        'video_id': video_id,
        'year': year,
    }


def get_track_download_directory(download_format, tags):
    if '14' in download_format:
        extension = '.m4a'
    else:
        extension = '.opus'
    if platform.system() == 'Windows':
        current_directory = '\\\\?\\' + os.getcwd()
        slash = '\\'
    else:
        current_directory = os.getcwd()
        slash = '/'
    track_download_directory = current_directory + slash + 'YouTube Music' + slash + tags['album_artist_fixed'] + slash \
                              + tags['album_fixed'] + slash + tags['track_number_fixed'] + ' ' \
                              + tags['track_title_fixed'] + extension
    return track_download_directory


def get_ydl_opts(track_download_directory, download_format, use_cookie):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': download_format,
    }
    if download_format == '251':
        ydl_opts['postprocessors'] = [
            {
                'key': 'FFmpegExtractAudio',
            }
        ]
    if use_cookie or download_format == '141':
        ydl_opts['cookiefile'] = 'cookies.txt'
    ydl_opts['outtmpl'] = track_download_directory
    return ydl_opts


def download_track(ydl_opts, video_id):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download('youtu.be/' + video_id)


def apply_tags(track_download_directory, download_format, exclude_tags, tags):
    if 'all' not in exclude_tags:
        if '14' in download_format:
            file = MP4(track_download_directory).tags
            if 'album' not in exclude_tags:
                file['\xa9alb'] = tags['album']
            if 'album_artist' not in exclude_tags:
                file['aART'] = tags['album_artist']
            if 'artist' not in exclude_tags:
                file['\xa9ART'] = tags['artist']
            if 'artwork' not in exclude_tags:
                file['covr'] = [MP4Cover(tags['artwork'], imageformat=MP4Cover.FORMAT_JPEG)]
            if 'lyrics' not in exclude_tags:
                if tags['lyrics'] is not None:
                    file['\xa9lyr'] = tags['lyrics']
            if 'track_title' not in exclude_tags:
                file['\xa9nam'] = tags['track_title']
            if 'total_tracks' not in exclude_tags:
                file['trkn'] = [(0, tags['total_tracks'])]
                if 'track_number' not in exclude_tags:
                    file['trkn'] = [(tags['track_number'], tags['total_tracks'])]
            if 'track_number' not in exclude_tags:
                file['trkn'] = [(tags['track_number'], 0)]
                if 'total_tracks' not in exclude_tags:
                    file['trkn'] = [(tags['track_number'], tags['total_tracks'])]
            if 'rating' not in exclude_tags:
                file['rtng'] = [tags['rating']]
            if 'year' not in exclude_tags:
                file['\xa9day'] = tags['year']
            file.save(track_download_directory)
        else:
            file = music_tag.load_file(track_download_directory)
            if 'album' not in exclude_tags:
                file['album'] = tags['album']
            if 'album_artist' not in exclude_tags:
                file['album_artist'] = tags['album_artist']
            if 'artist' not in exclude_tags:
                file['artist'] = tags['artist']
            if 'artwork' not in exclude_tags:
                file['artwork'] = tags['artwork']
            if 'lyrics' not in exclude_tags:
                if tags['lyrics'] is not None:
                    file['lyrics'] = tags['lyrics']
            if 'total_tracks' not in exclude_tags:
                file['total_tracks'] = tags['total_tracks']
            if 'track_number' not in exclude_tags:
                file['track_number'] = tags['track_number']
            if 'track_title' not in exclude_tags:
                file['track_title'] = tags['track_title']
            if 'year' not in exclude_tags:
                file['year'] = tags['year']
            file.save()


def save_artwork(tags):
    if platform.system() == 'Windows':
        current_directory = '\\\\?\\' + os.getcwd()
        slash = '\\'
    else:
        current_directory = os.getcwd()
        slash = '/'
    cover_download_directory = current_directory + slash + 'YouTube Music' + slash + tags['album_artist_fixed'] + slash \
                              + tags['album_fixed'] + slash + 'Cover.jpg'
    with open(
            cover_download_directory, 'wb'
    ) as cover_file:
        cover_file.write(tags['artwork'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Python script to download YouTube Music tracks ')
    parser.add_argument(
        'url',
        help='Any valid YouTube Music URL.',
        nargs='+',
    )
    parser.add_argument(
        '--u',
        '--usecookie',
        action='store_true',
        help='Use cookie file named "cookies.txt" located at the current directory of this script to download tracks.',
    )
    parser.add_argument(
        "--f",
        "--format",
        choices=['141', '251', '140'],
        default='140',
        help='141 (AAC 256kbps), 251 (Opus 160kbps) or 140 (AAC 128kbps). A YouTube Music Premium cookie file named '
             '"cookies.txt" located at the current directory of this script is required to download format 141 tracks. '
             'Default format is 140',
    )
    parser.add_argument(
        '--e',
        '--excludetags',
        default=[],
        help='Any valid tag ("album", "album_artist", "artist", "artwork", "lyrics", "rating", "total_tracks", '
             '"track_number", "track_title" and "year") separated by comma with no spaces.',
    )
    parser.add_argument(
        '--s',
        '--saveartwork',
        action='store_true',
        help='Save artwork as "Cover.jpg" in download directory.',
    )
    parser.add_argument(
        '--a',
        '--artworksize',
        default='1200',
        help='"max" or any value from 1 to 16383. Default is "1200".'
    )
    args = parser.parse_args()
    url = args.url
    use_cookie = args.u
    download_format = args.f
    exclude_tags = args.e
    artwork_save = args.s
    artwork_size = args.a

    if exclude_tags:
        exclude_tags = exclude_tags.split(',')
        valid_tags = ['album', 'album_artist', 'artist', 'artwork', 'lyrics', 'rating', 'total_tracks', 'track_number',
                      'track_title', 'year']
        for i in range(len(exclude_tags)):
            if exclude_tags[i] not in valid_tags:
                parser.error(f'"{exclude_tags[i]}" is not a valid tag.')

    if artwork_size == 'max':
        artwork_size = '16383'
    else:
        try:
            if (int(artwork_size) < 0) or (int(artwork_size) > 16383):
                parser.error(f'"{artwork_size}" is not a valid artwork size.')
        except:
            parser.error(f'"{artwork_size}" is not a valid artwork size.')

    if use_cookie or download_format == '141':
        if not os.path.exists('cookies.txt'):
            parser.error('Cannot locate "cookies.txt" file.')

    error_count = 0
    video_id = []
    for a in range(len(url)):
        try:
            print(f'Checking URL ({a + 1} of {len(url)})...')
            video_id += get_video_id(url[a])
        except KeyboardInterrupt:
            exit()
        except:
            pass
    if not video_id:
        exit('No valid URL entered.')
    for i in range(len(video_id)):
        print(f'Getting tags ({str(i + 1)} of {str(len(video_id))})...')
        tags = get_tags(video_id[i], artwork_size)
        print(f'Downloading "{tags["track_title"]}" ({str(i + 1)} of {str(len(video_id))})...')
        track_download_directory = get_track_download_directory(download_format, tags)
        ydl_opts = get_ydl_opts(track_download_directory, download_format, use_cookie)
        download_track(ydl_opts, video_id[i])
        apply_tags(track_download_directory, download_format, exclude_tags, tags)
        if artwork_save:
            save_artwork(tags)
        print(f'Download finished ({str(i + 1)} of {str(len(video_id))})!')
