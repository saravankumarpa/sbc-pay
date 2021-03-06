# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Super class to handle all operations related to base schema."""

from marshmallow import post_dump

from .db import ma


class BaseSchema(ma.ModelSchema):
    """Base Schema."""

    @post_dump(pass_many=True)
    def _remove_empty(self, data, many):  # pylint: disable=no-self-use
        """Remove all empty values from the dumped dict."""
        if not many:
            return {
                key: value for key, value in data.items()
                if value
            }
        for item in data:
            for key in list(item):
                if not item[key]:
                    item.pop(key)
        return data
