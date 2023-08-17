import os

"""Handle a Plex.tv authorization flow to obtain an access token."""
import urllib.parse
import uuid
from datetime import datetime, timedelta

__version__ = "0.0.5"

CODES_URL = "https://plex.tv/api/v2/pins.json?strong=true"
AUTH_URL = "https://app.plex.tv/auth#!?{}"
TOKEN_URL = "https://plex.tv/api/v2/pins/{}"

import requests
import yaml
from plexapi.myplex import MyPlexAccount, PlexServer

AUTH_TOKEN_FILE = "auth_token.yml"
BASE_URL_FILE = "base_url.yml"


class NoAuthException(Exception):
    pass


class NoServerException(Exception):
    pass


def save_auth_token(username, password):
    try:
        os.remove(AUTH_TOKEN_FILE)
    except FileNotFoundError:
        pass
    account = MyPlexAccount(username, password)
    print(account.authenticationToken)
    yaml.dump(
        {"authenticationToken": account.authenticationToken}, open(AUTH_TOKEN_FILE, "w")
    )
    os.chmod(AUTH_TOKEN_FILE, 0o600)


def get_auth_token():
    if not os.path.exists(AUTH_TOKEN_FILE):
        raise NoAuthException("Auth file does not exist")
    try:
        with open(AUTH_TOKEN_FILE, "r") as f:
            auth = yaml.load(f, Loader=yaml.FullLoader)
        return auth["authenticationToken"]
    except KeyError:
        raise NoAuthException("Auth file is missing username or password")


def save_base_url(base_url):
    with open(BASE_URL_FILE, "w") as f:
        yaml.dump({"base_url": base_url}, f)
    os.chmod(BASE_URL_FILE, 0o600)


def get_base_url():
    if not os.path.exists(BASE_URL_FILE):
        raise NoServerException("Server file does not exist")
    try:
        with open(BASE_URL_FILE, "r") as f:
            server = yaml.load(f, Loader=yaml.FullLoader)
        return server["base_url"]
    except KeyError:
        raise NoServerException("Server file is missing server")


def get_account():
    auth_token = get_auth_token()
    return MyPlexAccount(token=auth_token)


def get_client():
    base_url = get_base_url()
    auth_token = get_auth_token()
    session = requests.Session()
    session.verify = False
    plex = PlexServer(
        base_url,
        auth_token,
        session,
    )
    return plex
