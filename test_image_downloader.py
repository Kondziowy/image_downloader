import os
import timeit
import unittest
import urllib
from statistics import mean
import logging

import image_downloader

NUM_SAMPLES = 100


class TestImageDownloader(unittest.TestCase):
    def test_get_image_urls_regex__simple_html__return_single_link(self):
        with open(os.path.join("data", "test_simple.html")) as f:
            data = f.read()
        self.assertEqual([urllib.parse.urlparse("cat.png")], image_downloader.get_image_uris_regex(data))

    def test_get_image_urls_regex__complex_html__multiple_links(self):
        with open(os.path.join("data", "wppl-rendered.html"), "rb") as f:
            data = f.read().decode('utf-8')
        self.assertEqual(21, len(image_downloader.get_image_uris_regex(data)))

    def test_get_image_urls_regex__complex_html__regex_performance(self):
        # Supress logging to make tests more meaningful
        logging.getLogger("image_downloader").setLevel(logging.ERROR)
        with open(os.path.join("data", "wppl-rendered.html"), "rb") as f:
            data = f.read().decode('utf-8')
        time = mean(timeit.repeat(lambda: image_downloader.get_image_uris_regex(data), number=NUM_SAMPLES))
        print("Regex parsing took %.3lf seconds" % time)

    def test_get_image_urls_regex__complex_html__find_performance(self):
        # Supress logging to make tests more meaningful
        logging.getLogger("image_downloader").setLevel(logging.ERROR)
        with open(os.path.join("data", "wppl-rendered.html"), "rb") as f:
            data = f.read().decode('utf-8')
        time = mean(timeit.repeat(lambda: image_downloader.get_image_uris_regex(data), number=NUM_SAMPLES))
        print("Find parsing took %.3lf seconds" % time)


if __name__ == '__main__':
    unittest.main()
