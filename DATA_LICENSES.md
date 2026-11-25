# Data licenses

This file lists the datasets and models this playbook uses, where they come from, and their licenses. The code in this repository is MIT-licensed. That license does not cover third-party data or models; each one keeps its own license, listed below.

## Datasets

| Dataset | Source | License | In this repo |
|---|---|---|---|
| Product photos (19) | [Unsplash](https://unsplash.com) and [Pexels](https://www.pexels.com). Per-file sources were not recorded | [Unsplash License](https://unsplash.com/license) or [Pexels License](https://www.pexels.com/license/) | `sample_data/product_images/` (34 MB) |
| Product videos (31 clips) | [Pexels Videos](https://www.pexels.com/videos/). Per-file sources were not recorded | [Pexels License](https://www.pexels.com/license/) | `sample_data/product_videos/`, Git LFS (about 840 MB) |
| Customer reviews (18 text files) | Synthetic, written for this playbook; not real purchases or users | MIT (this repository) | `sample_data/reviews/` (72 KB) |

## Models

| Model | Source | License | How it's used |
|---|---|---|---|
| ResNet-18, ImageNet weights (`ResNet18_Weights.DEFAULT`) | [torchvision](https://pytorch.org/vision/stable/models.html) | BSD-3-Clause (torchvision), as the README states | Image and video-frame encoder. Downloaded by `make setup` (`python download_models.py`) and saved to `models/resnet18.pth` (about 45 MB) |
| all-MiniLM-L6-v2 | [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | Apache-2.0 | Review text encoder. Downloaded by `make setup` (`python download_models.py`) and saved to `models/all-MiniLM-L6-v2/` (about 80 MB) |

## Notes

- `sample_data/README.md` says the source page and photographer of each photo and video were not recorded, so per-file attribution is not available. It also says neither license allows redistributing the files on another stock-photo platform.

## Citations

- ResNet: K. He, X. Zhang, S. Ren and J. Sun, "Deep Residual Learning for Image Recognition", arXiv:1512.03385, 2015.
- Product photos and videos, all-MiniLM-L6-v2: no citation given by the source.
