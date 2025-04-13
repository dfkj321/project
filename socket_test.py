import socket
import time

host = "rm-7xv4m6fn2cxl3c327jo.mysql.rds.aliyuncs.com"
port = 3306
timeout = 10

print(f"尝试连接 {host}:{port}，超时设置为 {timeout} 秒...")

start_time = time.time()
success = False

try:
    # 创建socket对象
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    # 尝试连接
    result = sock.connect_ex((host, port))
    
    if result == 0:
        print(f"成功连接到 {host}:{port}")
        success = True
    else:
        print(f"无法连接到 {host}:{port}，错误代码: {result}")
    
    # 关闭socket
    sock.close()
except Exception as e:
    print(f"连接过程中发生错误: {e}")

end_time = time.time()
print(f"连接测试耗时: {end_time - start_time:.2f} 秒")
print(f"连接结果: {'成功' if success else '失败'}")

# 尝试解析IP地址
try:
    ip_address = socket.gethostbyname(host)
    print(f"主机 {host} 解析到IP地址: {ip_address}")
except Exception as e:
    print(f"无法解析主机名: {e}") 