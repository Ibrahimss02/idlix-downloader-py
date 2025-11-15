#!/usr/bin/env python3
"""
Crypto helper for AES decryption
"""

import base64
import hashlib
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def add_base64_padding(b64_string):
    """Add padding to base64 string"""
    return b64_string + '=' * (-len(b64_string) % 4)


def dec(r, e):
    """Key derivation function"""
    r_list = [r[i:i + 2] for i in range(2, len(r), 4)]
    m_padded = add_base64_padding(e[::-1])
    try:
        decoded_m = base64.b64decode(m_padded).decode('utf-8')
    except Exception as ex:
        print(f"Base64 decoding error: {ex}")
        return ""

    decoded_m_list = decoded_m.split("|")
    return "".join("\\x" + r_list[int(s)] for s in decoded_m_list if s.isdigit() and int(s) < len(r_list))


class CryptoJsAes:
    """CryptoJS-compatible AES encryption/decryption"""
    
    @staticmethod
    def decrypt(json_str, passphrase):
        """
        Decrypt data encrypted with CryptoJS
        
        Args:
            json_str (str): JSON string with ct, iv, s fields
            passphrase (str): Decryption passphrase
            
        Returns:
            str: Decrypted plaintext
        """
        json_data = json.loads(json_str)
        salt = bytes.fromhex(json_data["s"])
        iv = bytes.fromhex(json_data["iv"])
        ct = base64.b64decode(json_data["ct"])

        concated_passphrase = passphrase.encode() + salt
        result = hashlib.md5(concated_passphrase).digest()
        for _ in range(1, 3):
            result += hashlib.md5(result + concated_passphrase).digest()
        key = result[:32]

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(ct)

        try:
            return json.loads(CryptoJsAes._unpad(decrypted_data).decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    
    @staticmethod
    def _pad(s):
        """PKCS7 padding"""
        padding = AES.block_size - len(s) % AES.block_size
        return s + bytes([padding]) * padding

    @staticmethod
    def _unpad(s):
        """Remove PKCS7 padding"""
        return s[:-s[-1]]
    
    @staticmethod
    def encrypt(value, passphrase):
        """
        Encrypt data compatible with CryptoJS
        
        Args:
            value: Data to encrypt (will be JSON serialized)
            passphrase (str): Encryption passphrase
            
        Returns:
            str: JSON string with encrypted data
        """
        import os
        salt = os.urandom(8)
        salted = b''
        dx = b''
        while len(salted) < 48:
            dx = hashlib.md5(dx + passphrase.encode() + salt).digest()
            salted += dx
        key = salted[:32]
        iv = salted[32:48]

        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(CryptoJsAes._pad(json.dumps(value).encode()))

        return json.dumps({
            "ct": base64.b64encode(encrypted_data).decode('utf-8'),
            "iv": iv.hex(),
            "s": salt.hex()
        })
