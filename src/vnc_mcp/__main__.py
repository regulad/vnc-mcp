"""vnc-mcp

Copyright (C) 2025  Parker Wahle

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501, B950, D415

from __future__ import annotations

import json

import typer

from ._assets import RESOURCES
from ._metadata import __version__


cli = typer.Typer()


@cli.command()
def main() -> None:
    data = RESOURCES / "data.json"
    with data.open() as json_fp:
        parsed = json.load(json_fp)
    status = parsed["status"]
    print(__version__ + " " + typer.style(status, fg=typer.colors.GREEN, bold=True))


if __name__ == "__main__":  # pragma: no cover
    cli()

__all__ = ("cli",)
