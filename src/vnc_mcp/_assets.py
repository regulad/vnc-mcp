"""vnc-mcp

Copyright (C) 2025  Parker Wahle

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: E501, B950, D415

from __future__ import annotations

from importlib.resources import files


# The root of the package. This may not be a path if the package is installed, so just access the Traversable.
PACKAGE = files(__package__)
# If you use all of your files in a folder like `assets` or `resources` (recommended), use the following line.
RESOURCES = PACKAGE / "resources"

__all__ = ("RESOURCES",)
