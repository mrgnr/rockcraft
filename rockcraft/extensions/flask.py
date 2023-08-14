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

"""An experimental extension for the Flask framework."""

import copy
import os
from typing import Any, Dict, Optional, Tuple

from overrides import override

from ._utils import apply_extension_property
from .extension import Extension


class Flask(Extension):
    """An extension for constructing Python applications based on the Flask framework."""

    @staticmethod
    @override
    def get_supported_bases() -> Tuple[str, ...]:
        """Return supported bases."""
        return "bare", "ubuntu:20.04", "ubuntu:22.04"

    @staticmethod
    @override
    def is_experimental(base: Optional[str]) -> bool:
        """Check if the extension is in an experimental state."""
        return True

    @override
    def get_root_snippet(self) -> Dict[str, Any]:
        """Fill in some default root components for Flask.

        Default values:
          - run_user: _daemon_
          - build-base: ubuntu:22.04 (only if user specify bare without a build-base)
          - platform: amd64
        """
        snippet: Dict[str, Any] = {}
        if "run_user" not in self.yaml_data:
            snippet["run_user"] = "_daemon_"
        if (
            "build-base" not in self.yaml_data
            and self.yaml_data.get("base", "bare") == "bare"
        ):
            snippet["build-base"] = "ubuntu:22.04"
        if "platforms" not in self.yaml_data:
            snippet["platforms"] = {"amd64": {}}
        current_parts = copy.deepcopy(self.yaml_data.get("parts", {}))
        current_parts.update(self._gen_new_parts())
        snippet["parts"] = current_parts
        return snippet

    @override
    def get_part_snippet(self) -> Dict[str, Any]:
        """Return the part snippet to apply to existing parts."""
        return {}

    def _merge_part(self, base_part: dict, new_part: dict) -> dict:
        """Merge two part definitions by the extension part merging rule."""
        result = {}
        properties = set(base_part.keys()).union(set(new_part.keys()))
        for property_name in properties:
            if property_name in base_part and property_name not in new_part:
                result[property_name] = base_part[property_name]
            elif property_name not in base_part and property_name in new_part:
                result[property_name] = new_part[property_name]
            else:
                result[property_name] = apply_extension_property(
                    base_part[property_name], new_part[property_name]
                )
        return result

    def _merge_existing_part(self, part_name: str, part_def: dict) -> dict:
        """Merge the new part with the existing part in the current rockcraft.yaml."""
        existing_part = self.yaml_data.get("parts", {}).get(part_name, {})
        return self._merge_part(existing_part, part_def)

    def _gen_new_parts(self) -> Dict[str, Any]:
        """Generate new parts for the flask extension.

        Parts added:
            - flask/dependencies: install Python dependencies
            - flask/install-app: copy the flask project into the OCI image
        """
        if not (self.project_root / "requirements.txt").exists():
            raise ValueError(
                "missing requirements.txt file, "
                "flask extension requires this file with flask specified as a dependency"
            )
        ignores = [".git", "node_modules", ".yarn"]
        source_files = [
            f
            for f in os.listdir(self.project_root)
            if f not in ignores and not f.endswith(".rock")
        ]
        renaming_map = {f: os.path.join("srv/flask/app", f) for f in source_files}
        install_app_part_name = "flask/install-app"
        dependencies_part_name = "flask/dependencies"
        # Users are required to compile any static assets prior to executing the
        # rockcraft pack command, so assets can be included in the final OCI image.
        install_app_part = {
            "plugin": "dump",
            "source": ".",
            "organize": renaming_map,
            "stage": list(renaming_map.values()),
        }
        dependencies_part = {
            "plugin": "python",
            "stage-packages": ["python3-venv"],
            "source": ".",
            "python-packages": ["gunicorn"],
            "python-requirements": ["requirements.txt"],
        }
        snippet = {
            dependencies_part_name: self._merge_existing_part(
                dependencies_part_name, dependencies_part
            ),
            install_app_part_name: self._merge_existing_part(
                install_app_part_name, install_app_part
            ),
        }
        return snippet

    @override
    def get_parts_snippet(self) -> Dict[str, Any]:
        """Create necessary parts to facilitate the flask application."""
        return {}
