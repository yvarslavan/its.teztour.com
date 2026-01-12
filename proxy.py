import socket
import threading
import sys
import time
import os

def handle_client(client_socket, remote_host, remote_port):
    remote_socket = None
    try:
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.settimeout(10)
        # print(f"[*] Connecting to {remote_host}:{remote_port}...", file=sys.stderr)
        remote_socket.connect((remote_host, remote_port))
        # print(f"[*] Connected to {remote_host}:{remote_port}", file=sys.stderr)
        
        def forward(src, dst, direction):
            try:
                while True:
                    data = src.recv(4096)
                    if not data: 
                        # print(f"[{direction}] Connection closed", file=sys.stderr)
                        break
                    dst.send(data)
            except Exception as e:
                # print(f"[{direction}] Forward error: {e}", file=sys.stderr)
                pass
            finally:
                try:
                    src.close()
                except: pass
                try:
                    dst.close()
                except: pass
        
        t1 = threading.Thread(target=forward, args=(client_socket, remote_socket, "C->S"))
        t2 = threading.Thread(target=forward, args=(remote_socket, client_socket, "S->C"))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()

    except Exception as e:
        print(f"❌ Error connecting to {remote_host}:{remote_port}: {e}", file=sys.stderr)
        if remote_socket:
            try:
                remote_socket.close()
            except: pass
        client_socket.close()

def start_proxy(local_port, remote_host, remote_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', local_port))
    except PermissionError:
        print(f"❌ Permission denied binding to port {local_port}", file=sys.stderr)
        return

    server.listen(50)
    print(f"[*] Listening on 0.0.0.0:{local_port} -> {remote_host}:{remote_port}")
    sys.stdout.flush()
    
    while True:
        try:
            client, addr = server.accept()
            # print(f"[*] Connection from {addr[0]}", file=sys.stderr)
            t = threading.Thread(target=handle_client, args=(client, remote_host, remote_port))
            t.daemon = True
            t.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Accept error: {e}", file=sys.stderr)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python3 proxy.py <local_port> <remote_host> <remote_port>")
        sys.exit(1)
    
    try:
        start_proxy(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]))
    except KeyboardInterrupt:
        print("\nStopping proxy...")
