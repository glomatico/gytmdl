# Glomatico's YouTube Music Downloader
A Python to download YouTube Music songs with audio quality up to 256kpbs AAC m4a and with tags from YouTube Music.
## Basic usage
```
/path/to/python gytmdl.py <url>
```
Make sure to install ffmpeg in your system and the "requirements.txt" with pip.
For more information about usage, type this command.
```
/path/to/python gytmdl.py --help
```
## Getting "cookies.txt"
With a "cookies.txt" file, you can download age restricted tracks and download tracks in "141" (256kbps AAC m4a) format if you have a YouTube Music Premium subscription. To get one, you can use this Google Chrome extension in YouTube Music's page with your acccount logged: https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid. Place the generated file with the name "cookies.txt" at the script's current directory.
### Usage examples
Download using "cookies.txt":
```
path/to/python gytmdl.py --c <url>
```
Dowloading in "141" format:
```
path/to/python gytmdl.py --f 141 <url>
```
