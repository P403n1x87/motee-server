import json
import socket

from message import Message


def discover_request(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.001)
        try:
            client.connect((ip, port))
        except Exception:
            return None
        client.sendall(Message("discover", ip).json().encode())
        try:
            result = json.loads(client.recv(1024).decode())
            return result if result.get("response", None) == "OK" else None
        except Exception:
            return False


for i in range(1, 255):
    discovered = discover_request(f"192.168.0.{i}", 8787)
    if discovered is not None:
        print(discovered)
