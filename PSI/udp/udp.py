#!/bin/env python3
"""
KarelUDP client.

Author: Dmytro Osaulenko, homework for BI-PSI (Computer Networks) @ FIT CTU
Date: 05.06.2020
Requires: python3
Tested on python 3.8.3
"""
from typing import BinaryIO, List, Tuple, Dict

import argparse
import io
import ipaddress
import random
import socket
import struct
import time


SERVER_PORT = 4000
MAX_ATTEMPTS = 20
PACKET_HEADER_SIZE = 9  # bytes
PACKET_MAX_DATA_SIZE = 255  # bytes
MAX_PACKET_SIZE = PACKET_HEADER_SIZE + PACKET_MAX_DATA_SIZE
WINDOW_MAX_PACKETS = 8
WINDOW_MAX_SIZE = WINDOW_MAX_PACKETS * PACKET_MAX_DATA_SIZE
TIMEOUT = 0.1  # 100ms

DOWNLOAD_PHOTO = b"\x01"
UPLOAD_FIRMWARE = b"\x02"

SYN = 4  # third bit  (2 ^ 2)
FIN = 2  # second bit (2 ^ 1)
RST = 1  # first bit  (2 ^ 0)
NO_FLAGS = 0  # all bits are zeros

# for print/log purpose
BOLD_START = "\033[1m"
BOLD_END = "\033[0;0m"

TICK = random.randint(1, 1000)


def log_pipe(
    connection_id: int,
    sequence_number: int,
    ack_number: int,
    flags: int,
    data: bytes,
    operation: str,
    address: str,
) -> Tuple[int, int, int, int, bytes]:
    """
    Kind of replication of output produced by reference implementation
    (wanted to have same or similar output).

    Works almost as a `tee` program, takes 5 params (from which packet is
    constructed in create_packet() or which were returned by decode_packet())
    + one extra (operation string, either SEND or RECV),
    produces output and returns first 5 params.
    """

    global TICK
    TICK += random.randint(0, 5)

    print(
        f"{TICK:10d}  {connection_id:08X}  {BOLD_START}{operation}{BOLD_END}  "
        f"{address}:{SERVER_PORT}  seq={sequence_number} ack={ack_number} "
        f"flags={flags:02d} ",
        end="",
    )

    if data:
        print(f"data({len(data)}):", end="")

        if len(data) > 18:
            for byte in data[:8]:
                print(f" {byte:02x}", end="")

            print(" ...", end="")

            for byte in data[-8:]:
                print(f" {byte:02x}", end="")

            print()
        else:
            for byte in data:
                print(f" {byte:02x}", end="")
            print()
    else:
        print("data(0): --")

    return connection_id, sequence_number, ack_number, flags, data


def log_message(connection_id: int, message: str) -> None:
    """
    Kind of replication of output produced by reference implementation
    (wanted to have same or similar output).
    """
    global TICK
    TICK += random.randint(0, 5)
    print(f"{TICK:10d}  {connection_id:08X}  {message}")


def create_packet(
    connection_id: int,
    sequence_number: int,
    ack_number: int,
    flags: int,
    data: bytes,
) -> bytearray:
    """
    Create a packet in order to send it to the probe on Mars.
    Pack python native data types data to C types using struct.pack()
    """
    packet = bytearray()

    # more at help(struct) or https://docs.python.org/3/library/struct.html
    # '!' is network (= big-endian) endianness format
    # 'I' is unsigned int (4B)
    # 'H' is unsigned short int (2B)
    packet += struct.pack("!IHH", connection_id, sequence_number, ack_number)

    # now the rest is in the native endianness (according to the task)

    # '@' - native endianness (and alignment)
    # 'b' - signed char (1B)
    packet += struct.pack("@b", flags)

    # data are optional, packet must be at minimum 9B header + 0-255B data
    # 's' for 'char *' with length in bytes prefix
    packet += struct.pack(f"@{len(data)}s", data)

    return packet


def decode_packet(packet: bytes) -> Tuple[int, int, int, int, bytes]:
    """
    Gets raw bytes packet (probe response). Returns unpacked data.
    """
    connection_id, sequence_number, ack_number = struct.unpack(
        "!IHH", packet[:8]
    )
    (flags,) = struct.unpack("@b", packet[8:PACKET_HEADER_SIZE])
    (data,) = struct.unpack(
        f"@{len(packet[PACKET_HEADER_SIZE:])}s", packet[PACKET_HEADER_SIZE:],
    )

    return connection_id, sequence_number, ack_number, flags, data


