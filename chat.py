"""
SecureChat Pro - Terminal Chat
CMD / PowerShell client
"""

import argparse
import getpass
import socket
import struct
import sys
import threading
import time

from crypto_core import PREFIX, CryptoError, ReplayCache, decrypt, encrypt


PORT = 5000
MAX_MSG = 1_000_000

PRINT_LOCK = threading.Lock()


def safe_print(*args, **kwargs):
    with PRINT_LOCK:
        print(*args, **kwargs, flush=True)


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)


def send_msg(sock, text: str) -> None:
    data = text.encode("utf-8")

    if len(data) > MAX_MSG:
        raise ValueError("Message is too large")

    sock.sendall(struct.pack(">I", len(data)) + data)


def recv_exact(sock, n: int):
    buf = b""

    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk

    return buf


def recv_msg(sock):
    header = recv_exact(sock, 4)
    if header is None:
        return None

    (length,) = struct.unpack(">I", header)

    if length > MAX_MSG:
        return None

    body = recv_exact(sock, length)
    if body is None:
        return None

    return body.decode("utf-8")


def local_ips():
    ips = set()

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    return sorted(ips)


def print_help(auto_mode: bool) -> None:
    safe_print("\nCommands:")
    safe_print("  /exit   Exit")
    safe_print("  /help   This help")
    safe_print("  /ips    Show local IP addresses")
    safe_print("  /status Connection status")

    if auto_mode:
        safe_print("\nMode: Automatic")
        safe_print("Every message you type will be encrypted automatically before sending.")
    else:
        safe_print("\nMode: Manual")
        safe_print("Use crypt_app.py to encrypt the message, then copy the encrypted token here.")


def receiver(sock, peer: str, auto_mode: bool, password, cache):
    while True:
        try:
            token = recv_msg(sock)
        except OSError:
            token = None

        if token is None:
            safe_print("\n[!] Connection closed.")
            break

        stamp = time.strftime("%H:%M:%S")

        if auto_mode:
            try:
                if cache is not None:
                    cache.check_and_add(token)

                msg = decrypt(password, token)
                safe_print(f"\n[{stamp}] {peer}: {msg}")
            except CryptoError as exc:
                safe_print(f"\n[!] Invalid message: {exc}")
        else:
            if token.startswith(PREFIX):
                safe_print(f"\n[{stamp}] {peer} - encrypted token:")
                safe_print(token)
                safe_print("-> Paste it into crypt_app.py to decrypt.")
            else:
                safe_print(f"\n[{stamp}] {peer}:")
                safe_print(token)


def main():
    parser = argparse.ArgumentParser(description="SecureChat Pro terminal client")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--listen", action="store_true", help="Wait for incoming connection")
    group.add_argument("--connect", metavar="IP", help="Connect to IP")
    parser.add_argument("--port", type=int, default=PORT, help="Connection port")
    parser.add_argument("--auto", action="store_true", help="Automatic encryption inside terminal")

    args = parser.parse_args()

    safe_print("=== SecureChat Pro ===")
    safe_print("AES-256-GCM | scrypt | SC2 envelope")

    ips = local_ips()
    if ips:
        safe_print("Suggested local IPs: " + ", ".join(ips))
    else:
        safe_print("Could not detect local IP. On Windows use: ipconfig")

    password = None
    cache = None

    if args.auto:
        try:
            password = getpass.getpass("Shared password: ")
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)

        if not password:
            safe_print("Password is required in automatic mode.")
            sys.exit(1)

        cache = ReplayCache()

    if args.listen:
        mode = "1"
    elif args.connect:
        mode = "2"
    else:
        mode = ask("1) Wait for connection   2) Connect to IP : ")

    conn = None
    peer = ""
    port_used = args.port

    if mode == "1":
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind(("0.0.0.0", args.port))
        except OSError as exc:
            safe_print(f"[!] Failed to bind port: {exc}")
            server.close()
            sys.exit(1)

        server.listen(1)
        port_used = server.getsockname()[1]

        safe_print(f"Waiting for connection on port {port_used} ...")

        try:
            conn, addr = server.accept()
        except (KeyboardInterrupt, OSError):
            server.close()
            sys.exit(0)

        server.close()
        peer = addr[0]

    elif mode == "2":
        peer = args.connect or ask("Enter IP: ")

        if not peer:
            safe_print("No IP provided.")
            sys.exit(1)

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(10)

        try:
            conn.connect((peer, args.port))
        except OSError as exc:
            safe_print(f"[!] Connection failed: {exc}")
            conn.close()
            sys.exit(1)

        conn.settimeout(None)
        port_used = args.port

    else:
        safe_print("Invalid option.")
        sys.exit(1)

    safe_print(f"[OK] Connected with {peer}")
    safe_print("Type /help for commands, /exit to quit.\n")

    threading.Thread(
        target=receiver,
        args=(conn, peer, args.auto, password, cache),
        daemon=True,
    ).start()

    try:
        while True:
            line = input("> ")
            stripped = line.strip()
            cmd = stripped.lower()

            if cmd == "/exit":
                break

            if cmd.startswith("/"):
                if cmd == "/help":
                    print_help(args.auto)
                elif cmd == "/ips":
                    found = local_ips()
                    if found:
                        safe_print("IP: " + ", ".join(found))
                    else:
                        safe_print("No clear local IP addresses found.")
                elif cmd == "/status":
                    safe_print(
                        f"Mode: {'automatic' if args.auto else 'manual'} | "
                        f"Peer: {peer} | Port: {port_used}"
                    )
                else:
                    safe_print("[!] Unknown command. Type /help")
                continue

            if not stripped:
                continue

            payload = encrypt(password, stripped) if args.auto else stripped

            try:
                send_msg(conn, payload)
            except (OSError, ValueError) as exc:
                safe_print(f"[!] Send failed: {exc}")
                break

    except (KeyboardInterrupt, EOFError):
        pass
    except OSError as exc:
        safe_print(f"[!] Network error: {exc}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except OSError:
                pass
        safe_print("Connection closed.")


if __name__ == "__main__":
    main()
