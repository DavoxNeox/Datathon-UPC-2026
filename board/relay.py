#!/usr/bin/env python3
"""Relay the model servers to the App Lab container, without opening them to the network.

    python3 board/relay.py --listen docker0 --ports 8081,8082
    python3 board/relay.py --listen 172.17.0.1 --ports 8081,8082 --target 127.0.0.1

The two llama-servers listen on 127.0.0.1 only (README step 5). The App Lab app runs in a
Docker container on its own network, where 127.0.0.1 is the container itself; the host is
reachable from it as `msgpack-rpc-router` (Docker's host-gateway, the docker0 address,
172.17.0.1 on our board). This relay accepts TCP connections on that address only, and
forwards each one to the same port on 127.0.0.1. Nothing listens on the Wi-Fi interface.

Standard library only. Installed as the math-relay systemd service by board/06_install_relay.sh.
"""
import argparse
import fcntl
import selectors
import socket
import struct
import sys
import threading

SIOCGIFADDR = 0x8915


def interface_address(name):
    """IPv4 address of a network interface (Linux), e.g. docker0 -> 172.17.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        packed = struct.pack("256s", name.encode()[:15])
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), SIOCGIFADDR, packed)[20:24])


def resolve_listen(spec):
    try:
        socket.inet_aton(spec)
        return spec
    except OSError:
        return interface_address(spec)


def pump(a, b):
    """Copy bytes both ways until either side closes."""
    sel = selectors.DefaultSelector()
    sel.register(a, selectors.EVENT_READ, b)
    sel.register(b, selectors.EVENT_READ, a)
    try:
        while True:
            for key, _ in sel.select():
                data = key.fileobj.recv(65536)
                if not data:
                    return
                key.data.sendall(data)
    except OSError:
        return
    finally:
        for s in (a, b):
            try:
                s.close()
            except OSError:
                pass


def serve(listen_host, port, target_host, ready=None):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((listen_host, port))
    server.listen(16)
    if ready is not None:
        ready(server.getsockname()[1])
    while True:
        client, _ = server.accept()
        try:
            upstream = socket.create_connection((target_host, port), timeout=10)
            upstream.settimeout(None)
        except OSError as error:
            print(f"port {port}: upstream {target_host}:{port} unreachable: {error}", file=sys.stderr, flush=True)
            client.close()
            continue
        threading.Thread(target=pump, args=(client, upstream), daemon=True).start()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--listen", default="docker0", help="address or interface name to listen on (default docker0)")
    p.add_argument("--ports", default="8081,8082", help="comma-separated ports to relay")
    p.add_argument("--target", default="127.0.0.1", help="where the servers really listen")
    args = p.parse_args()
    host = resolve_listen(args.listen)
    ports = [int(x) for x in args.ports.split(",") if x]
    print(f"relaying {host}:{ports} -> {args.target}", flush=True)
    threads = [threading.Thread(target=serve, args=(host, port, args.target), daemon=True) for port in ports]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
