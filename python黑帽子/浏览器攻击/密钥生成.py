from Crypto.PublicKey import RSA
import logging
import sys

# 设置日志配置
logging.basicConfig(
    filename="keygen.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def generate_rsa_keys(key_size=2048, exponent=65537):
    """
    生成 RSA 公钥和私钥对
    参数:
        key_size: 密钥长度（位），默认 2048
        exponent: 公钥指数，默认 65537
    返回:
        public_key: PEM 格式的公钥
        private_key: PEM 格式的私钥
    """
    try:
        # 生成 RSA 密钥对
        new_key = RSA.generate(key_size, e=exponent)
        
        # 导出公钥和私钥（PEM 格式）
        public_key = new_key.publickey().exportKey("PEM").decode('utf-8')
        private_key = new_key.exportKey("PEM").decode('utf-8')
        
        # 记录生成日志
        logging.info("RSA 密钥对生成成功")
        
        return public_key, private_key
    
    except Exception as e:
        logging.error(f"生成 RSA 密钥失败: {e}")
        print(f"[错误] 生成 RSA 密钥失败: {e}")
        sys.exit(1)

def save_keys(public_key, private_key, pub_file="public_key.pem", priv_file="private_key.pem"):
    """
    保存公钥和私钥到文件
    参数:
        public_key: 公钥字符串
        private_key: 私钥字符串
        pub_file: 公钥文件路径
        priv_file: 私钥文件路径
    """
    try:
        with open(pub_file, "w") as f:
            f.write(public_key)
        with open(priv_file, "w") as f:
            f.write(private_key)
        print(f"公钥已保存到 {pub_file}")
        print(f"私钥已保存到 {priv_file}")
        logging.info(f"公钥保存到 {pub_file}，私钥保存到 {priv_file}")
    
    except Exception as e:
        logging.error(f"保存密钥失败: {e}")
        print(f"[错误] 保存密钥失败: {e}")
        sys.exit(1)

def main():
    """
    主函数，生成并打印 RSA 密钥对
    """
    try:
        # 生成密钥对
        public_key, private_key = generate_rsa_keys()
        
        # 打印密钥
        print("\n公钥:")
        print(public_key)
        print("\n私钥:")
        print(private_key)
        
        # 保存密钥到文件
        save_keys(public_key, private_key)
        
    except Exception as e:
        logging.error(f"主程序错误: {e}")
        print(f"[错误] 主程序错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()