# Glomatico’s YouTube Music Downloader
A Python CLI app for downloading YouTube Music songs with tags from YouTube Music.

**Discord Server:** https://discord.gg/aBjMEZ9tnq

## Features
* **Precise metadata**: [YouTube Music API](https://github.com/sigma67/ytmusicapi) is used to get accurate metadata that yt-dlp alone can’t provide, like high-resolution square covers, lyrics, track numbers, and total track counts.
* **Synced Lyrics**: Download synced lyrics in LRC.
* **Artist Support**: Download all albums of an artist using their link.
* **Highly Customizable**: Extensive configuration options for advanced users.

## Prerequisites
* **Python 3.9 or higher** installed on your system.
* **FFmpeg** on your system PATH.
    * **Windows**: Download from [AnimMouse’s FFmpeg Builds](https://github.com/AnimMouse/ffmpeg-stable-autobuild/releases).
    * **Linux**: Download from [John Van Sickle’s FFmpeg Builds](https://johnvansickle.com/ffmpeg/).
* (Optional) The **cookies file** of your YouTube Music browser session in Netscape format (requires an active subscription).
    * **Firefox**: Use the [Export Cookies](https://addons.mozilla.org/addon/export-cookies-txt) extension.
    * **Chromium-based Browsers**: Use the [Open Cookies.txt](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif) extension.
    * With cookies, you can download **age-restricted content**, **private playlists**, and songs in **premium formats** if you have an active Premium subscription. You’ll have to set the cookies file path using the command line arguments or the config file (see [Configuration](#configuration)).
    * **YouTube cookies can expire very quickly**. As a workaround, export your cookies in an incognito/anonymous window so they don’t expire as quickly.
    *  **You may need to provide a PO token** by using the command line arguments or the config file if you encounter issues when downloading with cookies. To get a PO token, you can follow yt-dlp's instructions [here](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide).

### Optional dependencies
The following tools are optional but required for specific features. Add them to your system’s PATH or specify their paths using command-line arguments or the config file.
* [aria2](https://aria2.github.io/): Required for `aria2c` download mode.

## Installation
Install the package `gytmdl` using pip:
```bash
pip install gytmdl
```

## Usage
Run Gytmdl with the following command:
```bash
gytmdl [OPTIONS] URLS...
```

### Supported URL types
* Song
* Album
* Playlist
* Artist

**Songs that are not part of an album (standard YouTube videos) are not supported**. To make sure you get valid links, use YouTube Music for searching and enable filtering by songs, albums or artists.

### Examples
* Download a song:
    ```bash
    gytmdl "https://music.youtube.com/watch?v=3BFTio5296w"
    ```
* Download an album:
    ```bash
    gytmdl "https://music.youtube.com/playlist?list=OLAK5uy_lvpL_Gr_aVEq-LaivwJaSK5EbFd4HeamM"
    ```
* Choose which albums or singles to download from an artist:
    ```bash
    gytmdl "https://music.youtube.com/channel/UCwZEU0wAwIyZb4x5G_KJp2w"
    ```

### Interactive prompt controls
* **Arrow keys**: Move selection
* **Space**: Toggle selection
* **Ctrl + A**: Select all
* **Enter**: Confirm selection

## Configuration
Gytmdl can be configured by using the command line arguments or the config file.

The config file is created automatically when you run Gytmdl for the first time at `~/.gytmdl/config.json` on Linux/macOS and `%USERPROFILE%\.gytmdl\config.json` on Windows.

Config file values can be overridden using command line arguments.
| Command line argument / Config file key       | Description                                                                  | Default value                |
| --------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------- |
| `--save-cover`, `-s` / `save_cover`           | Save cover as a separate file.                                               | `false`                      |
| `--overwrite` / `overwrite`                   | Overwrite existing files.                                                    | `false`                      |
| `--read-urls-as-txt`, `-r` / -                | Interpret URLs as paths to text files containing URLs separated by newlines. | `false`                      |
| `--config-path` / -                           | Path to config file.                                                         | `<home>/.gytmdl/config.json` |
| `--log-level` / `log_level`                   | Log level.                                                                   | `INFO`                       |
| `--no-exceptions` / `no_exceptions`           | Don't print exceptions.                                                      | `false`                      |
| `--output-path`, `-o` / `output_path`         | Path to output directory.                                                    | `./YouTube Music`            |
| `--temp-path` / `temp_path`                   | Path to temporary directory.                                                 | `./temp`                     |
| `--cookies-path`, `-c` / `cookies_path`       | Path to .txt cookies file.                                                   | `null`                       |
| `--ffmpeg-path` / `ffmpeg_path`               | Path to FFmpeg binary.                                                       | `ffmpeg`                     |
| `--aria2c-path` / `aria2c_path`               | Path to aria2c binary.                                                       | `aria2c`                     |
| `--download-mode` / `download_mode`           | Download mode.                                                               | `ytdlp`                      |
| `--po-token` / `po_token`                     | Proof of Origin (PO) Token.                                                  | `null`                       |
| `--itag`, `-i` / `itag`                       | Itag (audio codec/quality).                                                  | `140`                        |
| `--cover-size` / `cover_size`                 | Cover size.                                                                  | `1200`                       |
| `--cover-format` / `cover_format`             | Cover format.                                                                | `jpg`                        |
| `--cover-quality` / `cover_quality`           | Cover JPEG quality.                                                          | `94`                         |
| `--template-folder` / `template_folder`       | Template of the album folders as a format string.                            | `{album_artist}/{album}`     |
| `--template-file` / `template_file`           | Template of the song files as a format string.                               | `{track:02d} {title}`        |
| `--template-date` / `template_date`           | Date tag template.                                                           | `%Y-%m-%dT%H:%M:%SZ`         |
| `--no-synced-lyrics` / `no_synced_lyrics`     | Don't save synced lyrics.                                                    | `false`                      |
| `--synced-lyrics-only` / `synced_lyrics_only` | Skip track download and only save synced lyrics.                             | `false`                      |
| `--exclude-tags`, `-e` / `exclude_tags`       | Comma-separated tags to exclude.                                             | `null`                       |
| `--truncate` / `truncate`                     | Maximum length of the file/folder names.                                     | `null`                       |
| `--no-config-file`, `-n` / -                  | Don't load the config file.                                                  | `false`                      |

### Tag variables
The following variables can be used in the template folder/file and/or in the `exclude_tags` list:
* `album`
* `album_artist`
* `artist`
* `cover`
* `date`
* `lyrics`
* `media_type`
* `rating`
* `title`
* `track`
* `track_total`
* `url`

### Itags (audio codec/quality)
* Free itags:
    * `140`: (AAC 128kbps)
    * `139`: (AAC 48kbps)
    * `251`: (Opus 128kbps)
    * `250`: (Opus 64kbps)
    * `249`: (Opus 48kbps)
* Premium itags (requires cookies and an active Premium subscription):
    * `141`: (AAC 256kbps)
    * `774`: (Opus 256kbps)

### Download modes
* `ytdlp`: Default download mode.
* `aria2c`: Faster than `ytdlp`.

### Cover formats
* `jpg`: Default format.
* `png`: Lossless format.
* `raw`: Raw cover without processing (requires `save_cover` to save separately).
