# Glomatico's YouTube Music Downloader
A Python script to download YouTube Music songs/albums/playlists in 128kbps/256kbps AAC with YouTube Music tags and following the iTunes standard.

## Setup
1. Install Python 3.8 or higher
2. Install the required packages using pip: 
    ```
    pip install -r requirements.txt
    ```
3. Add MP4Box to your PATH. You can get MP4Box here: https://gpac.wp.imt.fr/downloads/
5. (Optional) Get your cookies.txt
    * With cookies.txt, you can download age restricted tracks, private playlists and songs in 256kbps AAC using `--premium-quality` argument. You can export your cookies by using the following Google Chrome extension on YouTube Music website with your account logged in: https://chrome.google.com/webstore/detail/gdocmgbfkjnnpapoeobnolbbkoibbcif. Make sure to export it as `cookies.txt` to the same directory as the script or specify the location using `--cookies-location` argument.

## Usage
```
python gytmdl.py [OPTIONS] [URLS]
```
Tracks are saved in `./YouTube Music` by default, but the directory can be changed using `--final-path` argument.

Use `--help` argument to see all available options.