def send_and_log(
    sock: socket.socket,
    connection_id: int,
    sequence_number: int,
    ack_number: int,
    flags: int,
    data: bytes,
) -> None:
    """
    Simple wrapper to log each request to stdout before sending it.
    """
    sock.send(
        create_packet(
            *log_pipe(
                connection_id=connection_id,
                sequence_number=sequence_number,
                ack_number=ack_number,
                flags=flags,
                data=data,
                operation="SEND",
                address=sock.getpeername()[0],
            )
        )
    )


def recv_and_log(sock: socket.socket) -> Tuple[int, int, int, int, bytes]:
    """
    Simple wrapper to log each responset to stdout after receiving it.
    """
    return log_pipe(
        *decode_packet(sock.recv(MAX_PACKET_SIZE)),
        "RECV",
        sock.getpeername()[0],
    )


def establish_connection(
    sock: socket.socket, operation: bytes
) -> Tuple[bool, int]:
    """
    Establish connection with the server (probe on Mars).
    Sends each 100 ms SYN flagged packet with either upload or download
    command until won't receive the connection id to use later.

    Returns a tuple of bool and int representing success
    (False for errors_occurred == False) and connection id (if succeeded).
    """
    # send first packet, expecting to get the same packet,
    # but with different first 4B (different connection_id,
    # will need to use that id). Sending each 100 ms till we'll get it.
    while True:

        send_and_log(
            sock=sock,
            connection_id=0,
            sequence_number=0,
            ack_number=0,
            flags=SYN,
            data=operation,
        )

        try:
            # rewrite connection_id (if flag is SYN) or then rewrite it again
            # dropping sequence_number and ack_number, we don't need it now
            (
                connection_id,
                sequence_number,
                ack_number,
                flags,
                data,
            ) = recv_and_log(sock)
        except socket.timeout:
            continue

        # wait for the SYN. Other packets (with data for e.g.)
        # will be dropped (they are not for us)
        if flags == SYN:

            if (
                connection_id != 0
                and sequence_number == 0
                and ack_number == 0
                and data == operation
            ):
                # we're good to go
                return False, connection_id

            # else -> something is wrong
            break

    return True, 0


def close_connection(
    sock: socket.socket,
    connection_id: int,
    sequence_number: int,
    ack_number: int,
) -> None:
    """
    Simple function to adhere the DRY principle and reduce code duplication.
    Closes the connection with peer.
    """

    # not the best solution, but it works
    for _ in range(3):
        send_and_log(
            sock=sock,
            connection_id=connection_id,
            sequence_number=sequence_number,
            ack_number=ack_number,
            flags=FIN,
            data=b"",
        )

        time.sleep(TIMEOUT)


