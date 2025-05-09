import zlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import logging
import sys
import argparse

# 设置日志配置
logging.basicConfig(
    filename="decrypt.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 默认私钥（需替换为有效的私钥）
DEFAULT_PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQCqGKukO1De7zhZj6+H0qtjTkVxwTCpvKe4eCZ0FPqri0cb2JZf
XJ/DgYSF6vUpwmJG8wVQZKjeGcjDOL5UlsuusFncCzWBQ7RKNUSesmQRMSGkVb1/
3j+skZ6UtW+5u09lHNsj6tQ51s1SPrCBkedbNf0Tp0GbMJDyR4e9T04ZZwIDAQAB
AoGAFijko56+qGyN8M0RVyaRAE1oFHr2z4U97k8Cmx1TeSBPkI75o/ZJPL4zIIIM
vncAut3csdMNdXsW5kf3qP3O3aZrVOb2h2zVR3bHMj1qQd6bNuYVSnrTE9m0Y2zv
M4xmi3S3e3uhaSrQ+4ZRbE5fnjE4j8eP4z2vH8b6fcQKbFCAQhAOdH0qlg==
-----END RSA PRIVATE KEY-----
"""

def decrypt_data(encrypted_data, private_key_str, chunk_size=256):
    """
    解密 Base64 编码的加密数据并解压缩
    参数:
        encrypted_data: Base64 编码的加密数据
        private_key_str: PEM 格式的私钥字符串
        chunk_size: 解密分块大小（与加密时的 chunk_size 一致）
    返回:
        解密并解压缩后的明文（字符串）
    """
    try:
        # Base64 解码
        encrypted = base64.b64decode(encrypted_data)
        print(f"Base64 解码后: {len(encrypted)} 字节")
        
        # 初始化 RSA 解密
        rsakey = RSA.import_key(private_key_str)
        cipher = PKCS1_OAEP.new(rsakey)
        
        # 分块解密
        decrypted = b""
        offset = 0
        while offset < len(encrypted):
            chunk = encrypted[offset:offset + chunk_size]
            if not chunk:
                break
            decrypted += cipher.decrypt(chunk)
            offset += chunk_size
        print(f"解密后: {len(decrypted)} 字节")
        
        # 解压缩
        plaintext = zlib.decompress(decrypted)
        print(f"解压缩后: {len(plaintext)} 字节")
        
        # 转换为字符串
        plaintext_str = plaintext.decode('utf-8', errors='ignore')
        logging.info("解密成功")
        
        return plaintext_str
    
    except Exception as e:
        logging.error(f"解密失败: {e}")
        print(f"[错误] 解密失败: {e}")
        raise

def main():
    """
    主函数，解析命令行参数并执行解密
    """
    parser = argparse.ArgumentParser(description="解密 RSA 加密的数据")
    parser.add_argument("--input", help="包含 Base64 编码加密数据的文件")
    parser.add_argument("--key", help="私钥文件路径", default=None)
    parser.add_argument("--output", help="输出明文的文件路径", default=None)
    
    args = parser.parse_args()
    
    try:
        # 加载私钥
        private_key = DEFAULT_PRIVATE_KEY
        if args.key:
            with open(args.key, "r") as f:
                private_key = f.read()
        logging.info("私钥加载成功")
        
        # 加载加密数据
        encrypted_data = ""
        if args.input:
            with open(args.input, "r") as f:
                encrypted_data = f.read().strip()
        else:
            encrypted_data = input("请输入 Base64 编码的加密数据: ").strip()
        if not encrypted_data:
            raise ValueError("加密数据为空")
        
        # 执行解密
        plaintext = decrypt_data(encrypted_data, private_key)
        print("\n解密后的明文:")
        print(plaintext)
        
        # 保存明文（可选）
        if args.output:
            with open(args.output, "w", encoding='utf-8') as f:
                f.write(plaintext)
            print(f"明文已保存到 {args.output}")
            logging.info(f"明文保存到 {args.output}")
        
    except Exception as e:
        logging.error(f"主程序错误: {e}")
        print(f"[错误] 主程序错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()