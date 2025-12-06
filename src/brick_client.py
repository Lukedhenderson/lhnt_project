import socket
import sys
import time

udp_sock = None

def clamp(v, lo, hi): return lo if v < lo else hi if v > hi else v
# Configuration
# Ports and secret, make the ports unique and 1024 < (DISCOVERY_PORT != CONTROL_PORT) < 65536
# (90, 90, 90)
#
# (50, 75, 80)
# (70, 75, 90)
# (90, 75, 110)
# (110, 75, 120)
# (130, 75, 130)
# (150, 75, 140)
#
# (50, 95, 50) bad
# (70, 95, 95) bad
# (90, 95, 100) almost bad
# (110, 95, 110)
# (130, 95, 120)
# (150, 95, 130)
#
# (50, 115, 30) bad
# (70, 115, 40) bad
# (90, 115, 80) bad
# (110, 115, 90) almost bad
# (130, 115, 100)
# (150, 115, 110)
#
# (50, 135, 30)bad
# (70, 135, 30)bad
# (90, 135, 30)bad
# (110, 135, 80) bad/almost bad
# (130, 135, 90)
# (150, 135, 100)


DISCOVERY_PORT = 65130
CONTROL_PORT = 65131
UDP_REPLY_MSG = b"passw" # should be the exact same as in the ESP32 client

DEADZONE = .2  # ignore minor noise
UPDATE_THRESHOLD = 0.01  # only print if moved significantly
DIAGONAL_THRESHOLD = 0.7 # higher = has to be more "diagonal" for it to count as diagonal

def handle_incoming_udp(udp_sock, data: bytes, addr):
    ip, port = addr[0], addr[1]
    print(f"[+] Received UDP {len(data)} bytes from {ip}:{port} -> {data!r}")
    try:
        time.sleep(.5)
        udp_sock.sendto(UDP_REPLY_MSG, (ip, port))
        print(f"[>] Sent UDP reply to {ip}:{port}")
        return ip, True
    except Exception as e:
        print(f"[!] Failed to send UDP reply to {ip}:{port}: {e}")
    return None, False



def send_motor_direction_packet(ip, msg):
    try:
        with socket.create_connection((ip, CONTROL_PORT), timeout=5) as s:
            s.sendall(msg)
            s.settimeout(.1) # increase this number if the packet is getting cut short
            s.recv(4096)
    except socket.timeout:
        pass
    except Exception as e:
        print(f"[!] TCP connect/send to {ip}:{CONTROL_PORT} failed: {e}")

def discover_esp():
    # create UDP socket & bind, same as you already do
    global udp_sock
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(("", DISCOVERY_PORT))

    has_connected = False
    esp_ip = None

    while not has_connected:
        print("Listening for ESP32 broadcast...")
        data, addr = udp_sock.recvfrom(4096)
        esp_ip, has_connected = handle_incoming_udp(udp_sock, data, addr)

    print(f"Paired with ESP32 at {esp_ip}")
    return esp_ip


