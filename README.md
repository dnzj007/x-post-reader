# x-post-reader

Read public X/Twitter post text through the official `publish.twitter.com/oembed` API.

This project is useful when:

- Tavily finds a raw X post URL
- Direct page fetch is blocked or noisy
- `r.jina.ai` does not work for a normal `status` URL

## What it does

- Normalizes `x.com` and `twitter.com` status URLs
- Calls the public oEmbed endpoint
- Extracts the readable post text from the returned blockquote HTML
- Optionally expands `t.co` short links
- Prints clean JSON

## Install

```bash
python3 -m pip install .
```

Or run it directly from the repo:

```bash
python3 -m x_post_reader https://x.com/OKXWallet_CN/status/2031361379438075907 --expand-links
```

## Example output

```json
{
  "author_name": "OKX Wallet 中文",
  "author_url": "https://twitter.com/OKXWallet_CN",
  "canonical_url": "https://twitter.com/OKXWallet_CN/status/2031361379438075907",
  "post_text": "OKX Onchain OS 延续 OKX DEX 的强大基建，帮用户自动找到最优价格！🫡 https://t.co/SrQAd4XWHO",
  "published_at": "March 10, 2026",
  "expanded_links": [
    {
      "short_url": "https://t.co/SrQAd4XWHO",
      "final_url": "https://x.com/Reboottttttt/status/2031219746008608781"
    }
  ]
}
```

## Limitations

- This targets public `status` URLs.
- X `article` pages are not covered yet.
- If X disables oEmbed for a post, the reader will fail cleanly with an error.
