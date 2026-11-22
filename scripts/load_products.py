"""Check a folder of products and add them to the running API.

    make load-samples                  # the 19 sample products
    make check-data DIR=my_products    # check your own folder, send nothing
    make load DIR=my_products          # check it, then add every product

Your folder holds one file per product and modality, named after the product:

    my_products/
      images/   red_runner.jpg  blue_tote.png      (.jpg .jpeg .png .webp)
      reviews/  red_runner.txt  blue_tote.txt      (.txt, UTF-8, optional)
      videos/   red_runner.mp4                     (.mp4 .mov .avi .webm, optional)

A product needs at least one file. Every file is checked first: images must
open and be at least 32x32, reviews must be non-empty UTF-8 text, videos must
have readable frames (and not be Git LFS pointers). If any file fails, nothing
is sent. Products already in the database (same name) are skipped, so it is
safe to rerun. Each product goes to POST /products/, the request from the
book's curl example, and the script waits until every job has finished.

Needs the API running (make serve), and DATABASE_URL if PostgreSQL isn't on 5432.
"""

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = os.environ.get("API_URL", "http://localhost:8000")
DSN = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/streambuy_features")
FOLDERS = {"image": ("images", "product_images"), "review": ("reviews",), "video": ("videos", "product_videos")}
EXTENSIONS = {"image": {".jpg", ".jpeg", ".png", ".webp"}, "review": {".txt"},
              "video": {".mp4", ".mov", ".avi", ".webm"}}
TYPES = {"sneakers": "footwear", "boots": "footwear", "sandals": "footwear",
         "headphones": "audio", "earbuds": "audio", "backpack": "bags", "waterbottle": "drinkware"}


def check_file(modality, path):
    """Return a problem description, or None if the file is usable."""
    if path.stat().st_size == 0:
        return "empty file"
    if path.read_bytes()[:40].startswith(b"version https://git-lfs"):
        return "Git LFS pointer, not the file (run git lfs pull)"
    if modality == "image":
        from PIL import Image
        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                if min(im.size) < 32:
                    return f"too small ({im.size[0]}x{im.size[1]}), needs at least 32x32"
        except Exception as e:
            return f"can't open as an image ({e.__class__.__name__})"
    elif modality == "review":
        try:
            if not path.read_text(encoding="utf-8").strip():
                return "no text"
        except UnicodeDecodeError:
            return "not UTF-8 text"
    else:
        import cv2
        cap = cv2.VideoCapture(str(path))
        ok, _ = cap.read()
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        if not ok or frames <= 0:
            return "no readable video frames"
    return None


def scan(folder, samples=False):
    """Group files by product name. Returns ({name: {modality: path}}, [problems])."""
    products, problems = {}, []
    for modality, names in FOLDERS.items():
        if samples and modality == "video":
            continue  # the sample clips show different products from the photos, on purpose
        sub = next((folder / n for n in names if (folder / n).is_dir()), None)
        if sub is None:
            continue
        for path in sorted(sub.iterdir()):
            if path.name.startswith("."):
                continue
            if path.suffix.lower() not in EXTENSIONS[modality]:
                problems.append(f"{path.relative_to(folder)}: not {'an' if modality[0] in 'aeiou' else 'a'} {modality} file type "
                                f"({', '.join(sorted(EXTENSIONS[modality]))})")
                continue
            name = path.stem.removesuffix("_reviews") if modality == "review" else path.stem
            problem = check_file(modality, path)
            if problem:
                problems.append(f"{path.relative_to(folder)}: {problem}")
            products.setdefault(name, {})[modality] = path.resolve()
    if samples:
        # blue_yellow_sneakers_2 is a second photo of blue_yellow_sneakers and shares its reviews
        for name, files in products.items():
            base = name.removesuffix("_2")
            if "review" not in files and base != name and "review" in products.get(base, {}):
                files["review"] = products[base]["review"]
        products = {n: f for n, f in products.items() if "image" in f}
    return products, problems


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


async def existing_names():
    import asyncpg
    conn = await asyncpg.connect(DSN)
    try:
        return {r["name"] for r in await conn.fetch("SELECT name FROM products")}
    finally:
        await conn.close()


def main():
    p = argparse.ArgumentParser(description="Check a folder of products and add them to the API.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--dir", type=Path, help="your folder (images/, reviews/, videos/)")
    src.add_argument("--samples", action="store_true", help="the sample products in sample_data/")
    p.add_argument("--check-only", action="store_true", help="check the files and send nothing")
    args = p.parse_args()

    folder = ROOT / "sample_data" if args.samples else args.dir
    if not folder.is_dir():
        sys.exit(f"No such folder: {folder}")
    products, problems = scan(folder, samples=args.samples)
    if not products and not problems:
        sys.exit(f"No product files found. Put them in {folder}/images, /reviews or /videos.")

    counts = {m: sum(m in f for f in products.values()) for m in FOLDERS}
    print(f"{len(products)} products in {folder}: "
          + ", ".join(f"{n} {m}{'s' if n != 1 else ''}" for m, n in counts.items() if n))
    if problems:
        print(f"\n{len(problems)} file(s) can't be used:")
        for line in problems:
            print(f"  {line}")
        sys.exit("\nFix or remove them and run again. Nothing was sent.")
    print("All files passed the checks.")
    if args.check_only:
        return

    try:
        call("GET", "/openapi.json")
    except OSError:
        sys.exit(f"The API isn't answering at {API}. Start it first with: make serve")

    have = asyncio.run(existing_names())
    start = time.time()
    jobs = []
    for stem, files in sorted(products.items()):
        name = stem.replace("_", " ")
        if name in have:
            continue
        category = next((c for k, c in TYPES.items() if k in stem), None)
        paths = {m: str(f) for m, f in files.items()}
        job = call("POST", "/products/", {"name": name, "category": category,
                                         "brand": "StreamBuy" if args.samples else None,
                                         "data_paths": paths})
        jobs.append((name, job["job_id"], list(paths)))
    if not jobs:
        print(f"All {len(products)} products are already loaded.")
        return
    for name, job_id, modalities in jobs:
        while True:
            status = call("GET", f"/jobs/{job_id}")["status"]
            if status not in ("pending", "processing"):
                break
            time.sleep(0.5)
        print(f"  {status:8} {name:36} {' + '.join(modalities)}")
    print(f"Added {len(jobs)} products in {time.time() - start:.0f} s.")


if __name__ == "__main__":
    main()
