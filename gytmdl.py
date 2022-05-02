from ytmusicapi import YTMusic
import yt_dlp
import requests
import platform
import os
from mutagen.mp4 import MP4, MP4Cover
import music_tag
import argparse
#import traceback

ytmusic = YTMusic()


def get_video_id(url):
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl_extracted_info = ydl.extract_info(
            url,
            download=False
        )
    if 'youtube' in ydl_extracted_info['extractor']:
        if 'MPREb' in ydl_extracted_info['webpage_url_basename']:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl_extracted_info = ydl.extract_info(
                    ydl_extracted_info['url'],
                    download=False
                )
        if 'playlist' in ydl_extracted_info['webpage_url_basename']:
            video_id = []
            for i in range(len(ydl_extracted_info['entries'])):
                video_id.append(ydl_extracted_info['entries'][i]['id'])
            return video_id
        if 'watch' in ydl_extracted_info['webpage_url_basename']:
            if len(ydl_extracted_info['id']) > 11:
                return [ydl_extracted_info['entries'][0]['id']]
            return [ydl_extracted_info['id']]
    raise Exception()


def get_tags(video_id):
    ytmusic_watch_playlist = ytmusic.get_watch_playlist(video_id)
    ytmusic_album_details = ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
    album = ytmusic_album_details['title']
    if len(ytmusic_album_details['artists']) == 1:
        album_artist = ytmusic_album_details['artists'][0]['name']
    else:
        temp_album_artist = []
        for a in range(len(ytmusic_album_details['artists'])):
            temp_album_artist.append(ytmusic_album_details['artists'][a]['name'])
        album_artist = ', '.join(temp_album_artist[:-1])
        album_artist += f' & {temp_album_artist[-1]}'
    if len(ytmusic_watch_playlist['tracks'][0]['artists']) == 1:
        artist = ytmusic_watch_playlist['tracks'][0]['artists'][0]['name']
    else:
        temp_artist = []
        for a in range(len(ytmusic_watch_playlist['tracks'][0]['artists'])):
            temp_artist.append(ytmusic_watch_playlist['tracks'][0]['artists'][a]['name'])
        artist = ", ".join(temp_artist[:-1])
        artist += f' & {temp_artist[-1]}'
    try:
        lyrics_id = ytmusic.get_lyrics(ytmusic_watch_playlist['lyrics'])
        lyrics = lyrics_id['lyrics']
    except:
        lyrics = None
    rating = 0
    track_number = 0
    total_tracks = ytmusic_album_details['trackCount']
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl_extracted_info = ydl.extract_info(
            f'https://www.youtube.com/playlist?list={ytmusic_album_details["audioPlaylistId"]}',
            download=False,
        )
    for i in range(len(ydl_extracted_info['entries'])):
        if ydl_extracted_info['entries'][i]['id'] == video_id:
            if ytmusic_album_details['tracks'][i]['isExplicit']:
                rating = 4
            else:
                rating = 0
            track_number = 1 + i
    track_title = ytmusic_watch_playlist['tracks'][0]['title']
    year = ytmusic_album_details['year']
    return {
        'album': album,
        'album_artist': album_artist,
        'artist': artist,
        'lyrics': lyrics,
        'rating': rating,
        'total_tracks': total_tracks,
        'track_number': track_number,
        'track_title': track_title,
        'video_id': video_id,
        'year': year
    }


def get_artwork_url(video_id, artwork_size = '1200'):
    ytmusic_watch_playlist = ytmusic.get_watch_playlist(video_id)
    artwork_url = f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}=w{artwork_size}'
    return artwork_url


def get_artwork(artwork_url):
    artwork = requests.get(artwork_url).content
    return artwork


def get_sanizated_string(string, is_folder = False):
    illegal_characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for a in range(len(illegal_characters)):
        string = string.replace(illegal_characters[a], '_')
    if is_folder:
        if string[-1:] == '.':
            string = string[:-1] + '_'
    return string


def get_slash():
    if platform.system() == 'Windows':
        return '\\'
    else:
        return '/'


def get_download_directory(tags = [], directory_structure = False):
    if platform.system() == 'Windows':
        download_directory = f'\\\\?\\{os.getcwd()}'
    else:
        download_directory = os.getcwd()
    slash = get_slash()
    if directory_structure:
        fixed_album_artist = get_sanizated_string(tags['album_artist'], True)
        fixed_album = get_sanizated_string(tags['album'], True)
        download_directory += f'{slash}YouTube Music{slash}{fixed_album_artist}{slash}{fixed_album}'
    return download_directory


def get_track_filename(download_format, tags, simple_filename = True):
    if '14' in download_format:
        file_extension = '.m4a'
    else:
        file_extension = '.opus'
    fixed_title = get_sanizated_string(tags['track_title'])
    if simple_filename:
        fixed_artist = get_sanizated_string(tags['artist'])
        track_filename = f'{fixed_artist} - {fixed_title}'
    else:
        fixed_track_number = f'{tags["track_number"]:02d}'
        track_filename = f'{fixed_track_number} {fixed_title}'
    track_filename += file_extension
    return track_filename


