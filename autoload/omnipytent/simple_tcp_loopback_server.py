#!/usr/bin/python3

import sys
import socket
import threading
from contextlib import contextmanager

def read_all(con):
    buf = []
    while True:
        data = con.recv(1024)
        if data:
            buf.append(data)
        else:
            return b''.join(buf)

@contextmanager
def socket_bound(dlg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    sock.bind(('localhost', 0))
    sock.listen(0)

    active = [True]

    def server_thread():
        while active[0]:
            try:
                con, addr = sock.accept()
            except (OSError, socket.timeout):
                continue
            thread = threading.Thread(target=connection_thread, args=(con,))
            thread.daemon = True
            thread.start()

    def connection_thread(con):
        con.send(dlg(read_all(con)))
        con.close()

    thread = threading.Thread(target=server_thread)
    thread.daemon = True
    thread.start()

    try:
        yield sock.getsockname()[1]
    finally:
        active[0] = False
        sock.close()


def connect(port):
    return sock


if __name__ == '__main__':
    _, port, data = sys.argv
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', int(port)))
    sock.send(data.encode('utf8'))
    sock.shutdown(socket.SHUT_WR)
    try:
        buffer = sys.stdout.buffer
    except AttributeError:
        sys.stdout.write(read_all(sock))
    else:
        buffer.write(read_all(sock))
