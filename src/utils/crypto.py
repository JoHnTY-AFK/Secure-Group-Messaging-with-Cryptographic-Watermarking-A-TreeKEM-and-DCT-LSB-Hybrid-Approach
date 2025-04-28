from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import binascii
import struct

# 常量定义
CHUNK_SIZE = 1024  # 每个加密块的大小(字节)
CRC_SIZE = 4  # CRC32校验和的大小

def aes_encrypt(data, key, iv=None):
    """改进的AES-CBC加密函数，支持分块加密"""
    iv = iv or os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted

def aes_decrypt(encrypted_data, key):
    """改进的AES-CBC解密函数，带错误恢复"""
    iv = encrypted_data[:16]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    try:
        decrypted_padded = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()
        return decrypted_data
    except Exception as e:
        print(f"解密失败: {e}")
        # 尝试恢复模式
        return recover_decrypted_data(encrypted_data[16:], decryptor)

def recover_decrypted_data(encrypted_data, decryptor):
    """尝试从损坏的加密数据中恢复尽可能多的内容"""
    block_size = algorithms.AES.block_size // 8
    recovered = bytearray()
    
    for i in range(0, len(encrypted_data), block_size):
        block = encrypted_data[i:i+block_size]
        try:
            recovered.extend(decryptor.update(block))
        except:
            recovered.extend(b'?' * len(block))  # 用问号标记损坏的块
    
    try:
        recovered.extend(decryptor.finalize())
    except:
        pass
    
    return bytes(recovered)

def encrypt_chunked_data(data, key):
    """分块加密数据，每块包含CRC校验"""
    chunks = []
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        crc = binascii.crc32(chunk).to_bytes(CRC_SIZE, 'big')
        encrypted_chunk = aes_encrypt(crc + chunk, key)
        chunks.append(encrypted_chunk)
    return b''.join(chunks)

def decrypt_chunked_data(encrypted_data, key):
    """解密分块数据，验证CRC校验"""
    iv_size = 16
    min_chunk_size = iv_size + CRC_SIZE + 16  # IV + CRC + 最小加密数据
    
    position = 0
    decrypted_parts = []
    
    while position < len(encrypted_data):
        remaining = len(encrypted_data) - position
        if remaining < min_chunk_size:
            print(f"警告: 剩余数据不足一个完整块({remaining}字节)")
            break
            
        iv = encrypted_data[position:position+iv_size]
        chunk_size = min(CHUNK_SIZE + CRC_SIZE + iv_size, len(encrypted_data) - position)
        chunk = encrypted_data[position:position+chunk_size]
        position += chunk_size
        
        try:
            decrypted = aes_decrypt(chunk, key)
            crc = int.from_bytes(decrypted[:CRC_SIZE], 'big')
            data_chunk = decrypted[CRC_SIZE:]
            
            if binascii.crc32(data_chunk) == crc:
                decrypted_parts.append(data_chunk)
            else:
                print(f"块CRC校验失败，位置{position-chunk_size}")
                decrypted_parts.append(data_chunk)  # 仍然使用，但标记为不可靠
        except Exception as e:
            print(f"解密块失败: {e}")
            decrypted_parts.append(b'[corrupted data]')
    
    return b''.join(decrypted_parts)

def encrypt_watermark(watermark, key):
    """加密水印数据，带CRC校验"""
    crc = binascii.crc32(watermark).to_bytes(CRC_SIZE, 'big')
    return aes_encrypt(crc + watermark, key)

def decrypt_watermark(encrypted_watermark, derived_key):
    """解水印数据，验证CRC"""
    decrypted = aes_decrypt(encrypted_watermark, derived_key)
    if len(decrypted) < CRC_SIZE:
        return decrypted  # 数据太短，无法提取CRC
        
    crc = int.from_bytes(decrypted[:CRC_SIZE], 'big')
    watermark = decrypted[CRC_SIZE:]
    
    if binascii.crc32(watermark) != crc:
        print("警告: 水印数据CRC校验失败")
    
    return watermark

def encrypt_long_message(message, derived_key):
    """加密长文本消息，使用分块和CRC校验"""
    message_bytes = message.encode('utf-8')
    return encrypt_chunked_data(message_bytes, derived_key)

def decrypt_message(encrypted_data, derived_key):
    """解密长文本消息，带错误恢复"""
    decrypted = decrypt_chunked_data(encrypted_data, derived_key)
    return decrypted.decode('utf-8', errors='replace')

def encrypt_photo(photo_path, derived_key):
    """加密照片，使用分块和CRC校验"""
    with open(photo_path, "rb") as photo_file:
        photo_data = photo_file.read()
    return encrypt_chunked_data(photo_data, derived_key)

def decrypt_photo(encrypted_data, derived_key):
    """解密照片，带错误恢复"""
    return decrypt_chunked_data(encrypted_data, derived_key)