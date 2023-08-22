# Glomatico's YouTube Music Downloader
Download YouTube Music songs/albums/playlists with tags from YouTube Music in 256kbps AAC/128kbps Opus/128kbps AAC.

## Why not just use yt-dlp directly?
While this project uses yt-dlp under the hood, it has the advantage of utilizing [YouTube Music's API](https://github.com/sigma67/ytmusicapi) to get songs metadata. This includes information such as track number, square cover, lyrics, year, etc.

## Setup
1. Install Python 3.8 or higher
2. Install gytmdl with pip
    ```
    pip install gytmdl
    ```
3. Add FFmpeg to PATH or specify the location using the command line arguments or the config file (see [Configuration](#configuration))
4. (optional) Set a cookies file
   * By setting a cookies file, you can download age restricted tracks, private playlists and songs in 256kbps AAC if you are a premium user. You can export your cookies to a file by using the following Google Chrome extension on YouTube Music website: https://chrome.google.com/webstore/detail/gdocmgbfkjnnpapoeobnolbbkoibbcif.

## Usage examples
Download a song:
```
gytmdl "https://music.youtube.com/watch?v=3BFTio5296w"
```
Download an album:
```
gytmdl "https://music.youtube.com/playlist?list=OLAK5uy_lvpL_Gr_aVEq-LaivwJaSK5EbFd4HeamM"
```

## Configuration
gytmdl can be configured using the command line arguments or the config file. The config file is created automatically when you run gytmdl for the first time at `~/.gytmdl/config.json` on Linux and `%USERPROFILE%\.gytmdl\config.json` on Windows. Config file values can be overridden using command line arguments.
| Command line argument / Config file key | Description | Default value |
| --- | --- | --- |
| `-f`, `--final-path` / `final_path` | Path where the downloaded files will be saved. | `./YouTube Music` |
| `-t`, `--temp-path` / `temp_path` | Path where the temporary files will be saved. | `./temp` |
| `-c`, `--cookies-location` / `cookies_location` | Location of the cookies file. | `null` |
| `--ffmpeg-location` / `ffmpeg_location` | Location of the FFmpeg binary. | `ffmpeg` |
| `--config-location` / - | Location of the config file. | `<home folder>/.gytmdl/config.json` |
| `-i`, `--itag` / `itag` | Itag (audio quality). | `140` |
| `--cover-size` / `cover_size` | Size of the cover.  [0<=x<=16383] | `1200` |
| `--cover-format` / `cover_format` | Format of the cover. | `jpg` |
| `--cover-quality` / `cover_quality` | JPEG quality of the cover.  [1<=x<=100] | `94` |
| `--template-folder` / `template_folder` | Template of the album folders as a format string. | `{album_artist}/{album}` |
| `--template-file` / `template_file` | Template of the song files as a format string. | `{track:02d} {title}` |
| `-e`, `--exclude-tags` / `exclude_tags` | List of tags to exclude from file tagging separated by commas without spaces. | `null` |
| `--truncate` / `truncate` | Maximum length of the file/folder names. | `40` |
| `-l`, `--log-level` / `log_level` | Log level. | `INFO` |
| `-s`, `--save-cover` / `save_cover` | Save cover as a separate file. | `false` |
| `-o`, `--overwrite` / `overwrite` | Overwrite existing files. | `false` |
| `-p`, `--print-exceptions` / `print_exceptions` | Print exceptions. | `false` |
| `-u`, `--url-txt` / - | Read URLs as location of text files containing URLs. | `false` |
| `-n`, `--no-config-file` / - | Don't use the config file. | `false` |

### Itags
The following itags are available:
- `141` (256kbps AAC)
- `140` (128kbps AAC)
- `251` (128kbps Opus)

### Cover formats
Can be either `jpg` or `png`.

### Tag variables
The following variables can be used in the template folder/file and/or in the `exclude_tags` list:
- `album`
- `album_artist`
- `artist`
- `comment`
- `cover`
- `lyrics`
- `media_type`
- `rating`
- `release_date`
- `release_year`
- `title`
- `track`
- `track_total`
