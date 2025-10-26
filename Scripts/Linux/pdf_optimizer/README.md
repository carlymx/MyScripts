# 📄 optimize_PDF

A Bash script to optimize scanned PDFs (especially black-and-white documents) by extracting, cleaning, rescaling, and efficiently recompressing them.

> Ideal for property notes, legal deeds, faxes, forms, or any 1-bit scanned documents (CCITT).

## 📚 Table of Contents

- [Description](#-description)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Example](#-example)
- [License](#-license)

## 📖 Description

This script automates the optimization of scanned PDFs containing **CCITT Group 4**-compressed images (common in black-and-white documents).  
It extracts pages as TIFF images, cleans them using `unpaper`, rescales them to the desired resolution, and repackages them into a compact, readable PDF.

It significantly reduces file size without compromising legibility—perfect for archiving or sharing official documents.

## ✨ Features

- ✅ Supports PDFs with CCITT (black-and-white) images.
- ✅ Automatic noise, speckle, and border cleaning with `unpaper`.
- ✅ Configurable DPI (72–300).
- ✅ Preserves efficient compression (CCITT) in the final PDF.
- ✅ Interactive: user configures input, output, DPI, and cleanup.
- ✅ Creates output directories if they don’t exist.
- ✅ Checks and installs dependencies automatically (on Debian/Ubuntu systems).

## ⚙️ Requirements

The script requires the following tools:

- `ghostscript` – to render PDF pages as images.
- `imagemagick` – for format conversion (`convert`).
- `unpaper` – to clean scanned images.
- `poppler-utils` – includes `pdfimages`.
- `img2pdf` – to generate PDFs from images without quality loss.
- `qpdf` – to optimize and linearize the final PDF.

## 📥 Installation

1. Clone or download this repository:
   
   ```bash
   git clone https://github.com/carlymx/MyScripts
   cd ./MyScripts/Scripts/Linux/pdf_optimizer
   ```

2. Make the script executable:
    ```./pdf_optimizer.sh```

You will be asked for: 

    Input PDF path.
    Output directory (optional).
    Target DPI (72–300).
    Whether to delete temporary files at the end.

🧪 Example

    ```
    $ ./optimizar_PDF.sh
    🔍 Checking dependencies...
    ✅ All dependencies are installed.
    ----------------------------------------
    🔧 Configuration:
    
    Enter input PDF path: ./Nota_simple.pdf
    Enter output directory (or press Enter for same as input): ./export
    Enter output DPI (72–300, recommended 100–150): 120
    Delete temporary directories when done? (y/n): y
    
    ✅ Done!
    📄 Optimized PDF: ./export/Nota_simple_final_120dpi.pdf
    ```

📜 License 

This project is open source under the MIT License.
See LICENSE  for details.
