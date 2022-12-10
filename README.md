# Glomatico's YouTube Music Downloader
A Python script to download YouTube Music tracks/albums/playlists with YouTube Music tags and audio quality up to 256kpbs AAC m4a following the iTunes standard.

## Basic usage
```
/path/to/python gytmdl.py <url>
```
Use `--help` argument to see all available options. 

Make sure to add MP4Box to PATH and install "requirements.txt" with pip before running this program. MP4Box can be downloaded from https://gpac.wp.imt.fr/downloads/.

## Cookies
If you want to download age restricted tracks, private playlists or download tracks using 141 premium only itag (AAC 256kbps), use this Chrome extension in YouTube Music's website to grab your cookies and use in the script: https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid. Default cookies location is "./cookies.txt", but can be changed using `--cookies-location` argument.