def get_ydl_opts(track_download_directory, download_format, use_cookie):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'overwrites': True,
        'format': download_format,
        'outtmpl': track_download_directory
    }
    if use_cookie or download_format == '141':
        if not os.path.exists('cookies.txt'):
            raise Exception()
        ydl_opts['cookiefile'] = 'cookies.txt'
    return ydl_opts


def ydl_download(ydl_opts, video_id):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(f'music.youtube.com/watch?v={video_id}')


def fix_opus(track_download_directory):
    os.system(f'ffmpeg -loglevel 0 -i "{track_download_directory}" -c copy -f opus "{track_download_directory}.temp"')
    os.remove(track_download_directory)
    os.rename(track_download_directory + '.temp', track_download_directory)


def apply_tags(track_download_directory, exclude_tags, tags, artwork):
    if 'all' not in exclude_tags:
        if track_download_directory[-3:] == 'm4a':
            file = MP4(track_download_directory).tags
            if 'album' not in exclude_tags:
                file['\xa9alb'] = tags['album']
            if 'album_artist' not in exclude_tags:
                file['aART'] = tags['album_artist']
            if 'artist' not in exclude_tags:
                file['\xa9ART'] = tags['artist']
            if 'artwork' not in exclude_tags:
                file['covr'] = [MP4Cover(artwork, imageformat=MP4Cover.FORMAT_JPEG)]
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
                file['artwork'] = artwork
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


def download_artwork(download_directory, artwork):
    slash = get_slash()
    artwork_download_directory = f'{download_directory}{slash}Cover.jpg'
    with open(artwork_download_directory, 'wb') as artwork_file:
        artwork_file.write(artwork)


def delete_track_file(track_download_directory, only_temp = True):
    if only_temp:
        if os.path.exists(track_download_directory + '.temp'):
            os.remove(track_download_directory + '.temp')
    else:
        if os.path.exists(track_download_directory + '.temp'):
            os.remove(track_download_directory + '.temp')
        if os.path.exists(track_download_directory):
            os.remove(track_download_directory)


def main():
    parser = argparse.ArgumentParser(description='A Python script to download YouTube Music tracks with YouTube Music tags.')
    parser.add_argument(
        'url',
        help='Download YouTube Music track/album/playlist.',
        nargs='+',
        metavar='<url 1> <url 2> <url 3> ...'
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
        help='Set download format. Valid download formats are 140 (128kbps AAC m4a), 251 (128bps Opus opus) and 141 (256kbps AAC m4a).',
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
        '--d',
        '--downloadartwork',
        action='store_true',
        help='Save artwork as "Cover.jpg" in track download directory.',
    )
    parser.add_argument(
        '--a',
        '--artworksize',
        default='1200',
        metavar='<size>',
        help='Set artwork size. Valid sizes are max (16383) or a number between 1 and 16383.'
    )
    parser.add_argument(
        '--n',
        '--nodirectorytructure',
        action='store_false',
        help='Download in "./" directory instead of "./YouTube/<Album Artist>/<Album>/<File>".',
    )
    parser.add_argument(
        '--s',
        '--simplefilename',
        action='store_true',
        help='Use "<Artist> - <Track Title>" track filename template instead of "<Track Number> <Track Title>".',
    )
    args = parser.parse_args()
    url = args.url
    use_cookie = args.u
    download_format = args.f
    exclude_tags = args.e
    artwork_download = args.d
    artwork_size = args.a
    simple_filename = args.s
    directory_structure = args.n
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
    slash = get_slash()
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
            tags = get_tags(video_id[i])
            print(f'Downloading "{tags["track_title"]}" ({str(i + 1)} of {str(len(video_id))})...')
            artwork_url = get_artwork_url(video_id[i], artwork_size)
            artwork = get_artwork(artwork_url)
            download_directory = get_download_directory(tags, directory_structure)
            track_filename = get_track_filename(download_format, tags, simple_filename)
            track_download_directory = download_directory + slash + track_filename
            ydl_opts = get_ydl_opts(track_download_directory, download_format, use_cookie)
            ydl_download(ydl_opts, video_id[i])
            if download_format == '251':
                fix_opus(track_download_directory)
            apply_tags(track_download_directory, exclude_tags, tags, artwork)
            if artwork_download:
                download_artwork(download_directory, artwork)
            print(f'Download finished ({str(i + 1)} of {str(len(video_id))})!')
            delete_track_file(track_download_directory)
        except KeyboardInterrupt:
            exit()
        except:
            print(f'* Download failed ({str(i + 1)} of {str(len(video_id))}).')
            error_count += 1
            #traceback.print_exc()
    print(f'All done ({error_count} error(s)).')


if __name__ == '__main__':
    main()
