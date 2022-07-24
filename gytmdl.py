from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL
import requests
import platform
import os
import music_tag
from mutagen.mp4 import MP4, MP4Cover
import argparse

ytmusic = YTMusic()

ydl_opts_extract_info = {
    'extract_flat': True,
    'skip_download': True,
    'quiet': True,
    'no_warnings': True
}

ydl_opts_download = {
    'cookiefile': 'cookies.txt',
    'quiet': True,
    'no_warnings': True,
    'overwrites': True,
    'fixup': 'never'
}


def get_download_info(url):
    url = url.split('&')[0]
    download_info = {}
    with YoutubeDL(ydl_opts_extract_info) as ydl:
        ydl_extract_info = ydl.extract_info(
            url,
            download = False
        )
    if 'youtube' in ydl_extract_info['extractor']:
        if 'MPREb' in ydl_extract_info['webpage_url_basename']:
            with YoutubeDL(ydl_opts_extract_info) as ydl:
                ydl_extract_info = ydl.extract_info(
                    ydl_extract_info['url'],
                    download = False
                )
        if 'playlist' in ydl_extract_info['webpage_url_basename']:
            for i in range(len(ydl_extract_info['entries'])):
                download_info[ydl_extract_info['entries'][i]['id']] = ydl_extract_info['entries'][i]['title']
            return download_info
        if 'watch' in ydl_extract_info['webpage_url_basename']:
            download_info[ydl_extract_info['id']] = ydl_extract_info['title']
            return download_info
    raise Exception()


def get_artist_string(artists):
    if len(artists) == 1:
        return artists[0]['name']
    temp_artist = []
    for i in range(len(artists)):
        temp_artist.append(artists[i]['name'])
    artist = ', '.join(temp_artist[:-1])
    artist += f' & {temp_artist[-1]}'
    return artist


def get_tags(video_id):
    ytmusic_watch_playlist = ytmusic.get_watch_playlist(video_id)
    ytmusic_album_details = ytmusic.get_album(ytmusic_watch_playlist['tracks'][0]['album']['id'])
    album = ytmusic_album_details['title']
    album_artist = get_artist_string(ytmusic_album_details['artists'])
    artist = get_artist_string(ytmusic_watch_playlist['tracks'][0]['artists'])
    comment = f'https://music.youtube.com/watch?v={video_id}'
    cover = requests.get(f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}=w1200').content
    try:
        lyrics_id = ytmusic.get_lyrics(ytmusic_watch_playlist['lyrics'])
        lyrics = lyrics_id['lyrics']
    except:
        lyrics = None
    title = ytmusic_watch_playlist['tracks'][0]['title']
    total_tracks = ytmusic_album_details['trackCount']
    with YoutubeDL(ydl_opts_extract_info) as ydl:
        ydl_extracted_info = ydl.extract_info(
            f'https://www.youtube.com/playlist?list={ytmusic_album_details["audioPlaylistId"]}',
            download = False,
        )
    for i in range(len(ydl_extracted_info['entries'])):
        if ydl_extracted_info['entries'][i]['id'] == video_id:
            if ytmusic_album_details['tracks'][i]['isExplicit']:
                rating = 4
            else:
                rating = 0
            track_number = 1 + i
            break
    year = ytmusic_album_details['year']
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


def get_sanizated_string(string, is_folder = False):
    illegal_characters = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for a in range(len(illegal_characters)):
        string = string.replace(illegal_characters[a], '_')
    if is_folder:
        if string[-1:] == '.':
            string = string[:-1] + '_'
    return string


def get_download_location(tags, download_format):
    if download_format == '251':
        file_extension = 'opus'
    else:
        file_extension = 'm4a'
    if platform.system() == 'Windows':
        download_location = f'\\\\?\\{os.getcwd()}'
        slash = '\\'
    else:
        download_location = os.getcwd()
        slash = '/'
    download_location += f'{slash}YouTube Music{slash}{get_sanizated_string(tags["album_artist"], True)}{slash}{get_sanizated_string(tags["album"], True)}{slash}{tags["track_number"]:02d} {get_sanizated_string(tags["title"])}.{file_extension}'
    return download_location


def download(download_format, temp_download_location, video_id):
    ydl_opts_download['format'] = download_format
    ydl_opts_download['outtmpl'] = temp_download_location
    with YoutubeDL(ydl_opts_download) as ydl:
        ydl.download(f'music.youtube.com/watch?v={video_id}')


def fixup(temp_download_location, download_location):
    os.system(f'ffmpeg -loglevel 0 -i "{temp_download_location}" -c copy "{download_location}"')
    os.remove(temp_download_location)


def apply_tags(download_format, download_location, tags):
    if download_format == '251':
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
        file['trkn'] = [(tags['track_number'], tags['total_tracks'])]
        file['rtng'] = [tags['rating']]
        file['\xa9day'] = tags['year']
        file.save(download_location)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'A Python script to download YouTube Music tracks with YouTube Music tags.')
    parser.add_argument(
        'url',
        help='Download YouTube Music track/album/playlist.',
        nargs='+',
        metavar='<url 1> <url 2> <url 3> ...'
    )
    parser.add_argument(
        "-d",
        "--downloadformat",
        default = '140',
        help = 'Set download format. Valid download formats are 141 (256kbps AAC m4a), 251 (128bps Opus opus) and 140 (128kbps AAC m4a).',
        metavar = '<download format>'
    )
    args = parser.parse_args()
    download_format = args.downloadformat
    url = args.url

    video_id = []
    title = []
    for i in range(len(url)):
        try:
            print(f'Checking URL ({i + 1} of {len(url)})...')
            download_info = get_download_info(url[i])
            video_id += (list(download_info.keys()))
            title += (list(download_info.values()))
        except:
            continue
    if not video_id:
        exit('No valid URL entered.')

    error_count = 0
    for i in range(len(video_id)):
        try:
            print(f'Downloading "{title[i]}" ({str(i + 1)} of {str(len(video_id))})...')
            tags = get_tags(video_id[i])
            download_location = get_download_location(tags, download_format)
            temp_download_location = download_location + '.temp'
            download(download_format, temp_download_location, video_id[i])
            fixup(temp_download_location, download_location)
            apply_tags(download_format, download_location, tags)
        except KeyboardInterrupt:
            exit()
        except:
            print(f'* Failed to dowload "{title[i]}" ({str(i + 1)} of {str(len(video_id))}).')
            error_count += 1

    print(f'All done ({error_count} error(s)).')
