from enum import Enum


class CoverFormat(Enum):
    JPG = "jpg"
    PNG = "png"


class DownloadMode(Enum):
    YTDLP = "ytdlp"
    ARIA2C = "aria2c"
