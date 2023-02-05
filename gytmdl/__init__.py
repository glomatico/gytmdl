import shutil
import argparse
import traceback
from .gytmdl import Gytmdl

__version__ = '1.0'


def main():
    if not shutil.which('MP4Box'):
        raise Exception('MP4Box is not on PATH.')
    parser = argparse.ArgumentParser(
        description = 'Download YouTube Music songs/albums/playlists with tags from YouTube Music in 128kbps/256kbps AAC',
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'url',
        help='YouTube Music song/album/playlist URL(s)',
        nargs='*',
        metavar='<url>'
    )
    parser.add_argument(
        '-u',
        '--urls-txt',
        help = 'Read URLs from a text file',
        nargs = '?'
    )
    parser.add_argument(
        '-t',
        '--temp-path',
        default = 'temp',
        help = 'Temp path'
    )
    parser.add_argument(
        '-f',
        '--final-path',
        default = 'YouTube Music',
        help = 'Final path'
    )
    parser.add_argument(
        '-c',
        '--cookies-location',
        default = 'cookies.txt',
        help = 'Cookies location'
    )
    parser.add_argument(
        '-p',
        '--premium-quality',
        action = 'store_true',
        help = 'Download 256kbps AAC instead of 128kbps AAC'
    )
    parser.add_argument(
        '-s',
        '--skip-cleanup',
        action = 'store_true',
        help = 'Skip cleanup'
    )
    parser.add_argument(
        '-e',
        '--print-exceptions',
        action = 'store_true',
        help = 'Print exceptions'
    )
    parser.add_argument(
        '-v',
        '--version',
        action = 'version',
        version = f'%(prog)s {__version__}'
    )
    args = parser.parse_args()
    dl = Gytmdl(
        args.cookies_location, 
        args.premium_quality, 
        args.final_path, 
        args.temp_path, 
        args.skip_cleanup
    )
    if not args.url and not args.urls_txt:
        parser.error('you must specify an url or a text file using -u/--urls-txt.')
    if args.urls_txt:
        with open(args.urls_txt, 'r', encoding = 'utf8') as f:
            args.url = f.read().splitlines()
    download_queue = []
    error_count = 0
    for i, url in enumerate(args.url):
        try:
            download_queue.append(dl.get_download_queue(url.strip()))
        except KeyboardInterrupt:
            exit(1)
        except:
            error_count += 1
            print(f'* Failed to check URL {i + 1}.')
            if args.print_exceptions:
                traceback.print_exc()
    for i, url in enumerate(download_queue):
        for j, track in enumerate(url):
            print(f'Downloading "{track["title"]}" (track {j + 1} from URL {i + 1})...')
            try:
                ytmusic_watch_playlist = dl.get_ytmusic_watch_playlist(track['id'])
                if ytmusic_watch_playlist is None:
                    track['id'] = dl.search_track(track['title'])
                    ytmusic_watch_playlist = dl.get_ytmusic_watch_playlist(track['id'])
                tags = dl.get_tags(ytmusic_watch_playlist)
                temp_location = dl.get_temp_location(track['id'])
                dl.download(track['id'], temp_location)
                fixed_location = dl.get_fixed_location(track['id'])
                dl.fixup(temp_location, fixed_location)
                final_location = dl.get_final_location(tags)
                dl.make_final(final_location, fixed_location, tags)
            except KeyboardInterrupt:
                exit(1)
            except:
                error_count += 1
                print(f'* Failed to download "{track["title"]}" (track {j + 1} from URL {i + 1}).')
                if args.print_exceptions:
                    traceback.print_exc()
            dl.cleanup()
    print(f'Done ({error_count} error(s)).')
