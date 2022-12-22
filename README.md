# Glomatico's YouTube Music Downloader
A Python script to download YouTube Music tracks/albums/playlists with YouTube Music tags and audio quality up to 256kpbs AAC m4a following the iTunes standard.

## Setup
1. Install Python 3.8 or higher
2. Install the required packages using pip: 
    ```
    pip install -r requirements.txt
    ```
3. Add MP4Box to your PATH. You can get MP4Box here: https://gpac.wp.imt.fr/downloads/
5. (Optional) Get your cookies.txt
    * With cookies.txt, you can download age restricted tracks, private playlists and download tracks using 141 premium only itag (AAC 256kbps). You can get your cookies.txt by using the following Google Chrome extension on YouTube Music website: https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid. Make sure to export it as `cookies.txt` and put it on the same folder as the script or specify the location to it using the `--cookies-location` argument.

## Usage
```
python gytmdl.py [OPTIONS] [URLS]
```
Tracks are saved in `./YouTube Music` by default, but the directory can be changed using `--final-path` argument.
