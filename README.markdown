# Secure Group Messaging with Cryptographic Watermarking

This project, developed as a Final Year Project for the Bachelor of Information Engineering at The Chinese University of Hong Kong, implements a secure group messaging system integrating TreeKEM-based group key management with Discrete Cosine Transform (DCT) and Least Significant Bit (LSB) watermarking techniques. The system ensures confidentiality, forward secrecy, and data authenticity for text and photo sharing, featuring a command-line tool and a Telegram bot for practical deployment.

## Project Overview

The system addresses the challenges of secure group messaging by combining:
- **TreeKEM**: A scalable protocol for group key management using X25519 key exchange and HKDF derivation, ensuring forward secrecy.
- **AES-CBC Encryption**: Secures text and images with 256-bit keys, supporting chunked encryption for large files.
- **DCT and LSB Watermarking**: Embeds tamper-evident markers in images for authenticity verification, resilient to compression and cut attacks.
- **Telegram Bot**: Facilitates secure photo sharing in group chats with encrypted metadata.

The project is implemented in Python and includes:
- A command-line tool (`encrypt.py`, `decrypt.py`) for encrypting/decrypting text and images.
- A Telegram bot (`main.py`, `handlers.py`) for real-time photo sharing.

## Features

- **End-to-End Encryption (E2EE)**: Only authorized group members can decrypt messages, using AES-256-CBC and X25519 key exchange.
- **Dynamic Group Management**: Efficiently updates group keys when members join or leave, ensuring forward secrecy (5-60 ms for 2-50 members).
- **Watermarking**:
  - **DCT**: Embeds visual watermarks in images (PSNR ≈ 40 dB), robust against JPEG compression and cropping.
  - **LSB**: Embeds encrypted metadata (e.g., group ID, timestamp) with high capacity and redundancy (PSNR > 50 dB).
- **Telegram Integration**: Share photos securely in group chats using `/share` and `/view_{user_id}` commands, with watermarked photos delivered in 2-3 seconds.
- **Scalability**: Supports groups up to 50 members with stable memory usage (50-55 MB).
- **Robustness**: Defends against cut attacks through DCT's frequency-domain embedding and LSB's redundant metadata distribution.

## Project Structure

```
├── data
│   ├── photos
│   │   └── testphoto.png
│   └── watermarks
│       └── watermark.png
├── output
│   ├── decrypted
│   ├── encrypted
│   ├── extracted
│   ├── keys
│   └── original
├── src
│   ├── bot
│   │   ├── handlers.py
│   │   └── main.py
│   ├── utils
│   │   ├── crypto.py
│   │   ├── treekem.py
│   │   └── watermark.py
│   ├── decrypt.py
│   └── encrypt.py
├── requirements.txt
├── structure.txt
└── README.md
```

