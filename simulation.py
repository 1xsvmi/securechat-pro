"""
SecureChat Pro - Local Simulation & Security Tests
Runs entirely on 127.0.0.1 without external network.
"""

import socket
import threading
import time

from chat import recv_msg, send_msg
from crypto_core import (
    CryptoError,
    ReplayCache,
    decrypt,
    decrypt_details,
    encrypt,
    token_fingerprint,
)


PASSWORD = "Simulated-Secret-123!"


def run_security_tests():
    print("\n=== 1) Security Tests ===")

    def check(name, func):
        try:
            func()
            print(f"PASS {name}")
            return True
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            return False
        except Exception as exc:
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            return False

    def basic_encrypt_decrypt():
        token = encrypt(PASSWORD, "secret message")
        plain = decrypt(PASSWORD, token)
        assert plain == "secret message", "Message did not round-trip correctly"

    def wrong_password_fails():
        token = encrypt(PASSWORD, "secret")
        try:
            decrypt("wrong-password", token)
            raise AssertionError("Wrong password should have failed")
        except CryptoError:
            pass

    def tampered_token_fails():
        token = encrypt(PASSWORD, "secret")
        last = "A" if token[-1] != "A" else "B"
        bad = token[:-1] + last

        try:
            decrypt(PASSWORD, bad)
            raise AssertionError("Tampered ciphertext should have failed")
        except CryptoError:
            pass

    def replay_detection_works():
        cache = ReplayCache()
        token = encrypt(PASSWORD, "replay-test")

        cache.check_and_add(token)

        try:
            cache.check_and_add(token)
            raise AssertionError("Replay should have been detected")
        except CryptoError:
            pass

    def expired_token_fails():
        token = encrypt(PASSWORD, "old-message", ttl=-10000)

        try:
            decrypt(PASSWORD, token)
            raise AssertionError("Expired token should have been rejected")
        except CryptoError:
            pass

    def sc2_prefix_required():
        try:
            decrypt(PASSWORD, "not-a-valid-token")
            raise AssertionError("Non-SC2 token should have been rejected")
        except CryptoError:
            pass

    results = []
    results.append(check("Encrypt/Decrypt basic flow", basic_encrypt_decrypt))
    results.append(check("Wrong password rejected", wrong_password_fails))
    results.append(check("Tampered ciphertext rejected", tampered_token_fails))
    results.append(check("Replay cache detects duplicate token", replay_detection_works))
    results.append(check("Expired token rejected", expired_token_fails))
    results.append(check("Non-SC2 token rejected", sc2_prefix_required))

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"\nSecurity tests result: {passed}/{total} passed")

    if passed != total:
        raise SystemExit("Some security tests failed")


def run_manual_flow_simulation():
    print("\n=== 2) Manual GUI Flow Simulation ===")

    original = "Hello, this is a test message from the encryption window"
    token = encrypt(PASSWORD, original)

    print(f"Original message : {original}")
    print(f"Encrypted token  : {token}")
    print(f"Token fingerprint: {token_fingerprint(token)}")

    details = decrypt_details(PASSWORD, token)
    print(f"Decrypted message: {details['message']}")

    assert details["message"] == original
    print("PASS Manual flow simulation")


def run_auto_loopback_simulation():
    print("\n=== 3) Auto Two-Party Loopback Simulation ===")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    port = server.getsockname()[1]
    print(f"Local test server: 127.0.0.1:{port}")

    errors = []

    def alice():
        try:
            conn = socket.create_connection(("127.0.0.1", port), timeout=5)
            cache = ReplayCache()

            msg = "Hello Bob, this is a local encrypted simulation"
            token = encrypt(PASSWORD, msg)

            send_msg(conn, token)
            print(f"[Alice -> Bob] sent encrypted token ({len(token)} chars)")
            print(f"[Alice] fingerprint: {token_fingerprint(token)}")

            reply_token = recv_msg(conn)
            if reply_token is None:
                raise RuntimeError("No reply received")

            cache.check_and_add(reply_token)
            reply = decrypt(PASSWORD, reply_token)

            print(f"[Alice <- Bob] decrypted reply: {reply}")

            try:
                cache.check_and_add(reply_token)
                print("[Alice] WARNING: Replay was NOT blocked")
            except CryptoError as exc:
                print(f"[Alice] Replay protection: {exc}")

            conn.close()

        except Exception as exc:
            errors.append(("Alice", exc))

    def bob():
        try:
            conn, addr = server.accept()

            token = recv_msg(conn)
            if token is None:
                raise RuntimeError("No message received")

            msg = decrypt(PASSWORD, token)
            print(f"[Bob <- Alice] decrypted message: {msg}")

            reply = encrypt(PASSWORD, "Hello Alice, received successfully")
            send_msg(conn, reply)

            print(f"[Bob -> Alice] sent encrypted reply ({len(reply)} chars)")
            print(f"[Bob] fingerprint: {token_fingerprint(reply)}")

            conn.close()

        except Exception as exc:
            errors.append(("Bob", exc))

    t_alice = threading.Thread(target=alice)
    t_bob = threading.Thread(target=bob)

    t_alice.start()
    time.sleep(0.05)
    t_bob.start()

    t_alice.join(timeout=10)
    t_bob.join(timeout=10)

    server.close()

    if errors:
        for name, exc in errors:
            print(f"FAIL Error in {name}: {type(exc).__name__}: {exc}")
        raise SystemExit("Loopback simulation failed")

    print("PASS Auto loopback simulation")


def main():
    print("=== SecureChat Pro Simulation ===")
    print("This runs locally and does not require internet.")

    run_security_tests()
    run_manual_flow_simulation()
    run_auto_loopback_simulation()

    print("\nAll simulations completed successfully.")
    print("Next steps:")
    print("  python chat.py --listen --auto")
    print("  python chat.py --connect 127.0.0.1 --auto")
    print("Or manual mode:")
    print("  python chat.py")
    print("  python crypt_app.py")


if __name__ == "__main__":
    main()
