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
"""All of the configuration for the service is captured here. All items are loaded, or have Constants defined here that are loaded into the Flask configuration. All modules and lookups get their configuration from the Flask config, rather than reading environment variables directly or by accessing this configuration directly.
"""

import os
import sys
import json

from dotenv import find_dotenv, load_dotenv

# this will load all the envars from a .env file located in the project root (api)
load_dotenv(find_dotenv())

CONFIGURATION = {
    'development': 'config.DevConfig',
    'testing': 'config.TestConfig',
    'production': 'config.ProdConfig',
    'default': 'config.ProdConfig',
}


def get_named_config(config_name: str = 'production'):
    """Return the configuration object based on the name

    :raise: KeyError: if an unknown configuration is requested
    """
    if config_name in ['production', 'staging', 'default']:
        config = ProdConfig()
    elif config_name == 'testing':
        config = TestConfig()
    elif config_name == 'development':
        config = DevConfig()
    else:
        raise KeyError(f"Unknown configuration '{config_name}'")
    return config


class _Config(object):  # pylint: disable=too-few-public-methods
    """Base class configuration that should set reasonable defaults for all the other configurations. """

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = 'a secret'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ALEMBIC_INI = 'migrations/alembic.ini'

    # POSTGRESQL
    DB_USER = os.getenv('DATABASE_USERNAME', '')
    DB_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
    DB_NAME = os.getenv('DATABASE_NAME', '')
    DB_HOST = os.getenv('DATABASE_HOST', '')
    DB_PORT = os.getenv('DATABASE_PORT', '5432')
    SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
        user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=int(DB_PORT), name=DB_NAME
    )
    SQLALCHEMY_ECHO = True

    # JWT_OIDC Settings
    JWT_OIDC_WELL_KNOWN_CONFIG = os.getenv('JWT_OIDC_WELL_KNOWN_CONFIG')
    JWT_OIDC_ALGORITHMS = os.getenv('JWT_OIDC_ALGORITHMS')
    JWT_OIDC_JWKS_URI = os.getenv('JWT_OIDC_JWKS_URI')
    JWT_OIDC_ISSUER = os.getenv('JWT_OIDC_ISSUER')
    JWT_OIDC_AUDIENCE = os.getenv('JWT_OIDC_AUDIENCE')
    JWT_OIDC_CLIENT_SECRET = os.getenv('JWT_OIDC_CLIENT_SECRET')
    JWT_OIDC_CACHING_ENABLED = os.getenv('JWT_OIDC_CACHING_ENABLED')
    try:
        JWT_OIDC_JWKS_CACHE_TIMEOUT = int(os.getenv('JWT_OIDC_JWKS_CACHE_TIMEOUT'))
    except:
        JWT_OIDC_JWKS_CACHE_TIMEOUT = 300

    # PAYBC API Settings
    PAYBC_BASE_URL = os.getenv('PAYBC_BASE_URL')
    PAYBC_CLIENT_ID = os.getenv('PAYBC_CLIENT_ID')
    PAYBC_CLIENT_SECRET = os.getenv('PAYBC_CLIENT_SECRET')
    PAYBC_PORTAL_URL = os.getenv('PAYBC_PORTAL_URL')
    AUTH_WEB_PAY_TRANSACTION_URL = os.getenv('AUTH_WEB_PAY_TRANSACTION_URL')
    PAYBC_MEMO_LINE_NAME = os.getenv('PAYBC_MEMO_LINE_NAME')
    CONNECT_TIMEOUT = int(os.getenv('PAYBC_CONNECT_TIMEOUT', 10))
    GENERATE_RANDOM_INVOICE_NUMBER = os.getenv('PAYBC_GENERATE_RANDOM_INVOICE_NUMBER', 'False')

    # BCOL
    BCOL_VERIFY_USER_WSDL_URL = os.getenv('BCOL_VERIFY_USER_WSDL_URL')
    BCOL_QUERY_PROFILE_WSDL_URL = os.getenv('BCOL_QUERY_PROFILE_WSDL_URL')
    BCOL_LDAP_SERVER = os.getenv('BCOL_LDAP_SERVER')
    BCOL_LDAP_USER_DN_PATTERN = os.getenv('BCOL_LDAP_USER_DN_PATTERN')
    BCOL_DEBIT_ACCOUNT_VERSION = os.getenv('BCOL_DEBIT_ACCOUNT_VERSION')
    BCOL_LINK_CODE = os.getenv('BCOL_LINK_CODE')

    # REPORT API Settings
    REPORT_API_BASE_URL = os.getenv('REPORT_API_BASE_URL')

    # NATS Config
    NATS_SERVERS = os.getenv('NATS_SERVERS', 'nats://127.0.0.1:4222').split(',')
    NATS_CLIENT_NAME = os.getenv('NATS_CLIENT_NAME', 'entity.filing.worker')
    NATS_CLUSTER_ID = os.getenv('NATS_CLUSTER_ID', 'test-cluster')
    NATS_SUBJECT = os.getenv('NATS_SUBJECT', 'entity.filings')
    NATS_QUEUE = os.getenv('NATS_QUEUE', 'filing-worker')
    # SERVICE Status Settings
    SERVICE_SCHEDULE = os.getenv('SERVICE_SCHEDULE')

    # Auth API Endpoint
    AUTH_API_ENDPOINT = os.getenv('AUTH_API_ENDPOINT')

    # Sentry Config
    SENTRY_DSN = os.getenv('SENTRY_DSN', None)

    TESTING = False
    DEBUG = True


