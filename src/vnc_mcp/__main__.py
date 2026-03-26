"""vnc-mcp

Copyright (C) 2025  Parker Wahle

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501, B950, D415

# Breaks some typer work with the options
# from __future__ import annotations

import json
from typing import Annotated
from typing import Optional

import typer

# from envwrap import envwrap
from pyvnc import VNCConfig
from typer import Argument
from typer import Option

from .mcp import create_mcp_server
from .utils.asyncio import make_sync


cli = typer.Typer()


@cli.command()
@make_sync
async def main(
    *,
    host: Annotated[
        str,
        Argument(
            envvar="VNCMCP_HOST",
            show_envvar=True,
            help="Hostname, address, or FQDN of the VNC server that will be connected to.",
        ),
    ] = "localhost",
    port: Annotated[
        int,
        Argument(
            envvar="VNCMCP_PORT", show_envvar=True, help="Port that the VNC server is listening on."
        ),
    ] = 5900,
    timeout: Annotated[
        float,
        Option(
            envvar="VNCMCP_TIMEOUT",
            show_envvar=True,
            help="How long the client will wait to connect. "
            "Note that VNC servers that require the end user to accept a connection may benefit from a longer "
            "timeout to accommodate waiting for the user.",
        ),
    ] = 5.0,
    password: Annotated[
        Optional[str],
        Option(
            envvar="VNCMCP_PASSWORD",
            show_envvar=True,
            help="Password that will be used to authenticate with the server if an authentication challenge is presented.",
        ),
    ] = None,
    username: Annotated[
        Optional[str],
        Option(
            envvar="VNCMCP_USERNAME",
            show_envvar=True,
            help="Username that will be used if the VNC server asks for a username. "
            "If your VNC server does not for a username and only asks for a password, only specify the password.",
        ),
    ] = None,
) -> None:
    """
    Spawns an MCP server over stdi/o that can be used to interface with the VNC client.

    Please note that the VNC server the client connects to must support basic VNC authentication. Servers implementing
    ARD (Apple Remote Desktop) are not supported.
    """
    vnc_config = VNCConfig(
        host=host,
        port=port,
        username=username,
        password=password,
    )
    mcp_server = await create_mcp_server(vnc_config)
    # enter the main loop of the MCP server
    await mcp_server.run_stdio_async()


if __name__ == "__main__":  # pragma: no cover
    cli()

__all__ = ("cli",)
