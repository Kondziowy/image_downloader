# image_downloader
Script to download all images defined by IMG HTML tags on a website. They will be saved to current workdir.
Tool will not recursively follow links.

    usage: image_downloader.py [-h] [--check] [--workers WORKERS] url

    positional arguments:
      url                website URL

    optional arguments:
      -h, --help         show this help message and exit
      --check            Don't save files to disk
      --workers WORKERS  How many workers to use

Example:
    image_downloader.py --workers 10 http://wp.pl