# Secure Image Encryption with Watermarking

This project implements a secure image encryption system using TreeKEM for group key management, AES encryption, and three watermarking techniques: DCT (frequency domain), LSB (spatial domain), and encrypted textual watermarking.

## Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd project-folder

2. **Create a Virtual Environment**
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

3. **Install Dependencies**
    pip install -r requirements.txt

## Usage

1. **Run encrypt.py to encrypt text or photos with optional watermarking**
    python3 src/encrypt.py
    Choose 'text' or 'photo'.
    For photos, select DCT, LSB, and/or encrypted textual watermarking.
    Outputs to output/encrypted/.

2. **Run decrypt.py to decrypt and extract watermarks**
    Choose 'text' or 'photo'.
    For photos, extract encrypted watermark, DCT watermark (needs original image), and LSB watermark (needs text length).
    Outputs to output/decrypted/ and output/extracted/.

## Example Workflow

1. **Encrypt a Photo**
    Input: data/photos/testcase_1.png
    Watermarks: DCT (data/watermarks/watermark.png), LSB ("SecretMessage"), Text ("Alice:Bob")
    Output: output/encrypted/encrypted_photo.bin

2. **Decrypt and Extract**
    Input: output/encrypted/encrypted_photo.bin
    Output: output/decrypted/decrypted_photo.png
    Extracts: "Alice:Bob", DCT watermark (output/extracted/extracted_dct_watermark.png), "SecretMessage"
