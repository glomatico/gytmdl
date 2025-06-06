from pathlib import Path

import click
import colorama


def color_text(text: str, color) -> str:
    return color + text + colorama.Style.RESET_ALL


def prompt_path(is_file: bool, initial_path: Path) -> Path:
    path_validator = click.Path(
        exists=True,
        file_okay=is_file,
        dir_okay=not is_file,
        path_type=Path,
    )
    while True:
        try:
            path_obj = path_validator.convert(initial_path.absolute(), None, None)
            break
        except click.BadParameter as e:
            path_str = click.prompt(
                str(e)
                + " Move it to that location, type the path or drag and drop it here. Then, press enter to continue"
            )
            path_str = path_str.strip('"')
            initial_path = Path(path_str)
    return path_obj
