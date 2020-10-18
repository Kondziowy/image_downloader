import os
import unittest
import urllib

import image_downloader


class TestImageDownloader(unittest.TestCase):
    def test_get_image_urls_regex__simple_html__return_single_link(self):
        with open(os.path.join("data", "test_simple.html")) as f:
            data = f.read()
        self.assertEqual([urllib.parse.urlparse("cat.png")], image_downloader.get_image_urls_regex(data))

    def test_get_image_urls_regex__complex_html__multiple_links(self):
        with open(os.path.join("data", "wppl-rendered.html"), "rb") as f:
            data = f.read().decode('utf-8')
        self.assertEqual(21, len(image_downloader.get_image_urls_regex(data)))


if __name__ == '__main__':
    unittest.main()
