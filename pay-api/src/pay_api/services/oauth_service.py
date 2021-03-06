# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Service to invoke Rest services."""
import json

import requests
from flask import current_app
from requests.adapters import HTTPAdapter  # pylint:disable=ungrouped-imports
# pylint:disable=ungrouped-imports
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import ConnectTimeout, HTTPError
from urllib3.util.retry import Retry

from pay_api.exceptions import ServiceUnavailableException
from pay_api.utils.enums import AuthHeaderType, ContentType


RETRY_ADAPTER = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[404]))


class OAuthService:
    """Service to invoke Rest services which uses OAuth 2.0 implementation."""

    @staticmethod
    def post(endpoint, token, auth_header_type: AuthHeaderType, content_type: ContentType, data):
        """POST service."""
        current_app.logger.debug('<post')

        headers = {
            'Authorization': auth_header_type.value.format(token),
            'Content-Type': content_type.value
        }
        if content_type == ContentType.JSON:
            data = json.dumps(data)

        current_app.logger.debug('Endpoint : {}'.format(endpoint))
        current_app.logger.debug('headers : {}'.format(headers))
        current_app.logger.debug('data : {}'.format(data))
        response = None
        try:
            response = requests.post(endpoint, data=data, headers=headers,
                                     timeout=current_app.config.get('CONNECT_TIMEOUT'))
            response.raise_for_status()
        except (ReqConnectionError, ConnectTimeout) as exc:
            current_app.logger.error('---Error on POST---')
            current_app.logger.error(exc)
            raise ServiceUnavailableException(exc)
        except HTTPError as exc:
            current_app.logger.error(
                'HTTPError on POST with status code {}'.format(response.status_code if response else ''))
            if response and response.status_code >= 500:
                raise ServiceUnavailableException(exc)
            raise exc
        finally:
            current_app.logger.debug(response.headers)
            current_app.logger.info('response : {}'.format(response.text if response else ''))

        current_app.logger.debug('>post')
        return response

    @staticmethod
    def get(endpoint, token, auth_header_type: AuthHeaderType, content_type: ContentType,
            retry_on_failure: bool = False):
        """GET service."""
        current_app.logger.debug('<GET')

        headers = {
            'Authorization': auth_header_type.value.format(token),
            'Content-Type': content_type.value
        }

        current_app.logger.debug('Endpoint : {}'.format(endpoint))
        current_app.logger.debug('headers : {}'.format(headers))
        session = requests.Session()
        if retry_on_failure:
            session.mount(endpoint, RETRY_ADAPTER)
        response = None
        try:
            response = session.get(endpoint, headers=headers, timeout=current_app.config.get('CONNECT_TIMEOUT'))
            response.raise_for_status()
        except (ReqConnectionError, ConnectTimeout) as exc:
            current_app.logger.error('---Error on POST---')
            current_app.logger.error(exc)
            raise ServiceUnavailableException(exc)
        except HTTPError as exc:
            current_app.logger.error(
                'HTTPError on POST with status code {}'.format(response.status_code if response else ''))
            if response and response.status_code >= 500:
                raise ServiceUnavailableException(exc)
            raise exc

        current_app.logger.info('response : {}'.format(response.text if response else ''))
        current_app.logger.debug('>GET')
        return response