def upload_firmware(sock: socket.socket, firmware: BinaryIO) -> None:
    """
    Handling firmware upload to the probe near Mars.
    """
    # get size of file to verify if transmitted data weren't corrupted
    # or if we transmitted everything
    firmware.seek(0, io.SEEK_END)
    firmware_size = firmware.tell()
    firmware.seek(0)

    # first byte in sliding window first packet
    sequence_number = 0

    # maximum amount of 20 attempts for window (8 packets) sending
    attempts = 0
    transferred = 0  # bytes

    window_queue: List[Tuple[int, bytes]] = []

    errors_occured, connection_id = establish_connection(
        sock=sock, operation=UPLOAD_FIRMWARE
    )

    if errors_occured:
        # yay! recursion (or goto 🤔)
        upload_firmware(sock, firmware)

    # first window
    for chunk_index in range(
        sequence_number, WINDOW_MAX_SIZE, PACKET_MAX_DATA_SIZE,
    ):
        chunk = firmware.read(PACKET_MAX_DATA_SIZE)
        if chunk == b"":
            break

        window_queue.append((chunk_index, chunk))

    while attempts < MAX_ATTEMPTS:

        # sending queue contents first
        for chunk_index, chunk in window_queue:
            send_and_log(
                sock=sock,
                connection_id=connection_id,
                sequence_number=chunk_index,
                ack_number=0,
                flags=NO_FLAGS,
                data=chunk,
            )

        # then try to get confirmation
        try:
            (
                connection_id_new,
                sequence_number_new,
                ack_number,
                flags,
                data,
            ) = recv_and_log(sock)
        except socket.timeout:
            log_message(connection_id, "event_timeout")
            attempts += 1
            continue

        # not for us
        if connection_id_new != connection_id:
            continue

        # wrong data
        if sequence_number_new != 0 or flags != NO_FLAGS or data != b"":
            send_and_log(
                sock=sock,
                connection_id=connection_id,
                sequence_number=0,
                ack_number=0,
                flags=RST,
                data=b"",
            )
            errors_occured = True
            break

        # already ack'ed
        if ack_number == sequence_number:
            continue

        # logging
        if transferred != 0 and transferred % WINDOW_MAX_SIZE == 0:
            log_message(
                connection_id,
                f"send_window: seq={sequence_number} "
                f"transferred={transferred}",
            )

        # we're done
        if (
            len(window_queue) < WINDOW_MAX_PACKETS
            and ack_number > window_queue[-1][0]
        ):
            if ack_number < sequence_number:
                transferred += (ack_number - sequence_number) + 2 ** 16
            else:
                transferred += ack_number - sequence_number
            sequence_number = ack_number
            break

        # ack'ing all packets in the window -> clearing window and
        # filling it up again
        if ack_number == (window_queue[-1][0] + PACKET_MAX_DATA_SIZE):
            window_queue.clear()
            attempts = 0
            sequence_number = ack_number
            transferred += WINDOW_MAX_SIZE

            for chunk_index in range(
                sequence_number,
                sequence_number + WINDOW_MAX_SIZE,
                PACKET_MAX_DATA_SIZE,
            ):
                chunk = firmware.read(PACKET_MAX_DATA_SIZE)
                if chunk == b"":
                    break

                window_queue.append((chunk_index % 65536, chunk))

        else:

            # otherwise try to figure out where ack_number is in the
            # window_queue (at what index), in order to drop ack'ed packets
            # and add new
            index = None

            # reserved is "optimization"
            for chunk_index, chunk in reversed(window_queue):
                if chunk_index == ack_number:
                    index = window_queue.index((chunk_index, chunk))
                    break

            if index is None:
                log_message(
                    connection_id,
                    "Prisel paket s potvrzovacim cislem, ktere je uplne mimo.",
                )
            else:
                # resetting attempts
                attempts = 0

                if ack_number < sequence_number:
                    transferred += (ack_number - sequence_number) + 2 ** 16
                else:
                    transferred += ack_number - sequence_number

                sequence_number = ack_number

                # popping ack'ed (and lower numbers) packets
                window_queue = window_queue[index:]

                # fill window_queue with next chunks
                for chunk_index in range(
                    window_queue[-1][0] + PACKET_MAX_DATA_SIZE,
                    window_queue[-1][0] + (index + 1) * PACKET_MAX_DATA_SIZE,
                    PACKET_MAX_DATA_SIZE,
                ):
                    chunk = firmware.read(PACKET_MAX_DATA_SIZE)
                    if chunk == b"":
                        break

                    window_queue.append((chunk_index % 65536, chunk))
    else:
        log_message(
            connection_id,
            "EXCEPTION #8: Dosazen max. pocet odeslani paketu "
            "se stejnym sekvencnim cislem.",
        )

    close_connection(sock, connection_id, sequence_number, 0)

    if transferred == firmware_size:
        log_message(
            connection_id,
            "USPECH: Spojeni bylo uzavreno. "
            f"Bylo preneseno celkem {transferred} bytu.",
        )
    else:
        log_message(
            connection_id,
            "EXCEPTION #30: Delka firmwaru neodpovida - "
            "firmware byl pri prenosu poskozen.",
        )


