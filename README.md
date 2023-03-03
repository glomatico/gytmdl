# Glomatico's YouTube Music Downloader
Download YouTube Music songs/albums/playlists with tags from YouTube Music in 128kbps AAC/128kbps Opus/256kbps AAC and following the iTunes standard.

## Setup
1. Install Python 3.8 or higher
2. Install gytmdl with pip
    ```
    pip install gytmdl
    ```
3. Add FFMPEG to your PATH. You can get it from here: https://ffmpeg.org/download.html
  * If you are on Windows you can move the `ffmpeg.exe` file to the same folder that you will run the script instead of adding it to your PATH.
4. (optional) Get your cookies.txt
    * With cookies.txt, you can download age restricted tracks, private playlists and songs in 256kbps AAC using `--itag 141` argument if you are a premium user. You can export your cookies by using the following Google Chrome extension on YouTube Music website with your account logged in: https://chrome.google.com/webstore/detail/gdocmgbfkjnnpapoeobnolbbkoibbcif. Make sure to export it as `cookies.txt` to the same folder that you will run the script.

## Usage
```
usage: gytmdl [-h] [-u [URLS_TXT]] [-t TEMP_PATH] [-f FINAL_PATH] [-c COOKIES_LOCATION] [-i {141,251,140}] [-o]
                   [-s] [-e] [-v]
                   [<url> ...]

Download YouTube Music songs/albums/playlists with tags from YouTube Music

positional arguments:
  <url>                 YouTube Music song/album/playlist URL(s) (default: None)

options:
  -h, --help            show this help message and exit
  -u [URLS_TXT], --urls-txt [URLS_TXT]
                        Read URLs from a text file (default: None)
  -t TEMP_PATH, --temp-path TEMP_PATH
                        Temp path (default: temp)
  -f FINAL_PATH, --final-path FINAL_PATH
                        Final path (default: YouTube Music)
  -c COOKIES_LOCATION, --cookies-location COOKIES_LOCATION
                        Cookies location (default: cookies.txt)
  -i {141,251,140}, --itag {141,251,140}
                        itag (quality). Can be 141 (256kbps AAC, requires cookies), 251 (128kbps Opus) or 140 (128kbps
                        AAC) (default: 140)
  -o, --overwrite       Overwrite existing files (default: False)
  -s, --skip-cleanup    Skip cleanup (default: False)
  -e, --print-exceptions
                        Print exceptions (default: False)
  -v, --version         show program's version number and exit
```
