from __future__ import annotations

import inspect
import json
import logging
import shutil
from enum import Enum
from pathlib import Path

import click
import colorama

from . import __version__
from .constants import EXCLUDED_CONFIG_FILE_PARAMS, X_NOT_FOUND_STRING, PREMIUM_FORMATS
from .custom_formatter import CustomFormatter
from .downloader import Downloader
from .enums import CoverFormat, DownloadMode
from .utils import color_text

downloader_sig = inspect.signature(Downloader.__init__)


def get_param_string(param: click.Parameter) -> str:
    if isinstance(param.default, Enum):
        return param.default.value
    elif isinstance(param.default, Path):
        return str(param.default)
    else:
        return param.default


def write_default_config_file(ctx: click.Context):
    ctx.params["config_path"].parent.mkdir(parents=True, exist_ok=True)
    config_file = {
        param.name: get_param_string(param)
        for param in ctx.command.params
        if param.name not in EXCLUDED_CONFIG_FILE_PARAMS
    }
    ctx.params["config_path"].write_text(json.dumps(config_file, indent=4))


def load_config_file(
    ctx: click.Context,
    param: click.Parameter,
    no_config_file: bool,
) -> click.Context:
    if no_config_file:
        return ctx
    if not ctx.params["config_path"].exists():
        write_default_config_file(ctx)
    config_file = dict(json.loads(ctx.params["config_path"].read_text()))
    for param in ctx.command.params:
        if (
            config_file.get(param.name) is not None
            and not ctx.get_parameter_source(param.name)
            == click.core.ParameterSource.COMMANDLINE
        ):
            ctx.params[param.name] = param.type_cast_value(ctx, config_file[param.name])
    return ctx


