from enum import Enum


class CoverFormat(Enum):
    JPG = "jpg"
    PNG = "png"
    RAW = "raw"


class DownloadMode(Enum):
    YTDLP = "ytdlp"
    ARIA2C = "aria2c"
