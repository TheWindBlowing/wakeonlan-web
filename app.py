'''
Author: Zhiwei Tao zwtao21@163.com
Date: 2024-12-13 01:03:41
LastEditTime: 2024-12-13 01:58:23
LastEditors: Zhiwei Tao zwtao21@163.com
FilePath: /wakeOnLan/app.py
Description: 
'''
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import subprocess
import socket
import struct
from scapy.all import ARP, Ether, srp
import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# 配置日志
def setup_logger():
    # 创建 logs 目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器 - 按大小轮转
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建日志记录器
logger = setup_logger()

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

def init_db():
    logger.info("初始化数据库")
    try:
        conn = sqlite3.connect('network_devices.db')
        c = conn.cursor()
        
        # 先删除旧表（如果存在）
        c.execute('DROP TABLE IF EXISTS devices')
        logger.info("删除旧的设备表")
        
        # 创建新表，MAC 地址作为唯一键
        c.execute('''
            CREATE TABLE IF NOT EXISTS devices
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             hostname TEXT,
             ip_address TEXT,
             mac_address TEXT UNIQUE,
             scan_time TIMESTAMP,
             network_segment TEXT)
        ''')
        logger.info("创建新的设备表")
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise

def scan_network(network_segment):
    logger.info(f"开始扫描网段: {network_segment}")
    try:
        # 验证 CIDR 格式
        if '/' not in network_segment:
            raise ValueError("网段格式错误，需要使用 CIDR 格式（例如：192.168.1.0/24）")

        # 获取所有可用的网络接口
        from scapy.arch import get_if_list
        
        # Linux 系统常用接口
        interfaces = get_if_list()
        logger.info(f"可用网络接口: {interfaces}")
        
        # Linux 优先使用的接口顺序
        linux_interfaces = ['eth0', 'ens33', 'enp0s3', 'wlan0', 'wlp2s0']
        iface = None
        
        # 查找第一个可用的接口
        for interface in linux_interfaces:
            if interface in interfaces:
                iface = interface
                break
        
        # 如果没有找到常用接口，使用第一个可用接口
        if not iface and interfaces:
            iface = interfaces[0]
            
        if not iface:
            raise Exception("未找到可用的网络接口")

        logger.info(f"使用网络接口: {iface}")
        
        # 直接使用 CIDR 格式进行扫描
        arp = ARP(pdst=network_segment)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        # 指定接口进行扫描，增加超时时间
        result = srp(packet, timeout=10, verbose=True, iface=iface)[0]
        
        devices = []
        logger.info(f"发现 {len(result)} 个设备")
        
        for sent, received in result:
            try:
                hostname = socket.gethostbyaddr(received.psrc)[0]
            except:
                hostname = "Unknown"
            
            device = {
                'hostname': hostname,
                'ip_address': received.psrc,
                'mac_address': received.hwsrc
            }
            logger.info(f"发现设备: {device}")
            devices.append(device)
        
        return devices
    except Exception as e:
        logger.error(f"扫描出错: {str(e)}")
        return []

def ping_scan(network_segment):
    devices = []
    for i in range(1, 255):
        ip = f"{network_segment}.{i}"
        try:
            # Linux ping 命令
            response = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                capture_output=True, 
                text=True
            )
            
            if response.returncode == 0:
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except:
                    hostname = "Unknown"
                
                # 获取 MAC 地址 (Linux)
                arp_output = subprocess.run(
                    ['arp', '-n', ip], 
                    capture_output=True, 
                    text=True
                )
                
                # 解析 ARP 输出获取 MAC 地址
                mac = "Unknown"
                if arp_output.returncode == 0:
                    # 解析 Linux arp 命令输出
                    lines = arp_output.stdout.splitlines()
                    for line in lines[1:]:  # 跳过标题行
                        parts = line.split()
                        if len(parts) >= 3 and parts[0] == ip:
                            mac = parts[2]
                            break
                
                devices.append({
                    'hostname': hostname,
                    'ip_address': ip,
                    'mac_address': mac
                })
        except Exception as e:
            logger.error(f"Ping扫描错误 {ip}: {str(e)}")
            continue
    
    return devices

# 添加路由来服务前端页面
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        if not request.is_json:
            logger.warning("请求Content-Type不是application/json")
            return jsonify({"error": "Content-Type 须是 application/json"}), 400
            
        data = request.get_json()
        if not data:
            logger.warning("请求体为空")
            return jsonify({"error": "请求体不能为空"}), 400
            
        network_segment = data.get('network_segment')
        if not network_segment:
            logger.warning("缺少network_segment参数")
            return jsonify({"error": "缺少必需参数 'network_segment'"}), 400
            
        logger.info(f"接收到扫描请求，网段: {network_segment}")
        devices = scan_network(network_segment)
        
        # 数据库操作
        conn = sqlite3.connect('network_devices.db')
        c = conn.cursor()
        
        for device in devices:
            try:
                # 尝试更新现有记录
                c.execute('''
                    UPDATE devices 
                    SET hostname = ?, 
                        ip_address = ?, 
                        scan_time = ?,
                        network_segment = ?
                    WHERE mac_address = ?
                ''', (
                    device['hostname'],
                    device['ip_address'],
                    datetime.datetime.now(),
                    network_segment,
                    device['mac_address']
                ))
                
                if c.rowcount == 0:
                    # 插入新记录
                    c.execute('''
                        INSERT INTO devices 
                        (hostname, ip_address, mac_address, scan_time, network_segment)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        device['hostname'],
                        device['ip_address'],
                        device['mac_address'],
                        datetime.datetime.now(),
                        network_segment
                    ))
                    logger.info(f"��加新设备: {device['mac_address']}")
                else:
                    logger.info(f"更新设备信息: {device['mac_address']}")
                    
            except sqlite3.IntegrityError as e:
                logger.error(f"数据库操作错误: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        logger.info("扫描完成")
        return jsonify(devices)
        
    except Exception as e:
        logger.error(f"请求处理错误: {str(e)}")
        return jsonify({"error": f"请求处理错误: {str(e)}"}), 400

@app.route('/history', methods=['GET'])
def get_history():
    logger.info("获取历史记录")
    try:
        conn = sqlite3.connect('network_devices.db')
        c = conn.cursor()
        c.execute('''
            SELECT hostname, ip_address, mac_address, scan_time, network_segment
            FROM devices
            ORDER BY scan_time DESC
        ''')
        
        devices = []
        for row in c.fetchall():
            devices.append({
                'hostname': row[0],
                'ip_address': row[1],
                'mac_address': row[2],
                'scan_time': row[3],
                'network_segment': row[4]
            })
        
        conn.close()
        logger.info(f"返回 {len(devices)} ��历史记录")
        return jsonify(devices)
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/wake', methods=['POST'])
def wake_device():
    try:
        mac_address = request.json.get('mac_address')
        logger.info(f"尝试唤醒设备: {mac_address}")
        
        # 构建魔术包
        mac_bytes = bytes.fromhex(mac_address.replace(':', ''))
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        
        # 发送魔术包
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ('255.255.255.255', 9))
        
        logger.info(f"唤醒命令已发送: {mac_address}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"唤醒设备失败: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # 检查是否以 root 权限运行
    if os.geteuid() != 0:
        logger.error("此程序需要 root 权限才能运行")
        print("请使用 sudo 运行此程序")
        sys.exit(1)
        
    logger.info("启动应用程序")
    init_db()
    app.run(host='0.0.0.0', port=5100, debug=True)