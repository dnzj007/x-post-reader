import unittest

from x_post_reader.reader import extract_post_text_from_html, extract_published_at, normalize_status_url


OEMBED_HTML = """
<blockquote class="twitter-tweet">
  <p lang="zh" dir="ltr">
    OKX Onchain OS 延续 OKX DEX 的强大基建，帮用户自动找到最优价格！🫡
    <a href="https://t.co/SrQAd4XWHO">https://t.co/SrQAd4XWHO</a>
  </p>
  &mdash; OKX Wallet 中文 (@OKXWallet_CN)
  <a href="https://twitter.com/OKXWallet_CN/status/2031361379438075907?ref_src=twsrc%5Etfw">March 10, 2026</a>
</blockquote>
"""


class ReaderTests(unittest.TestCase):
    def test_normalize_status_url_accepts_x(self) -> None:
        self.assertEqual(
            normalize_status_url("https://x.com/OKXWallet_CN/status/2031361379438075907"),
            "https://twitter.com/OKXWallet_CN/status/2031361379438075907",
        )

    def test_extract_post_text_preserves_tco(self) -> None:
        self.assertEqual(
            extract_post_text_from_html(OEMBED_HTML),
            "OKX Onchain OS 延续 OKX DEX 的强大基建，帮用户自动找到最优价格！🫡 https://t.co/SrQAd4XWHO",
        )

    def test_extract_published_at(self) -> None:
        self.assertEqual(extract_published_at(OEMBED_HTML), "March 10, 2026")


if __name__ == "__main__":
    unittest.main()
