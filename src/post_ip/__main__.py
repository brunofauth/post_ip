# vim: foldmethod=marker foldlevel=0
from __future__ import annotations
# yapf: disable


from .file_paths import get_scopes_fp, get_last_ip_fp, get_oauth_token_fp, get_credentials_fp

import argparse as ap
import io
import json
import logging
import time
import typing
import re
import subprocess as sp
from collections.abc import Iterable
from contextlib import suppress

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

if typing.TYPE_CHECKING:
    from googleapiclient._apis.drive.v3 import DriveResource
    from googleapiclient._apis.drive.v3 import FileList
    from googleapiclient._apis.drive.v3 import File


RE_SCOPE = re.compile(r'^https?://www.googleapis.com/')
RE_IPV4 = re.compile(r"\.".join([r'\d{1,3}'] * 4))
RE_IPV6 = re.compile(":".join([r'[0-9a-fA-F]{0,4}'] * 8))
LOG_LEVEL = [
    logging.WARNING,
    logging.INFO,
    logging.DEBUG,
]


# get_scopes() {{{

def _parse_scopes_file() -> Iterable[str]:
    with open(get_scopes_fp()) as scopes_file:
        for line in scopes_file:
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                continue
            if (match := RE_SCOPE.match(line)) is None:
                logging.warning("%s: %s is not a valid IPv4 or IPV6", get_scopes_fp(), line)
                continue
            yield line


_scopes: list[str] | None = None
def get_scopes() -> list[str]:
    global _scopes
    if _scopes is None:
        _scopes = list(_parse_scopes_file())
    return _scopes

# }}}


def _fetch_ip_from_ipecho() -> str | None:
    _URL = "http://ipecho.net/plain"
    response = requests.get(_URL)
    response.raise_for_status()
    logging.debug("GET %s returned: %s", _URL, response.text)

    if (match := RE_IPV4.search(response.text)) is not None:
        return match.group(0)
    if (match := RE_IPV6.search(response.text)) is not None:
        return match.group(0)
    return None


def get_ip() -> str:
    while True:
        logging.debug("Fetching IP from ipecho")
        try:
            ip = _fetch_ip_from_ipecho()

        # network problem (e.g. DNS failure, refused connection, etc)
        except requests.ConnectionError as error:
            logging.exception("Could not fetch IP from ipecho. Retrying in 10 minutes...")
            time.sleep(60 * 10)
            continue

        # If the request times out before receiving a response
        except requests.Timeout as error:
            logging.exception("Could not fetch IP from ipecho. Retrying in 10 minutes...")
            time.sleep(60 * 10)
            continue

        # If an HTTP error response is returned (e.g. 404 Not Found)
        except requests.HTTPError as error:
            logging.exception("Could not fetch IP from ipecho. Retrying in 10 minutes...")
            time.sleep(60 * 10)
            continue

        if ip is None:
            logging.fatal(f"The value received from ipecho was not an IPv4 or IPv6. Exiting.")
            raise SystemExit(1)

        return ip.strip()


def authenticate(credentials_cmd: str | None = None) -> Credentials:
    creds = None
    with suppress(FileNotFoundError, OSError, ValueError):
        if get_oauth_token_fp().stat().st_mtime > get_scopes_fp().stat().st_mtime:
            creds = Credentials.from_authorized_user_file(get_oauth_token_fp(), get_scopes())
            logging.debug("Found cached authorization token. Attempting to use it.")

    if creds is not None and creds.valid:
        logging.debug("Cached authorization token is valid.")
        return creds

    if creds is not None and creds.expired and creds.refresh_token:
        logging.debug("Cached authorization token is expired. Refreshing.")
        creds.refresh(Request())
        get_oauth_token_fp().write_text(creds.to_json())
        return creds

    logging.debug("No cached authorization token found or could not refresh it. Going through authorization flow.")

    try:
        if credentials_cmd is not None:
            process = sp.run(credentials_cmd, shell=True, check=True, text=True, capture_output=True)
            flow = InstalledAppFlow.from_client_config(json.loads(process.stdout), scopes=get_scopes())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(get_credentials_fp(), get_scopes())
            except FileNotFoundError as error:
                logging.fatal("Could not find a credentials.json file. Exiting.")
                logging.info("Get a credentias file at https://console.cloud.google.com/apis/credentials")
                raise SystemExit(1)
    except json.JSONDecodeError:
        logging.fatal("The given credentials are not valid JSON. Exiting.")
        raise SystemExit(1)
    except ValueError:
        logging.fatal("The given credentials are valid JSON, but are not in the expected data layout. Exiting.")
        raise SystemExit(1)
    creds = flow.run_local_server(port=0)

    get_oauth_token_fp().write_text(creds.to_json())
    return creds


# https://stackoverflow.com/questions/67936627/how-to-escape-filenames-for-google-drive-api
def q_escaped_name_eq(value: str) -> str:
    escaped = value.replace('\\', r'\\').replace("'", r"\'")
    return f"name = '{escaped}'"


def run(service: DriveResource) -> None:
    name = "post_ip_data.txt"
    ip = get_ip()

    try:
        last_ip = get_last_ip_fp().read_text().strip()
    except FileNotFoundError:
        last_ip = None

    if last_ip is not None and ip == last_ip:
        logging.info("Fetched IP matches cache (%s).", ip)
        return
    logging.info("Fetched IP (%s) does not match cache (%s). Updating.", ip, last_ip)

    # https://developers.google.com/drive/api/reference/rest/v3/files/list
    file_list: FileList = service.files().list(
        corpora="user",
        q=q_escaped_name_eq(name),
    ).execute()
    file: File
    for file in file_list["files"]:
        service.files().delete(fileId=file["id"]).execute()
        logging.debug("Deleted remote file '%s' of id '%s'", file["name"], file["id"])

    while (page_token := file_list.get("nextPageToken", None)) is not None:
        # https://developers.google.com/drive/api/reference/rest/v3/files/list
        file_list: FileList = service.files().list(
            corpora="user",
            q=q_escaped_name_eq(name),
            pageToken=page_token,
        ).execute()
        file: File
        for file in file_list["files"]:
            service.files().delete(file["id"]).execute()
            logging.debug("Deleted remote file '%s' of id '%s'", file["name"], file["id"])

    text = io.StringIO(ip)
    uploaded_file = service.files().create(
        body={"name": name},
        media_body=MediaIoBaseUpload(fd=text, mimetype="text/plain"),
    ).execute()
    logging.debug("Updated remote file '%s' with ip '%s'", file["name"], ip)

    get_last_ip_fp().write_text(ip)
    logging.debug("Cached ip '%s' to local file '%s'", ip, get_last_ip_fp())
    last_ip = ip


def get_cli_args() -> ap.Namespace:
    parser = ap.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-c", "--credentials_command", default=None, nargs=1, metavar="CMD",
        help="Instead of looking at the habitual places, use this command to get credentials")
    return parser.parse_args()


def main() -> None:
    cli_args = get_cli_args()
    logging.basicConfig(
        level=LOG_LEVEL[min(cli_args.verbose, 2)],
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    )

    credentials = authenticate(credentials_cmd=cli_args.credentials_command)
    service = build("drive", "v3", credentials=credentials)
    while True:
        try:
            run(service=service)
        except HttpError as error:
            logging.exception("An unexpected error ocurred. Sleeping for 10 minutes.")
            time.sleep(60 * 10)
        logging.info("Sleeping for %d seconds", 60 * 60)
        time.sleep(60 * 60)


if __name__ == "__main__":
    main()
