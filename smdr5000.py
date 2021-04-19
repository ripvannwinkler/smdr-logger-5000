import os
import socket
import sys
import datetime
import time
from dotenv import load_dotenv

# Mitel 5000 SMDR Protocol
# ---------------------------------------------------------------------------
# Once a valid socket connection has been established, the client must send a
# particular login sequence as its first smdr_login to the server. This
# smdr_login must take the form of:
#
# <byte_count><socket_type><password>0x00
#
# This smdr_login includes the following information:
#
#    byte_count: Indicates the byte count for the data being passed. Note that
#        the four bytes of the byte count is included in the smdr_login, and it
#        is in **little‐endian** format.
#
#    socket_type: Passed as hex 84 (0×84) to indicate an SMDR connection.
#
#    password: Can include up to 15 ASCII characters and is null‐terminated.
#        This password must match the 5000 CP SMDR password. The password is
#        configured via Database Programming (System\Sockets).For example, a
#        client with the password 12345678 could use the following to log in:
#        0x0A 0×00 0×00 0×00 0×84 0×31 0×32 0×33 0×34 0×35 0×36 0×37 0×38 0x00
#
# In the simplest case, we're sending b'\x02\x00\x00\x00\x84\x00':
#
#    \x02\x00\x00\x00 (two bytes total, see next line) \x84\x00         (SMDR
#    signal + null terminator)
#
# The following example is an SMDR record in hex format as it is sent from the
# 5000 CP. Note that the first four bytes is the length, and the last two bytes
# are a carriage return (CR) and a line‐feed (LF).
#
#    0×52 0×00 0×00 0×00 0×54 0x4C 0×43 0×20 0×31 0×31 0×32 0×30 0×32 0×20 0×39
#    0×34 0×30 0×30 0×33 0×20 0×39 0×36 0×31 0x2D 0×39 0×30 0×30 0×30 0×20 0×20
#    0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20
#    0×20 0×20 0×20 0×20 0×30 0×38 0x3A 0×33 0×36 0×20 0×30 0×30 0x3A 0×30 0×30
#    0x3A 0×30 0×33 0×20 0×24 0×30 0×30 0x2E 0×30 0×30 0×20 0×20 0×20 0×20 0×20
#    0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0×20 0x0D 0x0A
#
# The following example is the ASCII representation of the previous SMDR Record.
# Note that first row of bolded numbers represents the column (from 1 to 80) in
# which the specific SMDR field is located (e.g., the dialed digits field
# 961‐9000 starts at column 17, which is represented by a 7).
#
#    12345678901234567890123456789012345678901234567890123... TLC 11202 94003
#    961-9000   08:36 00:00:03 $00.00
#
# see also
#   https://web.archive.org/web/20131017133718/http://blog.denwa.uk.com/mitel-5000-smdr/
#   https://community.spiceworks.com/scripts/show/2965-mitel-5000-smdr-reader


def connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (os.getenv('HOST'), int(os.getenv('PORT')))
    sock.connect(server_address)
    print('Connected to %s on port %s.' % server_address)
    smdr_login = b'\x02\x00\x00\x00\x84\x00'
    sock.sendall(smdr_login)
    print('Waiting for data...')
    return sock


def processLine(record):
    text = record[4:-2].decode()
    now = datetime.datetime.now()
    output = '%s %s' % (now, text)
    fout.write('%s\n' % output)
    fout.flush()
    print(output)


def receiveData():
    sock = connect()

    try:
        while True:
            data = sock.recv(86)
            if data: processLine(data)
            else: break

    finally:
        sock.close()


def loop():
    while True:
        try:
            receiveData()
        except:
            e = sys.exc_info()[0]
            print('Error: %s' % e.with_traceback())
        finally:
            time.sleep(15)


if __name__ == "__main__":
    load_dotenv()
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', '4000'))
    script_path = os.path.realpath(__file__)
    log_directory = os.path.dirname(script_path)
    log_file = os.path.join(log_directory, 'smdr.log')
    print('Logging to %s' % log_file)
    fout = open("smdr.log", "a")
    loop()
