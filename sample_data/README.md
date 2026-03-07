# Sample Data — Attribution & Notes

The sample data in this directory is provided for educational purposes to
accompany Chapter 2 of *Data Engineering for Multimodal AI*.

## Sources

- **Product images** were collected from [Unsplash](https://unsplash.com) and
  [Pexels](https://www.pexels.com), both of which offer freely usable images
  under their respective licenses.
- **Product videos** were collected from [Pexels Videos](https://www.pexels.com/videos/),
  available under the Pexels license for free use.
- **Customer reviews** were generated synthetically to resemble realistic
  product feedback. They do not correspond to real purchases or real users.

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
