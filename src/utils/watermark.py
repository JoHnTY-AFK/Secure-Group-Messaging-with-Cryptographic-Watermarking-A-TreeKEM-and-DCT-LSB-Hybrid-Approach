import cv2
import numpy as np
from PIL import Image

def dct_watermark_color(image_path, watermark_path, output_path, alpha=0.1):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image from {image_path}")
    
    watermark = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
    if watermark is None:
        raise FileNotFoundError(f"Could not load watermark from {watermark_path}")
    
    watermark = cv2.resize(watermark, (image.shape[1], image.shape[0]))
    channels = cv2.split(image)
    watermarked_channels = []
    for channel in channels:
        channel_dct = cv2.dct(np.float32(channel))
        watermark_dct = cv2.dct(np.float32(watermark))
        watermarked_dct = channel_dct + alpha * watermark_dct
        watermarked_channel = cv2.idct(watermarked_dct)
        watermarked_channel = np.uint8(np.clip(watermarked_channel, 0, 255))
        watermarked_channels.append(watermarked_channel)
    watermarked_image = cv2.merge(watermarked_channels)
    cv2.imwrite(output_path, watermarked_image)
    return output_path

def encode_lsb(image_path, watermark_bytes, output_path):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    watermark_binary = ''.join(format(byte, '08b') for byte in watermark_bytes)
    watermark_length = len(watermark_binary)
    width, height = img.size

    # 检查水印是否超出图像容量
    if watermark_length > width * height * 3:
        raise ValueError("Watermark text too large for image")

    index = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if index < watermark_length:
                # 修改红色通道的 LSB
                r = (r & ~1) | int(watermark_binary[index])
                index += 1
            if index < watermark_length:
                # 修改绿色通道的 LSB
                g = (g & ~1) | int(watermark_binary[index])
                index += 1
            if index < watermark_length:
                # 修改蓝色通道的 LSB
                b = (b & ~1) | int(watermark_binary[index])
                index += 1
            pixels[x, y] = (r, g, b)

    # 保存嵌入水印后的图像
    img.save(output_path)
    return output_path

def extract_dct_watermark(original_image_path, watermarked_image_path, output_watermark_path, alpha=0.1):
    original_image = cv2.imread(original_image_path, cv2.IMREAD_GRAYSCALE)
    watermarked_image = cv2.imread(watermarked_image_path, cv2.IMREAD_GRAYSCALE)
    if original_image.shape != watermarked_image.shape:
        raise ValueError("Original and watermarked images must have the same dimensions.")
    original_dct = cv2.dct(np.float32(original_image))
    watermarked_dct = cv2.dct(np.float32(watermarked_image))
    watermark_dct = (watermarked_dct - original_dct) / alpha
    extracted_watermark = cv2.idct(watermark_dct)
    extracted_watermark = np.uint8(np.clip(extracted_watermark, 0, 255))
    cv2.imwrite(output_watermark_path, extracted_watermark)
    return output_watermark_path

def decode_lsb(image_path, watermark_length):
    img = Image.open(image_path).convert('RGB')
    pixels = img.load()
    watermark_binary = ''
    width, height = img.size
    index = 0

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            # 提取红色通道的 LSB
            watermark_binary += str(r & 1)
            index += 1
            if index >= watermark_length * 8:
                break

            # 提取绿色通道的 LSB
            watermark_binary += str(g & 1)
            index += 1
            if index >= watermark_length * 8:
                break

            # 提取蓝色通道的 LSB
            watermark_binary += str(b & 1)
            index += 1
            if index >= watermark_length * 8:
                break

        if index >= watermark_length * 8:
            break

    # 将二进制字符串转换为字节
    watermark_bytes = bytes(int(watermark_binary[i:i+8], 2) for i in range(0, len(watermark_binary), 8))
    return watermark_bytes