@click.command()
@click.help_option("-h", "--help")
@click.version_option(__version__, "-v", "--version")
# CLI specific options
@click.argument(
    "urls",
    nargs=-1,
    type=str,
    required=True,
)
@click.option(
    "--save-cover",
    "-s",
    is_flag=True,
    help="Save cover as a separate file.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing files.",
)
@click.option(
    "--read-urls-as-txt",
    "-r",
    is_flag=True,
    help="Interpret URLs as paths to text files containing URLs separated by newlines.",
)
@click.option(
    "--config-path",
    type=Path,
    default=Path.home() / ".gytmdl" / "config.json",
    help="Path to config file.",
)
@click.option(
    "--log-level",
    type=str,
    default="INFO",
    help="Log level.",
)
@click.option(
    "--no-exceptions",
    is_flag=True,
    help="Don't print exceptions.",
)
# Downloader specific options
@click.option(
    "--output-path",
    "-o",
    type=Path,
    default=downloader_sig.parameters["output_path"].default,
    help="Path to output directory.",
)
@click.option(
    "--temp-path",
    type=Path,
    default=downloader_sig.parameters["temp_path"].default,
    help="Path to temporary directory.",
)
@click.option(
    "--cookies-path",
    "-c",
    type=Path,
    default=downloader_sig.parameters["cookies_path"].default,
    help="Path to .txt cookies file.",
)
@click.option(
    "--ffmpeg-path",
    type=str,
    default=downloader_sig.parameters["ffmpeg_path"].default,
    help="Path to FFmpeg binary.",
)
@click.option(
    "--aria2c-path",
    type=str,
    default=downloader_sig.parameters["aria2c_path"].default,
    help="Path to aria2c binary.",
)
@click.option(
    "--download-mode",
    type=DownloadMode,
    default=downloader_sig.parameters["download_mode"].default,
    help="Download mode.",
)
@click.option(
    "--po-token",
    type=str,
    default=downloader_sig.parameters["po_token"].default,
    help="Proof of Origin (PO) Token.",
)
@click.option(
    "--itag",
    "-i",
    type=str,
    default=downloader_sig.parameters["itag"].default,
    help="Itag (audio codec/quality).",
)
@click.option(
    "--cover-size",
    type=int,
    default=downloader_sig.parameters["cover_size"].default,
    help="Cover size.",
)
@click.option(
    "--cover-format",
    type=CoverFormat,
    default=downloader_sig.parameters["cover_format"].default,
    help="Cover format.",
)
@click.option(
    "--cover-quality",
    type=int,
    default=downloader_sig.parameters["cover_quality"].default,
    help="Cover JPEG quality.",
)
@click.option(
    "--template-folder",
    type=str,
    default=downloader_sig.parameters["template_folder"].default,
    help="Template of the album folders as a format string.",
)
@click.option(
    "--template-file",
    type=str,
    default=downloader_sig.parameters["template_file"].default,
    help="Template of the song files as a format string.",
)
@click.option(
    "--template-date",
    type=str,
    default=downloader_sig.parameters["template_date"].default,
    help="Date tag template.",
)
@click.option(
    "--exclude-tags",
    "-e",
    type=str,
    default=downloader_sig.parameters["exclude_tags"].default,
    help="Comma-separated tags to exclude.",
)
@click.option(
    "--no-synced-lyrics",
    is_flag=True,
    help="Don't save synced lyrics.",
)
@click.option(
    "--synced-lyrics-only",
    is_flag=True,
    help="Skip track download and only save synced lyrics.",
)
@click.option(
    "--truncate",
    type=int,
    default=downloader_sig.parameters["truncate"].default,
    help="Maximum length of the file/folder names.",
)
# This option should always be last
@click.option(
    "--no-config-file",
    "-n",
    is_flag=True,
    callback=load_config_file,
    help="Don't load the config file.",
)
@click.version_option(__version__)
@click.help_option("-h", "--help")
def main(
    urls: tuple[str],
    save_cover: bool,
    overwrite: bool,
    read_urls_as_txt: bool,
    config_path: Path,
    log_level: str,
    no_exceptions: bool,
    output_path: Path,
    temp_path: Path,
    cookies_path: Path,
    ffmpeg_path: str,
    aria2c_path: str,
    download_mode: DownloadMode,
    po_token: str,
    itag: str,
    cover_size: int,
    cover_format: CoverFormat,
    cover_quality: int,
    template_folder: str,
    template_file: str,
    template_date: str,
    exclude_tags: str,
    no_synced_lyrics: bool,
    synced_lyrics_only: bool,
    truncate: int,
    no_config_file: bool,
):
    colorama.just_fix_windows_console()
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())
    logger.addHandler(stream_handler)
    if itag in PREMIUM_FORMATS and cookies_path is None:
        logger.critical("Cookies file is required for premium formats")
        return
    if po_token is None and cookies_path is not None:
        logger.warning("PO Token not provided, downloading may fail")
    if not shutil.which(ffmpeg_path):
        logger.critical(X_NOT_FOUND_STRING.format("FFmpeg", ffmpeg_path))
        return
    if download_mode == DownloadMode.ARIA2C and not shutil.which(aria2c_path):
        logger.critical(X_NOT_FOUND_STRING.format("aria2c", aria2c_path))
        return
    if cookies_path and not cookies_path.exists():
        logger.critical(X_NOT_FOUND_STRING.format("Cookies file", cookies_path))
        return
    if read_urls_as_txt:
        _urls = []
        for url in urls:
            if Path(url).exists():
                _urls.extend(Path(url).read_text().splitlines())
        urls = _urls
    logger.info("Starting Gytmdl")
    downloader = Downloader(
        output_path,
        temp_path,
        cookies_path,
        ffmpeg_path,
        aria2c_path,
        itag,
        download_mode,
        po_token,
        cover_size,
        cover_format,
        cover_quality,
        template_folder,
        template_file,
        template_date,
        exclude_tags,
        truncate,
    )
    error_count = 0
    download_queue = []
    for url_index, url in enumerate(urls, start=1):
        url_progress = color_text(f"URL {url_index}/{len(urls)}", colorama.Style.DIM)
        try:
            logger.info(f'({url_progress}) Checking "{url}"')
            download_queue = list(downloader.get_download_queue(url))
        except Exception as e:
            error_count += 1
            logger.error(
                f'({url_progress}) Failed to check "{url}"',
                exc_info=not no_exceptions,
            )
            continue
    for queue_index, queue_item in enumerate(download_queue, start=1):
        queue_progress = color_text(
            f"Track {queue_index}/{len(download_queue)} from URL {url_index}/{len(urls)}",
            colorama.Style.DIM,
        )
        try:
            logger.info(f'({queue_progress}) Downloading "{queue_item["title"]}"')
            logger.debug("Getting tags")
            ytmusic_watch_playlist = downloader.get_ytmusic_watch_playlist(
                queue_item["id"]
            )
            if not ytmusic_watch_playlist:
                logger.warning(
                    f"({queue_progress}) Track doesn't have an album or is not available, skipping"
                )
                continue
            tags = downloader.get_tags(ytmusic_watch_playlist)
            final_path = downloader.get_final_path(tags)
            synced_lyrics_path = downloader.get_synced_lyrics_path(final_path)
            if synced_lyrics_only:
                pass
            elif final_path.exists() and not overwrite:
                logger.warning(
                    f'({queue_progress}) Track already exists at "{final_path}", skipping'
                )
            else:
                video_id = ytmusic_watch_playlist["tracks"][0]["videoId"]
                track_temp_path = downloader.get_track_temp_path(video_id)
                remuxed_path = downloader.get_remuxed_path(video_id)
                cover_url = downloader.get_cover_url(ytmusic_watch_playlist)
                cover_file_extension = downloader.get_cover_file_extension(cover_url)
                cover_path = downloader.get_cover_path(final_path, cover_file_extension)
                logger.debug(f'Downloading to "{track_temp_path}"')
                downloader.download(video_id, track_temp_path)
                logger.debug(f'Remuxing to "{remuxed_path}"')
                downloader.remux(track_temp_path, remuxed_path)
                logger.debug("Applying tags")
                downloader.apply_tags(remuxed_path, tags, cover_url)
                logger.debug(f'Moving to "{final_path}"')
                downloader.move_to_output_path(remuxed_path, final_path)
            if no_synced_lyrics or not tags.get("lyrics"):
                pass
            elif synced_lyrics_path.exists() and not overwrite:
                logger.debug(
                    f'Synced lyrics already exists at "{synced_lyrics_path}", skipping'
                )
            else:
                logger.debug("Getting synced lyrics")
                synced_lyrics = downloader.get_synced_lyrics(ytmusic_watch_playlist)
                if synced_lyrics:
                    logger.debug(f'Saving synced lyrics to "{synced_lyrics_path}"')
                    downloader.save_synced_lyrics(synced_lyrics_path, synced_lyrics)
            if not save_cover:
                pass
            elif cover_path.exists() and not overwrite:
                logger.debug(f'Cover already exists at "{cover_path}", skipping')
            else:
                logger.debug(f'Saving cover to "{cover_path}"')
                downloader.save_cover(cover_path, cover_url)
        except Exception as e:
            error_count += 1
            logger.error(
                f'({queue_progress}) Failed to download "{queue_item["title"]}"',
                exc_info=not no_exceptions,
            )
        finally:
            if temp_path.exists():
                logger.debug(f'Cleaning up "{temp_path}"')
                downloader.cleanup_temp_path()
    logger.info(f"Done ({error_count} error(s))")
