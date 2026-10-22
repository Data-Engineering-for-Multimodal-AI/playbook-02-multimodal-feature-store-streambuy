# Sample Data — Attribution & Notes

The sample data in this directory is provided for educational purposes to
accompany Chapter 2 of *Data Engineering for Multimodal AI*.

## Sources and licenses

| Folder | Files | Source | License |
|---|---|---|---|
| `product_images/` | 19 product photos (35 MB) | [Unsplash](https://unsplash.com) and [Pexels](https://www.pexels.com) | [Unsplash License](https://unsplash.com/license) or [Pexels License](https://www.pexels.com/license/). Both allow free use without attribution. Neither allows redistributing the photos on another stock-photo platform |
| `product_videos/` | 31 product clips (842 MB, stored with Git LFS) | [Pexels Videos](https://www.pexels.com/videos/) | [Pexels License](https://www.pexels.com/license/) |
| `reviews/` | 18 customer review text files | Written synthetically for this playbook; not real purchases or real users | MIT, like the code |

The source page and photographer of each image and video were not recorded
when the sample set was collected, so per-file attribution isn't available.
Neither license requires it.

Only a few files are used by the code: `test_pipeline.py` reads all 19
images, one review (`blue_yellow_sneakers_reviews.txt`) and one video
(`white_sneakers.mp4`). The other videos and reviews are there to try the
API with.

## Git LFS

The videos are stored with [Git LFS](https://git-lfs.com). A clone without
Git LFS contains small text pointer files instead of the videos, and the
video encoder reports that. See the main README for a full download (842 MB)
or a light one that fetches only the video the tests use.

## Important caveats

Because the images and videos come from multiple free-stock sources, the
products shown are **not identical across modalities**. A "white sneakers"
image and a "white sneakers" video may depict different shoes from different
photographers. This is intentional — the goal of the sample data is to
exercise the multimodal encoding pipeline, not to build a production-grade
product catalog. The encoders, storage layer, and retrieval pipeline work
the same way regardless of whether the data depicts the exact same physical
product.

If you are building a production system, you would source images, videos, and
reviews for the same SKU from your own product catalog.
