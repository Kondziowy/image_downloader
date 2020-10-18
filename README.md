# image_downloader
Script to download all images defined by IMG HTML tags on a website. They will be saved to current workdir.
Tool will not recursively follow links.

    usage: image_downloader.py [-h] [--check] [--workers WORKERS] [--verbose] url

    Download all images defined by IMG HTML tags on a given page

    positional arguments:
      url                website URL

    optional arguments:
      -h, --help         show this help message and exit
      --check            Don't save files to disk
      --workers WORKERS  How many workers to use
      --verbose          Show more logs


Example:

    image_downloader.py --workers 1 --check http://wp.pl
    [2020-10-19 01:29:30,604][INFO][image_downloader.main] Downloading images from http://wp.pl using 1 workers
    [2020-10-19 01:29:30,604][INFO][image_downloader.main] Running in check mode, files will not be saved.
    [2020-10-19 01:29:30,863][INFO][image_downloader.get_image_uris_regex] Got 44 image URIs
    [2020-10-19 01:29:32,267][INFO][image_downloader.main] Downloaded 39 images in 1.664 seconds