def download_photo(sock: socket.socket) -> None:
    """
    Handling download of the photo from probe near Mars.
    """

    ack_number = 0

    image = bytearray()

    # caching
    wrongly_order_packets: Dict[int, bytes] = {}

    # id we'll be use to communicate with server,
    # will be received from server (not-zero id)
    errors_occured, connection_id = establish_connection(
        sock=sock, operation=DOWNLOAD_PHOTO
    )

    if errors_occured:
        # yay! recursion (or goto 🤔)
        download_photo(sock)

    while True:

        send_and_log(
            sock=sock,
            connection_id=connection_id,
            sequence_number=0,
            ack_number=ack_number,
            flags=NO_FLAGS,
            data=b"",
        )

        try:
            (
                connection_id_new,
                sequence_number,
                ack_number_new,
                flags,
                data,
            ) = recv_and_log(sock)
        except socket.timeout:
            continue

        # not for us
        if connection_id_new != connection_id:
            continue

        if flags == FIN:
            close_connection(
                sock=sock,
                connection_id=connection_id,
                sequence_number=0,
                ack_number=sequence_number,
            )
            break

        # server should send any flags with data or send ack_number != 0,
        # it only uses sequence_number when uploading, and so on client ->
        # only uses ack_number when downloading
        if flags != NO_FLAGS or ack_number_new != 0:
            # shouldn't be here
            send_and_log(
                sock=sock,
                connection_id=connection_id,
                sequence_number=0,
                ack_number=0,
                flags=RST,
                data=b"",
            )
            errors_occured = True
            break

        if sequence_number == ack_number:
            image += data
            ack_number = len(image) % 65536

            # using cache, if presented
            while wrongly_order_packets.get(ack_number):
                image += wrongly_order_packets.pop(ack_number)
                ack_number = len(image) % 65536

        else:
            if wrongly_order_packets.get(sequence_number):
                # already have that package, so duplicating
                if wrongly_order_packets[sequence_number] == data:
                    log_message(
                        connection_id,
                        "Tento paket se mi nehodi do rady, navic "
                        f"jsem ho jiz jednou prijal: seq={sequence_number}",
                    )
                else:
                    # according to the reference client implementation,
                    # when one received a packet X with some data, and then
                    # "same" packet X arrived with another contents ->
                    # that should be an error.
                    log_message(
                        connection_id,
                        "EXCEPTION #23: Predchozi paket se stejnym sekvencnim "
                        "cislem obsahoval jina data.",
                    )
                    send_and_log(
                        sock=sock,
                        connection_id=connection_id,
                        sequence_number=0,
                        ack_number=0,
                        flags=RST,
                        data=b"",
                    )
                    errors_occured = True
                    break
            else:
                # very new packet, not relevant right now,
                # so cache it for the future
                wrongly_order_packets[sequence_number] = data
                log_message(
                    connection_id,
                    "Tento paket se mi nehodi do rady, "
                    f"ale budu si ho pamatovat: seq={sequence_number}",
                )

    if not errors_occured:
        log_message(
            connection_id,
            f"Spojeni bylo uzavreno. Bylo preneseno celkem {len(image)} bytu.",
        )

        # can save image to FS in case of need

        # import uuid
        # name = f"photo-{uuid.uuid4()}.png"

        # with open(name, "wb") as f:
        #     f.write(image)
        # print(f"Image is written to {name}")


def main() -> None:
    """
    Parses CLI args and launches specific function of UDP client
    (either downloading or uploading).
    """
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    arg_parser.add_argument(
        "address",
        nargs=1,
        # getaddrinfo deals with domain names translation (for e.g. translates
        # 'localhost' to '127.0.0.1') if needed, leaves ip addresses alone.
        type=lambda addr: ipaddress.IPv4Address(socket.gethostbyname(addr)),
        metavar="address",  # to rewrite <lambda> in shown help
        default="127.0.0.1",
        help="Server address (string, default='localhost') - "
        "IPv4 address or domain name (will be translated)",
    )

    arg_parser.add_argument(
        "firmware",
        metavar="firmware.bin",
        nargs="?",  # none or one
        type=argparse.FileType("rb"),
        help="Binary firmware file to upload to the server.",
    )

    args = arg_parser.parse_args()

    # creating socket IPv4 UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # connecting to the server (in order not to use sendto(),
    # but just send(), as address is always the same)
    sock.connect((str(args.address[0]), SERVER_PORT))

    # timeout according to the task
    sock.settimeout(TIMEOUT)

    if args.firmware:
        upload_firmware(sock, args.firmware)
        # cleanup
        args.firmware.close()
    else:
        download_photo(sock)

    # cleanup
    sock.close()


if __name__ == "__main__":
    main()
