"""
Run this script ONCE to populate front_image_url and side_image_url.

It does not download or re-host images. It only stores image URLs from each paddle's
official/retailer page so your Streamlit app can display them.

Usage:
    python scrape_paddle_images.py

Input:
    paddles_balanced_90_image_ready.csv

Output:
    paddles_balanced_90_scraped_images.csv

Then rename the output file to paddles_balanced_90_image_ready.csv or update
CSV_FILENAME in app.py.
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


INPUT_CSV = "paddles_balanced_90_image_ready.csv"
OUTPUT_CSV = "paddles_balanced_90_scraped_images.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def clean_url(url):
    if not url:
        return ""

    url = str(url).strip()

    if url.startswith("//"):
        return "https:" + url

    return url


def is_image_url(url):
    if not url:
        return False

    lower = url.lower()
    image_keywords = [".jpg", ".jpeg", ".png", ".webp", "cdn/shop", "images", "media"]

    return any(keyword in lower for keyword in image_keywords)


def normalize_image_url(url, page_url):
    url = clean_url(url)
    if not url:
        return ""

    url = urljoin(page_url, url)

    # Remove tiny Shopify size variants when possible.
    url = re.sub(r"_(\d+)x(?=\.)", "", url)

    return url


def add_candidate(candidates, url, page_url, reason):
    url = normalize_image_url(url, page_url)

    if not is_image_url(url):
        return

    if url not in [candidate["url"] for candidate in candidates]:
        candidates.append({"url": url, "reason": reason})


def extract_images_from_json_ld(soup, page_url):
    candidates = []

    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        text = script.string or script.get_text(strip=True)

        if not text:
            continue

        try:
            data = json.loads(text)
        except Exception:
            continue

        items = data if isinstance(data, list) else [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            image_value = item.get("image")

            if isinstance(image_value, str):
                add_candidate(candidates, image_value, page_url, "json_ld_image")

            elif isinstance(image_value, list):
                for image_url in image_value:
                    if isinstance(image_url, str):
                        add_candidate(candidates, image_url, page_url, "json_ld_image_list")

    return candidates


def extract_images_from_meta(soup, page_url):
    candidates = []

    selectors = [
        ("property", "og:image"),
        ("property", "og:image:secure_url"),
        ("name", "twitter:image"),
        ("name", "twitter:image:src"),
    ]

    for attr_name, attr_value in selectors:
        tag = soup.find("meta", attrs={attr_name: attr_value})

        if tag and tag.get("content"):
            add_candidate(candidates, tag["content"], page_url, attr_value)

    return candidates


def extract_images_from_img_tags(soup, page_url, paddle_name):
    candidates = []
    name_tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", paddle_name) if len(token) >= 3]

    for img in soup.find_all("img"):
        possible_urls = []

        for attr in ["src", "data-src", "data-original", "data-image"]:
            if img.get(attr):
                possible_urls.append(img.get(attr))

        srcset = img.get("srcset") or img.get("data-srcset")
        if srcset:
            # Usually the last srcset item is largest.
            parts = [part.strip().split(" ")[0] for part in srcset.split(",") if part.strip()]
            possible_urls.extend(parts[-2:])

        alt_text = (img.get("alt") or "").lower()
        combined_text = alt_text + " " + " ".join(possible_urls).lower()

        score = 0
        for token in name_tokens:
            if token in combined_text:
                score += 1

        # Keep likely product images and Shopify CDN images.
        if score > 0 or "cdn/shop" in combined_text or "product" in combined_text:
            for url in possible_urls:
                add_candidate(candidates, url, page_url, f"img_tag_score_{score}")

    return candidates


def score_image_candidate(candidate):
    url = candidate["url"].lower()
    reason = candidate["reason"].lower()

    score = 0

    if "json_ld" in reason:
        score += 20

    if "og:image" in reason or "twitter:image" in reason:
        score += 15

    if "cdn/shop" in url:
        score += 10

    if "product" in url:
        score += 5

    if any(bad in url for bad in ["logo", "icon", "avatar", "sprite"]):
        score -= 50

    if any(side in url for side in ["side", "profile", "edge", "thickness", "detail", "angle"]):
        score += 5

    return score


def choose_front_and_side(candidates):
    if not candidates:
        return "", ""

    candidates = sorted(candidates, key=score_image_candidate, reverse=True)

    front = candidates[0]["url"]
    side = ""

    side_keywords = ["side", "profile", "edge", "thickness", "detail", "angle"]

    for candidate in candidates[1:]:
        url_lower = candidate["url"].lower()

        if candidate["url"] == front:
            continue

        if any(keyword in url_lower for keyword in side_keywords):
            side = candidate["url"]
            break

    if not side:
        for candidate in candidates[1:]:
            if candidate["url"] != front:
                side = candidate["url"]
                break

    return front, side


def scrape_product_images(page_url, paddle_name):
    if not isinstance(page_url, str) or not page_url.startswith("http"):
        return "", ""

    try:
        response = requests.get(page_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except Exception as error:
        print(f"FAILED: {paddle_name} -> {error}")
        return "", ""

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    candidates.extend(extract_images_from_json_ld(soup, page_url))
    candidates.extend(extract_images_from_meta(soup, page_url))
    candidates.extend(extract_images_from_img_tags(soup, page_url, paddle_name))

    return choose_front_and_side(candidates)


def main():
    input_path = Path(INPUT_CSV)

    if not input_path.exists():
        raise FileNotFoundError(f"Could not find {INPUT_CSV}")

    df = pd.read_csv(input_path)

    for column in ["front_image_url", "side_image_url", "image_credit_url"]:
        if column not in df.columns:
            df[column] = ""

    for index, row in df.iterrows():
        name = row["name"]
        buy_url = str(row.get("buy_url", "")).strip()

        # Skip generic search pages because they usually do not contain exact product images.
        if "/search" in buy_url or "google.com" in buy_url:
            print(f"SKIP SEARCH PAGE: {name}")
            continue

        print(f"Scraping {index + 1}/{len(df)}: {name}")

        front_url, side_url = scrape_product_images(buy_url, name)

        if front_url:
            df.at[index, "front_image_url"] = front_url

        if side_url:
            df.at[index, "side_image_url"] = side_url

        if front_url or side_url:
            df.at[index, "image_credit_url"] = buy_url

        time.sleep(1)

    df.to_csv(OUTPUT_CSV, index=False)
    print()
    print(f"Done. Wrote {OUTPUT_CSV}")
    print(f"Rows with front images: {(df['front_image_url'].fillna('') != '').sum()}")
    print(f"Rows with side images: {(df['side_image_url'].fillna('') != '').sum()}")


if __name__ == "__main__":
    main()
