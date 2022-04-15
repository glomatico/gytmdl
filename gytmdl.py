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
        ydl_extracted_info = ydl.extract_info(
            url,
            download=False,
        )
    if 'youtube' in ydl_extracted_info['extractor']:
        if 'MPREb' in ydl_extracted_info['webpage_url_basename']:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl_extracted_info = ydl.extract_info(
                    ydl_extracted_info['url'],
                    download=False,
                )
        if 'playlist' in ydl_extracted_info['webpage_url_basename']:
            video_id = []
            for i in range(len(ydl_extracted_info['entries'])):
                video_id.append(ydl_extracted_info['entries'][i]['id'])
            return video_id
        if 'watch' in ydl_extracted_info['webpage_url_basename']:
            return [ydl_extracted_info['id']]


def get_tags(video_id, artwork_size):
    ytmusic = YTMusic()
    ytmusic_watch_playlist = ytmusic.get_watch_playlist(video_id)
    ytmusic_album_details = ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
    album = ytmusic_album_details['title']
    album_fixed = album
    if len(ytmusic_album_details['artists']) == 1:
        album_artist = ytmusic_album_details['artists'][0]['name']
    else:
        album_artist_temp = []
        for a in range(len(ytmusic_album_details['artists'])):
            album_artist_temp.append(ytmusic_album_details['artists'][a]['name'])
        album_artist = ", ".join(album_artist_temp[:-1])
        album_artist += " & " + album_artist_temp[-1]
    album_artist_fixed = album_artist
    if len(ytmusic_watch_playlist['tracks'][0]['artists']) == 1:
        artist = ytmusic_watch_playlist['tracks'][0]['artists'][0]['name']
    else:
        artist_temp = []
        for a in range(len(ytmusic_watch_playlist['tracks'][0]['artists'])):
            artist_temp.append(ytmusic_watch_playlist['tracks'][0]['artists'][a]['name'])
        artist = ", ".join(artist_temp[:-1])
        artist += " & " + artist_temp[-1]
    artist_fixed = artist
    artwork = requests.get(ytmusic_album_details['thumbnails'][0]['url'].split('=')[0] + '=w' + artwork_size).content
    try:
        lyrics_id = ytmusic.get_lyrics(ytmusic_watch_playlist['lyrics'])
        lyrics = lyrics_id['lyrics']
    except:
        lyrics = None
    rating = 0
    track_number = 0
    track_number_fixed = 00
    total_tracks = ytmusic_album_details['trackCount']
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl_extracted_playlist_info = ydl.extract_info(
            'https://www.youtube.com/playlist?list='
            + ytmusic_album_details['audioPlaylistId'],
            download=False,
        )
    for i in range(len(ydl_extracted_playlist_info['entries'])):
        if ydl_extracted_playlist_info['entries'][i]['id'] == video_id:
            if ytmusic_album_details['tracks'][i]['isExplicit']:
                rating = 4
            else:
                rating = 0
            track_number = 1 + i
            track_number_fixed = '%02d' % (1 + i)
    track_title = ytmusic_watch_playlist['tracks'][0]['title']
    track_title_fixed = track_title
    year = ytmusic_album_details['year']
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


def get_track_download_directory(download_format, tags, simple_filename, folder_structure):
    if '14' in download_format:
        extension = 'm4a'
    else:
        extension = 'opus'
    if platform.system() == 'Windows':
        current_directory = '\\\\?\\' + os.getcwd()
        slash = '\\'
    else:
        current_directory = os.getcwd()
        slash = '/'
    if simple_filename:
        filename = f"{tags['artist_fixed']} - {tags['track_title_fixed']}.{extension}"
    else:
        filename = f"{tags['track_number_fixed']} {tags['track_title_fixed']}.{extension}"
    if folder_structure:
        track_download_directory = current_directory + slash + 'YouTube Music' + slash + tags['album_artist_fixed'] + slash \
                                   + tags['album_fixed'] + slash + filename
    else:
        track_download_directory = filename
    return track_download_directory


def get_ydl_opts(track_download_directory, download_format, use_cookie):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': download_format,
    }
    if use_cookie or download_format == '141':
        ydl_opts['cookiefile'] = 'cookies.txt'
    ydl_opts['outtmpl'] = track_download_directory
    return ydl_opts


def ydl_download(ydl_opts, video_id):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download('music.youtube.com/watch?v=' + video_id)


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


def fix_opus(track_download_directory):
    os.system(f'ffmpeg -i "{track_download_directory}" -c copy -f opus "{track_download_directory}.temp"')
    os.remove(track_download_directory)
    os.rename(track_download_directory + '.temp', track_download_directory)


