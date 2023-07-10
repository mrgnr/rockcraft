# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Extension processor and related utilities."""

from ._utils import apply_extensions
from .registry import get_extension_class, get_extension_names, register, unregister

__all__ = [
    "get_extension_class",
    "get_extension_names",
    "apply_extensions",
    "register",
    "unregister",
]

from .flask import Flask as _Flask

register("flask", _Flask)
