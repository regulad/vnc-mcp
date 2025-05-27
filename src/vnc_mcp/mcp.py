"""vnc-mcp

Copyright (C) 2025  Parker Wahle

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501, B950, D415

from __future__ import annotations

from io import BytesIO

import numpy as np
from mcp.server import FastMCP
from mcp.server.fastmcp import Image as MCPImage
from PIL import Image as PILImage
from pyvnc import AsyncVNCClient
from pyvnc import Rect

from .utils.asyncio import make_async


@make_async
def _convert_rgba_np_ndarray_to_mcpimage(array: np.ndarray) -> MCPImage:
    pilimage = PILImage.fromarray(array, "RGBA")
    with BytesIO() as bio:
        pilimage.save(bio, "png")
        bio.seek(0)
        image_png_bytes = bio.read()
        return MCPImage(data=image_png_bytes, format="png")


def create_mcp_server(vnc_client: AsyncVNCClient) -> FastMCP:
    """
    Creates a final FastMCP server initialized with the created AsyncVNCClient.
    """

    mcp_server = FastMCP(
        "VNC Client",
        instructions="This VNC client can be used to view the contents of and control the user's computer. "
        "Please, use it responsibly.",
    )

    # When declaring a tool, the description will default to the docstring of the function.

    # Tools/resources to provide:
    # According to Claude (funny, I know), only tools should be used for this application.
    # I doubt anybody will be using this tool with anything besides claude. mcphost might support resources, but I doubt it.

    #     Get screen resolution
    @mcp_server.tool()
    def get_screen_resolution() -> str:
        """
        Returns a string containing the width times height of the VNC session's workspace.

        Please note that this may not actually be the real resolution of the user's computer monitor.

        This resolution should be used for all calls to tools that take a resolution or position.
        """

        relative_resolution = vnc_client.get_relative_resolution()
        return f"{relative_resolution[0]}x{relative_resolution[1]}"

    #     Whole screen image
    @mcp_server.tool()
    async def get_whole_screen_image() -> MCPImage:
        """
        Gets an image of the entire VNC session's workspace.

        If you are only interested in a certain subrectangle of the workspace,
        consider using the get_rectangle_of_screen method.

        Please note that the resolution of the image does not match the resolution that is used to select points
        on the workspace.

        Please use get_screen_resolution to get the actual "relative" workspace resolution.
        """

        raw_rgba_array = await vnc_client.capture()
        return await _convert_rgba_np_ndarray_to_mcpimage(raw_rgba_array)

    #     Relative rectangle image
    @mcp_server.tool()
    async def get_rectangle_of_screen(
        top_left_x: int, top_left_y: int, width: int, height: int
    ) -> MCPImage:
        """
        Captures a subrectangle of the VNC workspace and returns it as an image.

        If you would like to get a picture of the entire screen, you should use the get_whole_screen_image tool.

        The coordinates passed into this method are "relative," and use the same coordinate system as other calls.

        To get the actual "relative" workspace resolution, use get_screen_resolution.

        Getting a screenshot of a suberectangle is more performant than getting a screenshot of the entire workspace, and should be preferred where possible.
        """

        rect = Rect(top_left_x, top_left_y, width, height)
        raw_rgba_array = await vnc_client.capture(rect, relative=True)
        return await _convert_rgba_np_ndarray_to_mcpimage(raw_rgba_array)

    #     Strike key(s)
    @mcp_server.tool()
    async def strike_keys(keys: list[str]) -> str:
        """
        Strikes the keys inputted without any delay between strikes nor any modifier keys held.

        The format for keys is similar to keysymdef.py in Python.
        Alphanumeric characters (0-9a-z) are supported, although only lowercase keys may be pressed.
        To input an uppercase letter, it must either be typed with a shift modifier ot inputted using a tool
        that writes a string into the session as opposed to typing a key.

        List of example modifiers in their correct format:
            Delete
            Escape
            Super_L
            Alt_L
            Control_L
            Shift_L
            BackSpace
            space

        The "right" versions of keys are also acceptable for versions of keys that are "sided," like most modifiers.

        Keys are released in the reverse order they are input. The final key in the array will always be typed with all
        other keys pressed.
        """
        await vnc_client.press(*keys)
        return "Successfully struck " + ", ".join(keys)

    #     Write string
    @mcp_server.tool()
    async def write_string(
        string: str,
    ) -> str:
        """
        Directly writes a string into the VNC session. A textbox or similar text-accepting appliance must first
        be selected using the mouse tool(s) for a likely effect.

        Because the string is inputted directly, it may not trigger actions in softwares that expect some delay
        between keypresses. Be mindful of this when using this tool.

        However, it is likely to work in most textboxes. Because if its efficiency, it should be preferred over pressing
        keys and waiting. You may always try it first and then evaluate alternatives.
        """

        await vnc_client.write(string)
        return "Successfully typed " + string

    #     Strike key(s) with key(s) held
    @mcp_server.tool()
    async def strike_keys_with_keys_held(
        keys_to_strike: list[str],
        keys_to_hold: list[str],
    ) -> str:
        """
        Strikes the provided keys while holding the provided keys. Useful for entering keyboard shortcuts.
        The keyboard shortcut "CTRL+X" may be entered with "keys to strike" as "X," and "keys to hold" as "Control_L."

        The format for keys is similar to keysymdef.py in Python.
        Alphanumeric characters (0-9a-z) are supported, although only lowercase keys may be pressed.
        To input an uppercase letter, it must either be typed with a shift modifier ot inputted using a tool
        that writes a string into the session as opposed to typing a key.

        List of example modifiers in their correct format:
            Delete
            Escape
            Super_L
            Alt_L
            Control_L
            Shift_L
            BackSpace
            space

        The "right" versions of keys are also acceptable for versions of keys that are "sided," like most modifiers.

        Keys are released in the reverse order they are input. The final key in the array will always be typed with all
        other keys pressed.
        """

        async with vnc_client.hold_key(*keys_to_hold):
            await vnc_client.press(*keys_to_strike)

        return f"Successfully struck {', '.join(keys_to_strike)} while holding {', '.join(keys_to_hold)}"

    #     Write string with key(s) held
    @mcp_server.tool()
    async def write_string_with_keys_held(
        string_to_write: str,
        keys_to_hold: list[str],
    ) -> str:
        """
        Directly writes a string into the VNC session. A textbox or similar text-accepting appliance must first
        be selected using the mouse tool(s) for a likely effect.

        Because the string is inputted directly, it may not trigger actions in softwares that expect some delay
        between keypresses. Be mindful of this when using this tool.

        However, it is likely to work in most textboxes. Because if its efficiency, it should be preferred over pressing
        keys and waiting. You may always try it first and then evaluate alternatives.

        The format for keys is similar to keysymdef.py in Python.
        Alphanumeric characters (0-9a-z) are supported, although only lowercase keys may be pressed.
        To input an uppercase letter, it must either be typed with a shift modifier ot inputted using a tool
        that writes a string into the session as opposed to typing a key.

        List of example modifiers in their correct format:
            Delete
            Escape
            Super_L
            Alt_L
            Control_L
            Shift_L
            BackSpace
            space

        The "right" versions of keys are also acceptable for versions of keys that are "sided," like most modifiers.

        Keys are released in the reverse order they are input. The final key in the array will always be typed with all
        other keys pressed.
        """

        async with vnc_client.hold_key(*keys_to_hold):
            await vnc_client.write(string_to_write)

        return f"Successfully wrote {string_to_write} while holding {', '.join(keys_to_hold)}"

    #     Strike key(s) with mouse button held
    @mcp_server.tool()
    async def strike_keys_with_mouse_button_held(
        keys_to_strike: list[str], mouse_button_to_hold: int
    ) -> str:
        """
        Strikes a number of keys while holding a certain mouse button.

        Keys are released in the reverse order they are input. The final key in the array will always be typed with all
        other keys pressed.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4
        """

        async with vnc_client.hold_mouse(mouse_button_to_hold):
            await vnc_client.press(*keys_to_strike)

        return f"Successfully struck {', '.join(keys_to_strike)} while holding mouse button {mouse_button_to_hold}"

    #     Write string with mouse button held
    @mcp_server.tool()
    async def write_string_with_mouse_button_held(
        string_to_write: str, mouse_button_to_hold: int
    ) -> str:
        """
        Writes a string while holding a certain mouse button.

        Same rules apply as other tools that write strings.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4
        """

        async with vnc_client.hold_mouse(mouse_button_to_hold):
            await vnc_client.write(string_to_write)

        return f"Successfully wrote {string_to_write} while holding mouse button {mouse_button_to_hold}"

    #     Strike key(s) with mouse button held and key(s) held
    @mcp_server.tool()
    async def strike_keys_with_mouse_button_and_keys_held(
        keys_to_strike: list[str],
        mouse_button_to_hold: int,
        keys_to_hold: list[str],
    ) -> str:
        """
        Strikes a number of keys while holding a certain mouse button and a number of other keys.

        Keys are released in the reverse order they are input. The final key in the array will always be typed with all
        other keys pressed.

        Same rules apply to the modifier keys as the strike_keys_with_keys_held tool.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4
        """

        async with vnc_client.hold_mouse(mouse_button_to_hold):
            async with vnc_client.hold_key(*keys_to_hold):
                await vnc_client.press(*keys_to_strike)

        return f"Successfully struck {', '.join(keys_to_strike)} while holding mouse button {mouse_button_to_hold} and keys {', '.join(keys_to_hold)}"

    #     Write string with mouse button held and key(s) held
    @mcp_server.tool()
    async def write_string_with_mouse_button_and_keys_held(
        string_to_write: str,
        mouse_button_to_hold: int,
        keys_to_hold: list[str],
    ) -> str:
        """
        Writes a string while holding a certain mouse button and a number of other keys.

        Same rules apply to the modifier keys as the write_string_with_keys_held tool.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4
        """

        async with vnc_client.hold_mouse(mouse_button_to_hold):
            async with vnc_client.hold_key(*keys_to_hold):
                await vnc_client.write(string_to_write)

        return f"Successfully wrote {string_to_write} while holding mouse button {mouse_button_to_hold} and keys {', '.join(keys_to_hold)}"

    #     Move mouse from (x,y) to (w,z) with mouse button held
    @mcp_server.tool()
    async def move_mouse_with_mouse_button_held(
        start_x: int, start_y: int, end_x: int, end_y: int, mouse_button_to_hold: int
    ) -> str:
        """
        Moves the mouse from (start_x, start_y) to (end_x, end_y) while holding a certain mouse button.

        Please note that the coordinates used are the "relative" coordinates given by the VNC session.

        The workspace resolution can be obtained using the get_screen_resolution tool.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4
        """

        async with vnc_client.hold_mouse(mouse_button_to_hold):
            await vnc_client.move((start_x, start_y), relative=True)
            await vnc_client.move((end_x, end_y), relative=True)

        return f"Successfully moved mouse from ({start_x}, {start_y}) to ({end_x}, {end_y}) while holding mouse button {mouse_button_to_hold}"

    #     Move mouse from (x,y) to (w,z) with key(s) held
    @mcp_server.tool()
    async def move_mouse_with_keys_held(
        start_x: int, start_y: int, end_x: int, end_y: int, keys_to_hold: list[str]
    ) -> str:
        """
        Moves the mouse from (start_x, start_y) to (end_x, end_y) while holding a number of keys.

        Please note that the coordinates used are the "relative" coordinates given by the VNC session.

        The workspace resolution can be obtained using the get_screen_resolution tool.

        Same rules apply to the modifier keys as the strike_keys_with_keys_held tool.
        """

        async with vnc_client.hold_key(*keys_to_hold):
            await vnc_client.move((start_x, start_y), relative=True)
            await vnc_client.move((end_x, end_y), relative=True)

        return f"Successfully moved mouse from ({start_x}, {start_y}) to ({end_x}, {end_y}) while holding keys {', '.join(keys_to_hold)}"

    #     Move mouse from (x,y) to (w,z) with key(s) and mouse button held
    @mcp_server.tool()
    async def move_mouse_with_keys_and_mouse_button_held(
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        keys_to_hold: list[str],
        mouse_button_to_hold: int,
    ) -> str:
        """
        Moves the mouse from (start_x, start_y) to (end_x, end_y) while holding a number of keys and a certain mouse button.

        Please note that the coordinates used are the "relative" coordinates given by the VNC session.

        The workspace resolution can be obtained using the get_screen_resolution tool.

        Same rules apply to the modifier keys as the strike_keys_with_keys_held tool.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4
        """

        async with vnc_client.hold_mouse(mouse_button_to_hold):
            async with vnc_client.hold_key(*keys_to_hold):
                await vnc_client.move((start_x, start_y), relative=True)
                await vnc_client.move((end_x, end_y), relative=True)

        return f"Successfully moved mouse from ({start_x}, {start_y}) to ({end_x}, {end_y}) while holding keys {', '.join(keys_to_hold)} and mouse button {mouse_button_to_hold}"

    #     Move mouse to (x,y)
    @mcp_server.tool()
    async def move_mouse_to(x: int, y: int) -> str:
        """
        Moves the mouse to the coordinates (x, y) in the VNC session's workspace.

        Please note that the coordinates used are the "relative" coordinates given by the VNC session.

        The workspace resolution can be obtained using the get_screen_resolution tool.

        In order to click on a specific point on the screen, you should use this tool to move the mouse to the desired position and then use the click_at_current_position tool.
        """

        await vnc_client.move((x, y), relative=True)
        return f"Successfully moved mouse to ({x}, {y})"

    #     Click (n) times at current position
    @mcp_server.tool()
    async def click_at_current_position(mouse_button: int, n: int) -> str:
        """
        Clicks the mouse at the current position n times.

        This can be used to perform a double-click or triple-click, for example.

        This can also be used to scroll the mouse wheel by clicking the scroll buttons.
        In the case that this is used to scroll, n is the number of lines to scroll.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4

        The current position is the position of the mouse in the VNC session's workspace.
        """

        for _ in range(n):
            await vnc_client.click(mouse_button)
        return f"Successfully clicked {n} times at current position"

    #     Click (n) times at current position with key(s) held
    @mcp_server.tool()
    async def click_at_current_position_with_keys_held(
        mouse_button: int, n: int, keys_to_hold: list[str]
    ) -> str:
        """
        Clicks the mouse at the current position n times while holding a number of keys.

        Same rules apply to the modifier keys as the strike_keys_with_keys_held tool.

        This can be used to perform a double-click or triple-click, for example.

        This can also be used to scroll the mouse wheel by clicking the scroll buttons.
        In the case that this is used to scroll, n is the number of lines to scroll.

        This tool may be used for actions such as a CTRL+click, SHIFT+click, or CTRL+Scroll.

        Mouse buttons are as follows:
        MOUSE_BUTTON_LEFT = 0
        MOUSE_BUTTON_MIDDLE = 1
        MOUSE_BUTTON_RIGHT = 2
        MOUSE_BUTTON_SCROLL_UP = 3
        MOUSE_BUTTON_SCROLL_DOWN = 4

        The current position is the position of the mouse in the VNC session's workspace.
        """

        async with vnc_client.hold_key(*keys_to_hold):
            for _ in range(n):
                await vnc_client.click(mouse_button)

        return f"Successfully clicked {n} times at current position while holding keys {', '.join(keys_to_hold)}"

    return mcp_server


__all__ = ("create_mcp_server",)
