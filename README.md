# TIFF WSI Label Removal Tool

A **Proof of Concept** tool to remove label pages from TIFF/BigTIFF files without loading the entire file into memory.
This utility is especially helpful when dealing with **Whole Slide Images (WSIs)** where a **label page** is present and may contain sensitive information.

## Why This Is Useful for Whole Slide Images (WSIs) — Label Page Found in WSI

In many Whole Slide Imaging (WSI) workflows—particularly within pathology or clinical research—TIFF files can contain additional pages labeled with patient details or institutional data. These **label pages** often reside alongside the main high-resolution scan. By removing the label page:

- You **reduce privacy concerns** by stripping away potentially identifying metadata.
- You **retain** the primary macro or full-resolution image necessary for analysis and sharing.
- You **avoid** loading the entire file into memory, which is critical when working with large WSI data.

## Features

- Removes **Label** pages from TIFF/BigTIFF files (including WSIs).
- Preserves **Macro** and other non-label pages.
- Modifies XML metadata to remove references to label images.
- Operates at a **low-level** file structure, minimizing memory usage.

## Installation

## Install using pip:

* `pip install tiff-wsi-label-removal`

## Alternatively, install from source:

1. **Clone** the repository:

   * `git clone https://github.com/zenquiorra/tiff-wsi-label-removal.git`
   * `cd tiff-wsi-label-removal`
2. **Install** dependencies:

   * `python -m pip install -r requirements.txt`

   Ensure you have a compatible Python version (e.g., Python 3.7+).
3. (Optional) **Install** as a package:

   * `pip install .`

## Usage

You can use the script **directly** or via the  **installed CLI** .

### CLI usage (if installed)

If you have installed this package locally (via `pip install .` or through `pip install tiff-wsi-label-removal`), then run:

```bash
remove-label <input_tiff_file> <output_tiff_file>
```

Example:

```bash
remove-label sample_input.tiff sample_output.tiff
```

### Inside a python script (if installed)

  ```python
    from tiff_wsi_label_removal.tiffprocessor import copy_tiff_low_level
    copy_tiff_low_level(input_file_path, output_file_path)
  ```

### Direct usage from source (if requirements are installed)

  ```bash
  python remove_label.py <input_tiff_file> <output_tiff_file>
  ```
  
  Example:
  
  ```bash
  python remove_label.py sample_input.tiff sample_output.tiff
  ```

## How It Works

1. **Page Verification** : The script reads the TIFF structure via `tifffile`. It identifies pages based on the `ImageDescription` tag, looking for entries with `"Label"` or `"Macro"`.
2. **XML Modification** : For the first page (usually containing metadata), the code extracts the XML, parses it (with `xml.etree.ElementTree`), and removes references to the label information (looking for `PIM_DP_IMAGE_TYPE` = `"LABELIMAGE"`).
3. **Low-Level Copy** : The script copies the file **IFDs (Image File Directories)** and image data segments, but **skips** the label page. It preserves the overall structure (page offsets, IFD chains) so the resulting TIFF remains valid.
4. **Result** : You end up with a TIFF file that excludes the label page but retains other pages and images.

---

## Planned Optimizations

**Performance** :

* Reduce file seeks by collecting and sorting I/O regions.
* Use configurable buffer sizes for copying.
* Merge contiguous byte regions to minimize I/O calls.

**IFD Chain Integrity** :

* Perform deeper checks to ensure removing pages doesn’t break references.
* Test against different TIFF variants (e.g., multi-page, BigTIFF).

**Comprehensive Testing** :

* Run tests on larger and more diverse TIFF datasets.
* Validate other metadata tags (beyond `ImageDescription`).

**Technical Analysis** :

* Further review of TIFF/BigTIFF standards.
* Check how tools like *QuPath* handle label metadata and page chains.

---

## Contributing

Contributions are welcome!

* **Issues** : If you find a bug or have a question, open a GitHub issue.
* **Pull Requests** : If you’d like to fix something or add a new feature, feel free to create a PR.
