import argparse
import hashlib
import os
import re
import sys
import typing
import urllib
from dataclasses import dataclass
from urllib.parse import ParseResult

import requests
import logging

logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(module)s.%(funcName)s] %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

FILE_WRITE_CHUNK_SIZE = 128


@dataclass
class DownloadResult:
    image_paths: str
    error_occured: bool


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to download images from", type=urllib.parse.urlparse)
    parser.add_argument("--check", help="Don't save files to disk", action='store_true')
    args = parser.parse_args()
    return args


def get_image_urls_regex(website_text: str) -> typing.List[ParseResult]:
    """
    Extract src links from IMG tags. Given current webdesign this is pretty naive (images can also sit in CSS
    background images or be dynamically added via JS) but handling these would require considerably more effort
    so just taking care of IMG tags for now.

    :param args:
    :return:
    """
    uris: typing.List[ParseResult] = []
    # Expecting a minimum of standard conformance here - quoted filenames/URIs
    for result in re.finditer("<img.*?src=[\"'](?P<image_link>[^'\"]+)", website_text):
        uris.append(urllib.parse.urlparse(result.group("image_link")))
    log.info("Got %d image URIs", len(uris))
    return uris


def download_images(base_uri: str, image_links: typing.Set[ParseResult], check=False) -> DownloadResult:
    """
    Download images from given list of URIs and return a list of local paths
    """
    downloaded_files = []
    error_occured = False
    for link in image_links:
        remote_uri = urllib.parse.urlunparse(link)
        if not link.scheme:
            log.debug("'%s' appears to be a relative link, prefixing it with website URL")
            remote_uri = f"{base_uri}/{remote_uri}"
        r = requests.get(remote_uri, stream=True)
        if not r.ok:
            log.error("URI %s failed to download, skipping it", remote_uri)
            error_occured = True
            continue
        if check:
            continue
        local_name = os.path.basename(link.path)
        if not local_name or os.path.exists(local_name):
            log.debug("%s does not contain a filename or the filename already exists, using the checksum as filename")
            local_name = hashlib.md5(bytes(remote_uri)).digest().decode('utf-8')
        with open(local_name, 'wb') as fd:
            log.debug("Downloading '%s' as '%s'", remote_uri, local_name)
            for chunk in r.iter_content(chunk_size=FILE_WRITE_CHUNK_SIZE):
                fd.write(chunk)
        return local_name

    return DownloadResult(image_paths=downloaded_files, error_occured=error_occured)


def main():
    args = get_arguments()
    uri = urllib.parse.urlunparse(args.url)
    log.info("Downloading images from %s", uri)
    data = requests.get(uri).text
    links = get_image_urls_regex(data)
    # Deduplicate URLs to save ourselves some work
    download_result = download_images(uri, set(links), check=args.check)
    log.info("Downloaded %d images", len(download_result.image_paths))
    sys.exit(download_result.error_occured is True)


if __name__ == '__main__':
    main()
