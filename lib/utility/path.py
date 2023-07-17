import datetime
from pathlib import Path

from .define_class import PURE_OR_APPEND


def datetimeChangingFolder(parentPath: Path,
                           mode: PURE_OR_APPEND = "pure") -> Path:
    if mode == "pure":
        return parentPath.joinpath(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    if mode == "append":
        return parentPath.joinpath(f"{parentPath.name}_"f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    print(f"Mode {mode} not supported")
    return Path()
