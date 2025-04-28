import os
from utils.crypto import (
    aes_decrypt, 
    decrypt_message, 
    decrypt_watermark,
    decrypt_chunked_data
)
from utils.watermark import extract_dct_watermark, decode_lsb

# Get the project root (src/)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_derived_key(filename):
    """加载派生密钥，处理版本标记"""
    with open(os.path.join(PROJECT_ROOT, "output", "encrypted", filename), "rb") as file:
        header = file.read(4)
        if header == b'CHK1':  # 新版本格式
            derived_key = file.read(32)
            lsb_length_bytes = file.read(4)
        else:  # 旧版本格式
            derived_key = header + file.read(28)
            lsb_length_bytes = file.read(4)
        
        lsb_length = int.from_bytes(lsb_length_bytes, byteorder='big') if lsb_length_bytes else None
        return derived_key, lsb_length

def decrypt_and_save_text(derived_key_filename="derived_key.bin"):
    derived_key, _ = load_derived_key(derived_key_filename)
    with open(os.path.join(PROJECT_ROOT, "output", "encrypted", "encrypted_messages.txt"), "rb") as file:
        encrypted_data = file.read()
    
    decrypted_message = decrypt_message(encrypted_data, derived_key)
    print("解密后的消息:", decrypted_message)

def decrypt_dct_watermark(original_image_path, watermarked_image_path, output_watermark_path):
    try:
        extracted_path = extract_dct_watermark(original_image_path, watermarked_image_path, output_watermark_path)
        if extracted_path:
            print(f"DCT水印提取并保存到 {extracted_path}")
        else:
            print("DCT水印提取失败")
    except Exception as e:
        print(f"DCT水印提取错误: {e}")

def decrypt_lsb_watermark(watermarked_image_path, lsb_length, derived_key):
    try:
        lsb_watermark_bytes = decode_lsb(watermarked_image_path, lsb_length)
        if lsb_watermark_bytes:
            decrypted_lsb_watermark = decrypt_watermark(lsb_watermark_bytes, derived_key)
            print(f"提取的LSB水印: {decrypted_lsb_watermark.decode('utf-8', errors='ignore')}")
        else:
            print("未找到LSB水印")
    except Exception as e:
        print(f"LSB水印解密失败: {e}")

if __name__ == "__main__":
    os.makedirs(os.path.join(PROJECT_ROOT, "output", "decrypted"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "output", "extracted"), exist_ok=True)
    
    choice = input("要解密什么? 输入 'text' 或 'photo': ").strip().lower()
    derived_key_filename = input("输入派生密钥文件名(默认: derived_key.bin): ").strip() or "derived_key.bin"
    derived_key, lsb_length = load_derived_key(derived_key_filename)
    
    if choice == 'text':
        decrypt_and_save_text(derived_key_filename)
    elif choice == 'photo':
        photo_to_decrypt = input("输入要解密的照片文件名(默认: final_watermarked.png): ").strip() or "final_watermarked.png"
        original_photo_path = input("输入原始未加水印照片路径(默认: data/photos/testphoto.png): ").strip() or os.path.join(PROJECT_ROOT, "data", "photos", "testphoto.png")
        
        dct_watermarked_image_path = os.path.join(PROJECT_ROOT, "output", "decrypted", photo_to_decrypt)
        output_dct_watermark_path = os.path.join(PROJECT_ROOT, "output", "extracted", "extracted_dct_watermark.png")

        if os.path.exists(dct_watermarked_image_path):
            print(f"从 '{dct_watermarked_image_path}' 解密DCT水印...")
            decrypt_dct_watermark(original_photo_path, dct_watermarked_image_path, output_dct_watermark_path)
        else:
            print(f"未找到DCT水印文件 '{dct_watermarked_image_path}'")

        if os.path.exists(dct_watermarked_image_path) and lsb_length:
            print(f"从 '{dct_watermarked_image_path}' 解密LSB水印...")
            decrypt_lsb_watermark(dct_watermarked_image_path, lsb_length, derived_key)
        else:
            print("未找到LSB水印或长度信息")
    else:
        print("无效输入，请输入 'text' 或 'photo'")