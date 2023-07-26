import json
import logging
import shutil
from pathlib import Path

import click

from . import __version__
from .dl import Dl

EXCLUDED_PARAMS = (
    "urls",
    "config_location",
    "url_txt",
    "no_config_file",
    "version",
    "help",
)


def write_default_config_file(ctx: click.Context):
    ctx.params["config_location"].parent.mkdir(parents=True, exist_ok=True)
    config_file = {
        param.name: param.default
        for param in ctx.command.params
        if param.name not in EXCLUDED_PARAMS
    }
    with open(ctx.params["config_location"], "w") as f:
        f.write(json.dumps(config_file, indent=4))


def no_config_callback(
    ctx: click.Context, param: click.Parameter, no_config_file: bool
):
    if no_config_file:
        return ctx
    if not ctx.params["config_location"].exists():
        write_default_config_file(ctx)
    with open(ctx.params["config_location"], "r") as f:
        config_file = dict(json.load(f))
    for param in ctx.command.params:
        if (
            config_file.get(param.name) is not None
            and not ctx.get_parameter_source(param.name)
            == click.core.ParameterSource.COMMANDLINE
        ):
            ctx.params[param.name] = param.type_cast_value(ctx, config_file[param.name])
    return ctx


@click.command()
@click.argument(
    "urls",
    nargs=-1,
    type=str,
    required=True,
)
@click.option(
    "--final-path",
    "-f",
    type=Path,
    default="./YouTube Music",
    help="Path where the downloaded files will be saved.",
)
@click.option(
    "--temp-path",
    "-t",
    type=Path,
    default="./temp",
    help="Path where the temporary files will be saved.",
)
@click.option(
    "--cookies-location",
    "-c",
    type=Path,
    default=None,
    help="Location of the cookies file.",
)
@click.option(
    "--ffmpeg-location",
    type=Path,
    default="ffmpeg",
    help="Location of the FFmpeg binary.",
)
@click.option(
    "--config-location",
    type=Path,
    default=Path.home() / ".gytmdl" / "config.json",
    help="Config file location.",
)
@click.option(
    "--itag",
    "-i",
    type=click.Choice(["141", "251", "140"]),
    default="140",
    help="Itag (audio quality).",
)
@click.option(
    "--cover-size",
    type=click.IntRange(0, 16383),
    default=1200,
    help="Size of the cover.",
)
@click.option(
    "--cover-format",
    type=click.Choice(["jpg", "png"]),
    default="jpg",
    help="Format of the cover.",
)
@click.option(
    "--cover-quality",
    type=click.IntRange(1, 100),
    default=94,
    help="JPEG quality of the cover.",
)
@click.option(
    "--final-path-structure",
    type=str,
    default="{album_artist}/{album}/{track:02d} {title}",
    help="Final path structure as a format string.",
)
@click.option(
    "--exclude-tags",
    "-e",
    type=str,
    default=None,
    help="List of tags to exclude from file tagging separated by commas.",
)
@click.option(
    "--truncate",
    type=int,
    default=40,
    help="Maximum length of the file/folder names.",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Log level.",
)
@click.option(
    "--save-cover",
    "-s",
    is_flag=True,
    help="Save cover as a separate file.",
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help="Overwrite existing files.",
)
@click.option(
    "--print-exceptions",
    "-p",
    is_flag=True,
    help="Print exceptions.",
)
@click.option(
    "--url-txt",
    "-u",
    is_flag=True,
    help="Read URLs as location of text files containing URLs.",
)
@click.option(
    "--no-config-file",
    "-n",
    is_flag=True,
    callback=no_config_callback,
    help="Don't use the config file.",
)
@click.version_option(__version__)
@click.help_option("-h", "--help")
def cli(
    urls: tuple[str],
    final_path: Path,
    temp_path: Path,
    cookies_location: Path,
    ffmpeg_location: Path,
    config_location: Path,
    itag: str,
    cover_size: int,
    cover_format: str,
    cover_quality: int,
    final_path_structure: str,
    exclude_tags: str,
    truncate: int,
    log_level: str,
    save_cover: bool,
    overwrite: bool,
    print_exceptions: bool,
    url_txt: bool,
    no_config_file: bool,
):
    logging.basicConfig(
        format="[%(levelname)-8s %(asctime)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    if not shutil.which(str(ffmpeg_location)):
        logger.critical(f'FFmpeg not found at "{ffmpeg_location}"')
        return
    if cookies_location is not None and not cookies_location.exists():
        logger.critical(f'Cookies file not found at "{cookies_location}"')
        return
    if url_txt:
        logger.debug("Reading URLs from text files")
        _urls = []
        for url in urls:
            with open(url, "r") as f:
                _urls.extend(f.read().splitlines())
        urls = tuple(_urls)
    logger.debug("Starting downloader")
    dl = Dl(**locals())
    download_queue = []
    for i, url in enumerate(urls):
        try:
            logger.debug(f'Checking "{url}" (URL {i + 1}/{len(urls)})')
            download_queue.append(dl.get_download_queue(url))
        except Exception:
            logger.error(
                f"Failed to check URL {i + 1}/{len(urls)}", exc_info=print_exceptions
            )
    error_count = 0
    for i, url in enumerate(download_queue):
        for j, track in enumerate(url):
            logger.info(
                f'Downloading "{track["title"]}" (track {j + 1}/{len(url)} from URL {i + 1}/{len(download_queue)})'
            )
            try:
                logger.debug("Gettings tags")
                ytmusic_watch_playlist = dl.get_ytmusic_watch_playlist(track["id"])
                if ytmusic_watch_playlist is None:
                    logger.warning("Track is a video, using song equivalent")
                    track["id"] = dl.search_track(track["title"])
                    logger.debug(f'Video ID changed to "{track["id"]}"')
                    ytmusic_watch_playlist = dl.get_ytmusic_watch_playlist(track["id"])
                tags = dl.get_tags(ytmusic_watch_playlist)
                final_location = dl.get_final_location(tags)
                if final_location.exists() and not overwrite:
                    logger.warning(
                        f'File already exists at "{final_location}", skipping'
                    )
                    continue
                temp_location = dl.get_temp_location(track["id"])
                logger.debug(f'Downloading to "{temp_location}"')
                dl.download(track["id"], temp_location)
                fixed_location = dl.get_fixed_location(track["id"])
                logger.debug(f'Remuxing to "{fixed_location}"')
                dl.fixup(temp_location, fixed_location)
                logger.debug("Applying tags")
                dl.apply_tags(fixed_location, tags)
                logger.debug(f'Moving to "{final_location}"')
                dl.move_to_final_location(fixed_location, final_location)
                cover_location = dl.get_cover_location(final_location)
                if save_cover and not cover_location.exists():
                    logger.debug(f'Saving cover to "{cover_location}"')
                    dl.save_cover(tags, cover_location)
            except Exception:
                error_count += 1
                logger.error(
                    f'Failed to download "{track["title"]}" (track {j + 1}/{len(url)} from URL {i + 1}/{len(download_queue)})',
                    exc_info=print_exceptions,
                )
            finally:
                if temp_path.exists():
                    logger.debug(f'Cleaning up "{temp_path}"')
                    dl.cleanup()
    logger.info(f"Done ({error_count} error(s))")