def save_artwork(tags, folder_structure):
    if platform.system() == 'Windows':
        current_directory = '\\\\?\\' + os.getcwd()
        slash = '\\'
    else:
        current_directory = os.getcwd()
        slash = '/'
    if folder_structure:
        artwork_directory = current_directory + slash + 'YouTube Music' + slash + tags['album_artist_fixed'] + slash \
                            + tags['album_fixed'] + slash + 'Cover.jpg'
    else:
        artwork_directory = 'Cover.jpg'
    with open(
            artwork_directory, 'wb'
    ) as cover_file:
        cover_file.write(tags['artwork'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Python script to download YouTube Music tracks ')
    parser.add_argument(
        'url',
        help='Download YouTube Music track/album/playlist.',
        nargs='+',
        metavar='<url1> <url2> <ur3> ...'
    )
    parser.add_argument(
        '--u',
        '--usecookie',
        action='store_true',
        help='Use "cookies.txt" file.',
    )
    parser.add_argument(
        "--f",
        "--downloadformat",
        default='140',
        help='Set download format. Valid download formats are 128 (128kbps AAC m4a), 251 (128bps Opus opus) and 141 (256kbps AAC m4a).',
        metavar='<download format>'
    )
    parser.add_argument(
        '--e',
        '--excludetags',
        default=[],
        help='Set exclude tags. Valid tags are "all", "album", "album_artist", "artist", "artwork", "lyrics", "rating", "total_tracks", "track_number", "track_title" and "year"',
        metavar='<tag 1>,<tag 2>,<tag 3> ...'
    )
    parser.add_argument(
        '--s',
        '--saveartwork',
        action='store_true',
        help='Save artwork as "Cover.jpg" in track download directory.',
    )
    parser.add_argument(
        '--a',
        '--artworksize',
        default='1200',
        metavar='<size>',
        help='Set artwork size. Valid sizes are max (16383) or a number between 1 to 16383.'
    )
    parser.add_argument(
        '--n',
        '--nofolderstructure',
        action='store_false',
        help='Set tracks to download in current directory instead of YouTube/<Album Artist>/<Album>/<File>.',
    )
    parser.add_argument(
        '--p',
        '--simplefilename',
        action='store_true',
        help='Set tracks to download with the file name template "<Artist> - <Track Title>" instead of "<Track Number> <Track Title>".',
    )
    args = parser.parse_args()
    url = args.url
    use_cookie = args.u
    download_format = args.f
    exclude_tags = args.e
    artwork_save = args.s
    artwork_size = args.a
    simple_filename = args.p
    folder_structure = args.n

    valid_download_formats = ['140', '251', '141']
    if download_format not in valid_download_formats:
        parser.error(f'"{download_format}" is not a valid download format.')

    if exclude_tags:
        exclude_tags = exclude_tags.split(',')
        if 'all' not in exclude_tags:
            valid_exclude_tags = ['album', 'album_artist', 'artist', 'artwork', 'lyrics', 'rating', 'total_tracks', 'track_number',
                        'track_title', 'year']
            for i in range(len(exclude_tags)):
                if exclude_tags[i] not in valid_exclude_tags:
                    parser.error(f'"{exclude_tags[i]}" is not a valid tag.')

    if artwork_size == 'max':
        artwork_size = '16383'
    else:
        valid_artwork_sizes = [str(x + 1) for x in range(16383)]
        if artwork_size not in valid_artwork_sizes:
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
        try:
            print(f'Getting tags ({str(i + 1)} of {str(len(video_id))})...')
            tags = get_tags(video_id[i], artwork_size)
            print(f'Downloading "{tags["track_title"]}" ({str(i + 1)} of {str(len(video_id))})...')
            track_download_directory = get_track_download_directory(download_format, tags, simple_filename, folder_structure)
            ydl_opts = get_ydl_opts(track_download_directory, download_format, use_cookie)
            ydl_download(ydl_opts, video_id[i])
            if download_format == '251':
                fix_opus(track_download_directory)
            apply_tags(track_download_directory, download_format, exclude_tags, tags)
            if artwork_save:
                save_artwork(tags, folder_structure)
            print(f'Download finished ({str(i + 1)} of {str(len(video_id))})!')
        except KeyboardInterrupt:
            exit()
        except:
            print(f'* Download failed ({str(i + 1)} of {str(len(video_id))}).')
            error_count += 1
    print(f'All done ({error_count} error(s)).')
