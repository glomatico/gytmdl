import datetime
import functools
import re
import shutil
import subprocess
from pathlib import Path

import requests
from mutagen.mp4 import MP4, MP4Cover
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

MP4_TAGS_MAP = {
    "album": "\xa9alb",
    "album_artist": "aART",
    "artist": "\xa9ART",
    "comment": "\xa9cmt",
    "lyrics": "\xa9lyr",
    "media_type": "stik",
    "rating": "rtng",
    "release_date": "\xa9day",
    "title": "\xa9nam",
}


class Dl:
    def __init__(
        self,
        final_path: Path,
        temp_path: Path,
        cookies_location: Path,
        ffmpeg_location: str,
        itag: str,
        cover_size: int,
        cover_format: str,
        cover_quality: int,
        final_path_structure: str,
        exclude_tags: str,
        truncate: int,
        **kwargs,
    ):
        self.ytmusic = YTMusic()
        self.final_path = final_path
        self.temp_path = temp_path
        self.cookies_location = cookies_location
        self.ffmpeg_location = ffmpeg_location
        self.itag = itag
        self.cover_size = cover_size
        self.cover_format = cover_format
        self.cover_quality = cover_quality
        self.final_path_structure = final_path_structure
        self.exclude_tags = (
            [i.lower() for i in exclude_tags.split(",")]
            if exclude_tags is not None
            else []
        )
        self.truncate = None if truncate < 4 else truncate

    @functools.lru_cache()
    def get_ydl_extract_info(self, url):
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
        }
        if self.cookies_location is not None:
            ydl_opts["cookiefile"] = str(self.cookies_location)
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def get_download_queue(self, url):
        url = url.split("&")[0]
        download_queue = []
        ydl_extract_info = self.get_ydl_extract_info(url)
        if "youtube" not in ydl_extract_info["webpage_url"]:
            raise Exception("Not a YouTube URL")
        if "MPREb_" in ydl_extract_info["webpage_url_basename"]:
            ydl_extract_info = self.get_ydl_extract_info(ydl_extract_info["url"])
        if "playlist" in ydl_extract_info["webpage_url_basename"]:
            download_queue.extend(ydl_extract_info["entries"])
        if "watch" in ydl_extract_info["webpage_url_basename"]:
            download_queue.append(ydl_extract_info)
        return download_queue

    def get_artist(self, artist_list):
        if len(artist_list) == 1:
            return artist_list[0]["name"]
        return (
            ", ".join([i["name"] for i in artist_list][:-1])
            + f' & {artist_list[-1]["name"]}'
        )

    def get_ytmusic_watch_playlist(self, video_id):
        ytmusic_watch_playlist = self.ytmusic.get_watch_playlist(video_id)
        if not ytmusic_watch_playlist["tracks"][0]["length"] and ytmusic_watch_playlist[
            "tracks"
        ][0].get("album"):
            raise Exception("Track is not available")
        if not ytmusic_watch_playlist["tracks"][0].get("album"):
            return None
        return ytmusic_watch_playlist

    def search_track(self, title):
        return self.ytmusic.search(title, "songs")[0]["videoId"]

    @functools.lru_cache()
    def get_ytmusic_album(self, browse_id):
        return self.ytmusic.get_album(browse_id)

    @functools.lru_cache()
    def get_cover(self, url):
        return requests.get(url).content

    def get_tags(self, ytmusic_watch_playlist):
        video_id = ytmusic_watch_playlist["tracks"][0]["videoId"]
        ytmusic_album = self.ytmusic.get_album(
            ytmusic_watch_playlist["tracks"][0]["album"]["id"]
        )
        tags = {
            "album": ytmusic_album["title"],
            "album_artist": self.get_artist(ytmusic_album["artists"]),
            "artist": self.get_artist(ytmusic_watch_playlist["tracks"][0]["artists"]),
            "comment": f"https://music.youtube.com/watch?v={video_id}",
            "cover_url": f'{ytmusic_watch_playlist["tracks"][0]["thumbnail"][0]["url"].split("=")[0]}'
            + f'=w{self.cover_size}-l{self.cover_quality}-{"rj" if self.cover_format == "jpg" else "rp"}',
            "media_type": 1,
            "title": ytmusic_watch_playlist["tracks"][0]["title"],
            "track_total": ytmusic_album["trackCount"],
        }
        for i, video in enumerate(
            self.get_ydl_extract_info(
                f'https://www.youtube.com/playlist?list={ytmusic_album["audioPlaylistId"]}'
            )["entries"]
        ):
            if video["id"] == video_id:
                if ytmusic_album["tracks"][i]["isExplicit"]:
                    tags["rating"] = 1
                else:
                    tags["rating"] = 0
                tags["track"] = i + 1
                break
        if ytmusic_watch_playlist["lyrics"]:
            lyrics = self.ytmusic.get_lyrics(ytmusic_watch_playlist["lyrics"])["lyrics"]
            if lyrics is not None:
                tags["lyrics"] = lyrics
        if ytmusic_album.get("year"):
            tags["release_date"] = (
                datetime.datetime.strptime(ytmusic_album["year"], "%Y").isoformat()
                + "Z"
            )
            tags["year"] = ytmusic_album["year"]
        return tags

    def get_sanizated_string(self, dirty_string, is_folder):
        dirty_string = re.sub(r'[\\/:*?"<>|;]', "_", dirty_string)
        if is_folder:
            dirty_string = dirty_string[: self.truncate]
            if dirty_string.endswith("."):
                dirty_string = dirty_string[:-1] + "_"
        else:
            if self.truncate is not None:
                dirty_string = dirty_string[: self.truncate - 4]
        return dirty_string.strip()

    def get_temp_location(self, video_id):
        return self.temp_path / f"{video_id}.m4a"

    def get_fixed_location(self, video_id):
        return self.temp_path / f"{video_id}_fixed.m4a"

    def get_final_location(self, tags):
        final_location = self.final_path_structure.split("/")
        final_location = [
            self.get_sanizated_string(i.format(**tags), True)
            for i in final_location[:-1]
        ] + [
            self.get_sanizated_string(final_location[-1].format(**tags), False) + ".m4a"
        ]
        return self.final_path.joinpath(*final_location)

    def get_cover_location(self, final_location):
        return final_location.parent / f"Cover.{self.cover_format}"

    def download(self, video_id, temp_location):
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "fixup": "never",
            "format": self.itag,
            "outtmpl": str(temp_location),
        }
        if self.cookies_location is not None:
            ydl_opts["cookiefile"] = str(self.cookies_location)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download("music.youtube.com/watch?v=" + video_id)

    def fixup(self, temp_location, fixed_location):
        fixup = [
            self.ffmpeg_location,
            "-loglevel",
            "error",
            "-i",
            temp_location,
        ]
        if self.itag == "251":
            fixup.extend(
                [
                    "-f",
                    "mp4",
                ]
            )
        subprocess.run(
            [
                *fixup,
                "-movflags",
                "+faststart",
                "-c",
                "copy",
                fixed_location,
            ],
            check=True,
        )

    def apply_tags(self, fixed_location, tags):
        _tags = {
            v: [tags[k]]
            for k, v in MP4_TAGS_MAP.items()
            if k not in self.exclude_tags and tags.get(k) is not None
        }
        if not {"track", "track_total"} & set(self.exclude_tags):
            _tags["trkn"] = [[0, 0]]
        if "cover" not in self.exclude_tags:
            _tags["covr"] = [
                MP4Cover(
                    self.get_cover(tags["cover_url"]), imageformat=MP4Cover.FORMAT_JPEG
                )
            ]
        if "track" not in self.exclude_tags:
            _tags["trkn"][0][0] = tags["track"]
        if "track_total" not in self.exclude_tags:
            _tags["trkn"][0][1] = tags["track_total"]
        mp4 = MP4(fixed_location)
        mp4.clear()
        mp4.update(_tags)
        mp4.save()

    def move_to_final_location(self, fixed_location, final_location):
        final_location.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(fixed_location, final_location)

    def save_cover(self, tags, cover_location):
        with open(cover_location, "wb") as f:
            f.write(self.get_cover(tags["cover_url"]))

    def cleanup(self):
        shutil.rmtree(self.temp_path)