- **data/**: Stores test images and watermark files.
- **output/**: Stores encrypted, decrypted, extracted, and key files.
- **src/**: Contains source code.
  - **bot/**: Telegram bot implementation.
  - **utils/**: Cryptographic, watermarking, and TreeKEM utilities.
  - **decrypt.py**, **encrypt.py**: Command-line tools for encryption/decryption.
- **requirements.txt**: Lists Python dependencies.
- **structure.txt**: Describes project structure.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/secure-group-messaging.git
   cd secure-group-messaging
   ```

2. **Set Up a Virtual Environment** (Optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Dependencies include:
   - cryptography==41.0.7
   - opencv-python==4.9.0
   - Pillow==10.2.0
   - numpy==1.25.4
   - python-telegram-bot==21.0.1
   - python-dotenv==1.0.1

4. **Set Up Telegram Bot** (For bot functionality):
   - Create a Telegram bot via [BotFather](https://t.me/BotFather) and obtain a `TELEGRAM_BOT_TOKEN`.
   - Create a `.env` file in the project root:
     ```env
     TELEGRAM_BOT_TOKEN=your_bot_token_here
     ```

5. **Prepare Input Files**:
   - Place test images in `data/photos/` (e.g., `testphoto.png`).
   - Place watermark images in `data/watermarks/` (e.g., `watermark.png`).

## Usage

### Command-Line Tool

1. **Encrypt Text or Photos**:
   ```bash
   python src/encrypt.py
   ```
   - Follow prompts to select 'text' or 'photo', specify group size, and provide input (e.g., message or photo path).
   - Outputs encrypted files to `output/encrypted/` and watermarked photos to `output/decrypted/`.
   - Example:
     - Input: `text`, 5 members, message "Hello, secure group!"
     - Output: `output/encrypted/encrypted_messages.txt`, `output/encrypted/derived_key.bin`
     - Input: `photo`, `data/photos/testphoto.png`, DCT and LSB watermarks
     - Output: `output/decrypted/dct_watermarked.png`, `output/decrypted/lsb_watermarked.png`, `output/decrypted/final_watermarked.png`

2. **Decrypt Text or Photos**:
   ```bash
   python src/decrypt.py
   ```
   - Select 'text' or 'photo', provide derived key filename (e.g., `derived_key.bin`), and specify input files.
   - Outputs decrypted text to console or extracted watermarks to `output/extracted/`.
   - Example:
     - Input: `text`, `derived_key.bin`
     - Output: Decrypted message printed to console
     - Input: `photo`, `final_watermarked.png`, `data/photos/testphoto.png`
     - Output: `output/extracted/extracted_dct_watermark.png`, decrypted LSB metadata printed

### Telegram Bot

1. **Run the Bot**:
   ```bash
   python src/bot/main.py
   ```

2. **Interact with the Bot**:
   - In a Telegram group, use `/start` to initialize the bot.
   - Use `/share` to share a photo:
     - The bot prompts you to send the photo in a private chat.
     - After uploading, the bot notifies the group with a `/view_{user_id}` command.
   - Group members use `/view_{user_id}` to request the watermarked photo, which is delivered privately with a caption containing timestamp and receiver ID.
   - Example:
     - User 123456789 shares a photo.
     - Group message: "User 123456789 shared a photo. Reply: /view_123456789"
     - Member uses `/view_123456789` and receives `output/decrypted/final_123456789_{timestamp}.png`.

3. **Verify Watermarks**:
   - Use `decrypt.py` to extract DCT and LSB watermarks from received photos.
   - Example:
     ```bash
     python src/decrypt.py
     ```
     - Input: `photo`, `final_123456789_{timestamp}.png`, `data/photos/testphoto.png`, `derived_key_123456789_{timestamp}.bin`
     - Output: Extracted DCT watermark and decrypted LSB metadata (e.g., group ID, timestamp, member list).

## Performance

- **TreeKEM Key Management**:
  - Key generation: 5.2 ms (2 members) to 123.5 ms (100 members).
  - Key updates: 15-30 ms, logarithmic scaling.
- **AES Encryption/Decryption**:
  - Text (100 characters): ~3 ms.
  - Photo (786 KB): ~45 ms (encryption), ~41 ms (decryption).
- **Watermarking**:
  - DCT: 320 ms (embedding), PSNR ≈ 40.2 dB, 85% extraction success after 50% crop.
  - LSB: 150 ms (embedding), PSNR > 50 dB, 75% bit accuracy after 50% crop.
- **Telegram Bot**: 500-510 ms for photo sharing, 100% metadata accuracy.
- **Scalability**: Stable for up to 50 members, memory usage 50-60 MB.

## Security Features

- **Forward Secrecy**: Removed members cannot decrypt new content (verified in tests).
- **Tamper Resistance**: CRC32 checksums and AES encryption ensure data integrity.
- **Watermark Robustness**: DCT and LSB watermarks resist compression and cut attacks.
- **Post-Quantum Readiness**: Modular design supports integration of Kyber or CSIDH.

## Future Enhancements

- **Parallel Key Derivation**: Use Python's `multiprocessing` to optimize TreeKEM for large groups.
- **Post-Quantum Cryptography**: Integrate Kyber or CSIDH in `treekem.py`.
- **Enhanced LSB Watermarking**: Add Reed-Solomon error-correcting codes for better robustness.
- **Optimized DCT Watermarking**: Use fast Fourier transform libraries to reduce embedding time.
- **Extended Bot Functionality**: Support video sharing and role-based access.
- **Key Security**: Add password-based encryption for user keys in `output/keys/`.

## References

- Barnes, R., et al. (2020). TreeKEM: A Protocol for Scalable Group Key Agreement. IETF.
- Cox, I., et al. (2007). Digital Watermarking and Steganography. Morgan Kaufmann.
- Cohn-Gordon, K., et al. (2019). On Ends-to-Ends Encryption: Asynchronous Group Messaging with Strong Security Guarantees. ACM CCS.
- Project report (`project.pdf`) for detailed methodology and results.

## Contributors

- TSOI, Ming Hon (1155175123)
- ZHANG, Yi Yao (1155174982)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.