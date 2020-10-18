import argparse
import concurrent.futures
import hashlib
import os
import re
import sys
import time
import typing
import urllib
from dataclasses import dataclass
from urllib.parse import ParseResult

import requests
import logging
logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(module)s.%(funcName)s] %(message)s')
log = logging.getLogger(__name__)

FILE_WRITE_CHUNK_SIZE = 128  # chunk size in bytes for file writes


@dataclass
class DownloadResult:
    image_paths: typing.List[str]
    error_occured: bool


@dataclass
class DownloadOperationResult:
    remote_uri: str
    local_path: typing.Optional[str]
    error_occured: bool


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download all images defined by IMG HTML tags on a given page")
    parser.add_argument("url", help="website URL", type=urllib.parse.urlparse)
    parser.add_argument("--check", help="Don't save files to disk", action='store_true')
    parser.add_argument("--workers", help="How many workers to use (default: 1)", type=int, default=1)
    parser.add_argument("--verbose", help="Show more logs", action='store_true')
    args = parser.parse_args()
    return args


def get_image_uris_regex(website_text: str) -> typing.List[ParseResult]:
    """
    Extract src links from IMG tags. Given current webdesign this is pretty naive (images can also sit in CSS
    background images or be dynamically added via JS) but handling these would require considerably more effort
    so just taking care of IMG tags for now.

    :param args:
    :return:
    """
    uris: typing.List[ParseResult] = []
    # Expecting a minimum of standard conformance here - quoted URIs as src attribute value
    # This actually performs better than using find to find img offsets
    for result in re.finditer("<img.*?src=[\"'](?P<image_link>[^'\"]+)", website_text, flags=re.IGNORECASE):
        uris.append(urllib.parse.urlparse(result.group("image_link")))
    log.info("Got %d image URIs", len(uris))
    return uris


def get_image_urls_find(website_text: str) -> typing.List[ParseResult]:
    """
    Extract src links from IMG tags. Given current webdesign this is pretty naive (images can also sit in CSS
    background images or be dynamically added via JS) but handling these would require considerably more effort
    so just taking care of IMG tags for now.
    This is a proof-of-concept to determine if it's worth not using regex here.

    :param args:
    :return:
    """
    uris: typing.List[ParseResult] = []
    current_pos = 0
    img_location = website_text.find("img", current_pos)
    while img_location:
        uris.append(img_location)
        img_location = website_text.find("img", current_pos)

    log.info("Got %d image URIs", len(uris))
    return uris


def download_single_image(base_uri: str, uri: ParseResult, check=False) -> DownloadOperationResult:
    """
    Download image using the src link in the IMG tag

    :param base_uri: Base URI for site in case link is relative
    :param uri: URI as given in the IMG tag
    :param check: if True, do the request but don't save to disk
    :return: operation status and path to local file
    """
    # TODO: pass log level to thread to get logs from here too
    remote_uri = urllib.parse.urlunparse(uri)
    if not uri.scheme:
        log.debug("'%s' appears to be a relative link, prefixing it with website URL")
        remote_uri = f"{base_uri}/{remote_uri}"
    r = requests.get(remote_uri, stream=True)
    if not r.ok:
        log.error("URI %s failed to download, skipping it", remote_uri)
        return DownloadOperationResult(remote_uri=remote_uri, local_path=None, error_occured=True)
    if check:
        return DownloadOperationResult(remote_uri=remote_uri, local_path=None, error_occured=False)
    local_name = os.path.basename(uri.path)
    if not local_name or os.path.exists(local_name):
        log.debug("%s does not contain a filename or the filename already exists, using the checksum as filename")
        local_name = hashlib.md5(bytes(remote_uri)).digest().decode('utf-8')
    with open(local_name, 'wb') as fd:
        log.debug("Downloading '%s' as '%s'", remote_uri, local_name)
        for chunk in r.iter_content(chunk_size=FILE_WRITE_CHUNK_SIZE):
            fd.write(chunk)
    return DownloadOperationResult(remote_uri=remote_uri, local_path=local_name, error_occured=False)


def download_images(base_uri: str, image_links: typing.Set[ParseResult], check=False, pool_size=10) -> DownloadResult:
    """
    Download images from given list of URIs

    :param base_uri: site base URI in case image links are relative
    :param image_links: list of URIs to images extracted from IMG tags
    :param check: if True, do the request but don't save to disk
    :param pool_size: how many process workers to use
    :return: list of saved files and operation status
    """

    log.debug("Starting pool for input size %d", len(image_links))
    downloaded_files = []
    # Reference TPE usage: https://docs.python.org/3.7/library/concurrent.futures.html
    # Making this parallel as I/O is the biggest bottleneck here
    # For sample data using 10 workers resulted in a 3x speedup
    with concurrent.futures.ThreadPoolExecutor(max_workers=pool_size) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(download_single_image, base_uri, url, check): url for url in image_links}
        for future in concurrent.futures.as_completed(future_to_url):
            downloaded_files.append(future.result())
    log.debug("Pool workers completed")
    for line in downloaded_files:
        if line.error_occured:
            log.error("Failed to download %s", line.remote_uri)
        else:
            log.debug("Downloaded %s", line.remote_uri)
    return DownloadResult(image_paths=[f.local_path for f in downloaded_files],
                          error_occured=any([f.error_occured for f in downloaded_files]))


def main():
    args = get_arguments()
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    uri = urllib.parse.urlunparse(args.url)
    log.info("Downloading images from %s using %d workers", uri, args.workers)
    if args.check:
        log.info("Running in check mode, files will not be saved.")
    start_time = time.time()
    data = requests.get(uri).text
    links = get_image_uris_regex(data)
    # Deduplicate URLs to save ourselves some work
    download_result = download_images(uri, set(links), check=args.check, pool_size=args.workers)
    log.info("Downloaded %d images in %.3lf seconds", len(download_result.image_paths), time.time() - start_time)
    sys.exit(download_result.error_occured is True)


if __name__ == '__main__':
    main()