class DevConfig(_Config):  # pylint: disable=too-few-public-methods
    TESTING = False
    DEBUG = True


class TestConfig(_Config):  # pylint: disable=too-few-public-methods
    """In support of testing only used by the py.test suite."""

    DEBUG = True
    TESTING = True
    # POSTGRESQL
    DB_USER = os.getenv('DATABASE_TEST_USERNAME', '')
    DB_PASSWORD = os.getenv('DATABASE_TEST_PASSWORD', '')
    DB_NAME = os.getenv('DATABASE_TEST_NAME', '')
    DB_HOST = os.getenv('DATABASE_TEST_HOST', '')
    DB_PORT = os.getenv('DATABASE_TEST_PORT', '5432')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_TEST_URL',
        'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
            user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=int(DB_PORT), name=DB_NAME
        ),
    )

    JWT_OIDC_TEST_MODE = True
    JWT_OIDC_TEST_AUDIENCE = os.getenv('JWT_OIDC_AUDIENCE')
    JWT_OIDC_TEST_CLIENT_SECRET = os.getenv('JWT_OIDC_CLIENT_SECRET')
    JWT_OIDC_TEST_ISSUER = os.getenv('JWT_OIDC_ISSUER')
    JWT_OIDC_TEST_KEYS = {
        'keys': [
            {
                'kid': 'sbc-auth-cron-job',
                'kty': 'RSA',
                'alg': 'RS256',
                'use': 'sig',
                'n': 'AN-fWcpCyE5KPzHDjigLaSUVZI0uYrcGcc40InVtl-rQRDmAh-C2W8H4_Hxhr5VLc6crsJ2LiJTV_E72S03pzpOOaaYV6-TzAjCou2GYJIXev7f6Hh512PuG5wyxda_TlBSsI-gvphRTPsKCnPutrbiukCYrnPuWxX5_cES9eStR',
                'e': 'AQAB',
            }
        ]
    }

    JWT_OIDC_TEST_PRIVATE_KEY_JWKS = {
        'keys': [
            {
                'kid': 'sbc-auth-cron-job',
                'kty': 'RSA',
                'alg': 'RS256',
                'use': 'sig',
                'n': 'AN-fWcpCyE5KPzHDjigLaSUVZI0uYrcGcc40InVtl-rQRDmAh-C2W8H4_Hxhr5VLc6crsJ2LiJTV_E72S03pzpOOaaYV6-TzAjCou2GYJIXev7f6Hh512PuG5wyxda_TlBSsI-gvphRTPsKCnPutrbiukCYrnPuWxX5_cES9eStR',
                'e': 'AQAB',
                'd': 'C0G3QGI6OQ6tvbCNYGCqq043YI_8MiBl7C5dqbGZmx1ewdJBhMNJPStuckhskURaDwk4-8VBW9SlvcfSJJrnZhgFMjOYSSsBtPGBIMIdM5eSKbenCCjO8Tg0BUh_xa3CHST1W4RQ5rFXadZ9AeNtaGcWj2acmXNO3DVETXAX3x0',
                'p': 'APXcusFMQNHjh6KVD_hOUIw87lvK13WkDEeeuqAydai9Ig9JKEAAfV94W6Aftka7tGgE7ulg1vo3eJoLWJ1zvKM',
                'q': 'AOjX3OnPJnk0ZFUQBwhduCweRi37I6DAdLTnhDvcPTrrNWuKPg9uGwHjzFCJgKd8KBaDQ0X1rZTZLTqi3peT43s',
                'dp': 'AN9kBoA5o6_Rl9zeqdsIdWFmv4DB5lEqlEnC7HlAP-3oo3jWFO9KQqArQL1V8w2D4aCd0uJULiC9pCP7aTHvBhc',
                'dq': 'ANtbSY6njfpPploQsF9sU26U0s7MsuLljM1E8uml8bVJE1mNsiu9MgpUvg39jEu9BtM2tDD7Y51AAIEmIQex1nM',
                'qi': 'XLE5O360x-MhsdFXx8Vwz4304-MJg-oGSJXCK_ZWYOB_FGXFRTfebxCsSYi0YwJo-oNu96bvZCuMplzRI1liZw',
            }
        ]
    }

    JWT_OIDC_TEST_PRIVATE_KEY_PEM = """
    -----BEGIN RSA PRIVATE KEY-----
    MIICXQIBAAKBgQDfn1nKQshOSj8xw44oC2klFWSNLmK3BnHONCJ1bZfq0EQ5gIfg
    tlvB+Px8Ya+VS3OnK7Cdi4iU1fxO9ktN6c6TjmmmFevk8wIwqLthmCSF3r+3+h4e
    ddj7hucMsXWv05QUrCPoL6YUUz7Cgpz7ra24rpAmK5z7lsV+f3BEvXkrUQIDAQAB
    AoGAC0G3QGI6OQ6tvbCNYGCqq043YI/8MiBl7C5dqbGZmx1ewdJBhMNJPStuckhs
    kURaDwk4+8VBW9SlvcfSJJrnZhgFMjOYSSsBtPGBIMIdM5eSKbenCCjO8Tg0BUh/
    xa3CHST1W4RQ5rFXadZ9AeNtaGcWj2acmXNO3DVETXAX3x0CQQD13LrBTEDR44ei
    lQ/4TlCMPO5bytd1pAxHnrqgMnWovSIPSShAAH1feFugH7ZGu7RoBO7pYNb6N3ia
    C1idc7yjAkEA6Nfc6c8meTRkVRAHCF24LB5GLfsjoMB0tOeEO9w9Ous1a4o+D24b
    AePMUImAp3woFoNDRfWtlNktOqLel5PjewJBAN9kBoA5o6/Rl9zeqdsIdWFmv4DB
    5lEqlEnC7HlAP+3oo3jWFO9KQqArQL1V8w2D4aCd0uJULiC9pCP7aTHvBhcCQQDb
    W0mOp436T6ZaELBfbFNulNLOzLLi5YzNRPLppfG1SRNZjbIrvTIKVL4N/YxLvQbT
    NrQw+2OdQACBJiEHsdZzAkBcsTk7frTH4yGx0VfHxXDPjfTj4wmD6gZIlcIr9lZg
    4H8UZcVFN95vEKxJiLRjAmj6g273pu9kK4ymXNEjWWJn
    -----END RSA PRIVATE KEY-----"""

    PAYBC_BASE_URL = 'https://mock-lear-tools.pathfinder.gov.bc.ca/rest/PayBC+API+Reference/1.0.0'
    PAYBC_CLIENT_ID = 'TEST'
    PAYBC_CLIENT_SECRET = 'TEST'
    PAYBC_PORTAL_URL = ''
    SERVER_NAME = 'auth-web.dev.com'

    schedule_json = [
        {
            "service_name": "PAYBC",
            "schedules": [
                {"up": "30 6 * * 1-2", "down": "19 10 * * 1-2"},
                {"up": "30 6 * * 3", "down": "30 10 * * 3"},
                {"up": "30 14 * * 4"},
                {"down": "30 9 * * 5"},
                {"up": "30 6 * * 7", "down": "30 21 * * 7"},
            ],
        },
        {
            "service_name": "BCOL",
            "schedules": [
                {"up": "30 06 * * 1-3", "down": "30 22 * * 1-3"},
                {"up": "30 06 * * 6-7", "down": "30 20 * * 6-7"},
            ],
        },
    ]

    REPORT_API_BASE_URL = "https://mock-lear-tools.pathfinder.gov.bc.ca/rest/PayBC+API+Reference/1.0.0/cfs/parties/"

    SERVICE_SCHEDULE = json.dumps(schedule_json)

    AUTH_API_ENDPOINT = "https://mock-lear-tools.pathfinder.gov.bc.ca/rest/Auth+API/1.0.0/"


class ProdConfig(_Config):  # pylint: disable=too-few-public-methods
    """Production environment configuration."""

    SECRET_KEY = os.getenv('SECRET_KEY', None)

    if not SECRET_KEY:
        SECRET_KEY = os.urandom(24)
        print('WARNING: SECRET_KEY being set as a one-shot', file=sys.stderr)

    TESTING = False
    DEBUG = False
