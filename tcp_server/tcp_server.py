#!/bin/env python3
"""
Concurrent (asynchronous) server for TCP/IP communication
(with custom protocol) for "controlling remote robots".

Author: Dmytro Osaulenko, homework for BI-PSI (Computer Networks) @ FIT CTU
Date: 29.4.2020
Requires: python >= 3.7
Tested on (100% of tests passed): python 3.8.2
"""
from typing import AsyncIterator, Iterator, Tuple

import argparse
import asyncio
import enum
import logging
import re
import socket


# Different task constants (for robot(s) and server)
MOD_16BIT = 65536  # 2**16
CLIENT_KEY = 45328
SERVER_KEY = 54621

SERVER_MOVE = b"102 MOVE\a\b"
SERVER_TURN_LEFT = b"103 TURN LEFT\a\b"
SERVER_TURN_RIGHT = b"104 TURN RIGHT\a\b"
SERVER_PICK_UP = b"105 GET MESSAGE\a\b"
SERVER_LOGOUT = b"106 LOGOUT\a\b"
SERVER_OK = b"200 OK\a\b"
SERVER_LOGIN_FAILED = b"300 LOGIN FAILED\a\b"
SERVER_SYNTAX_ERROR = b"301 SYNTAX ERROR\a\b"
SERVER_LOGIC_ERROR = b"302 LOGIC ERROR\a\b"
CLIENT_RECHARGING = b"RECHARGING\a\b"
CLIENT_FULL_POWER = b"FULL POWER\a\b"
TIMEOUT = 1
TIMEOUT_RECHARGING = 5

# just an alias for convenience and clarity
Position = Tuple[int, int]


class Direction(enum.Enum):
    """
    Enum helper (instead of constants using) for direction manipulation.
    """

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


class SocketWrapper:
    """
    An aux wrapper aroung asynchronous sockets.
    Handles segmentation (segments of one message sent with small intervals,
    like 0.1 sec), multiple messages sent once (does caching, so
    for SocketWrapper's user it looks like independently received messages).
    """

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.loop = asyncio.get_event_loop()
        self.cache = bytearray()

    def close_socket(self) -> None:
        """
        Closes the socket.
        """
        self.sock.close()
        logging.debug("Closed client socket.")

    async def send(self, data: bytes) -> None:
        """
        Asynchronously (tries to) send data and log what was sent.
        """
        try:
            await self.loop.sock_sendall(self.sock, data)
            logging.debug("Sent: %s", data)

        # if socket was closed earlier (synchronous operation), than data sent
        except BrokenPipeError:
            logging.debug("Didn't send. Socket was closed.")

    async def _recv(self, timeout: int, max_len: int) -> None:
        """
        Does recv() on socket and caching extra data
        (not mandatory needed when it's called, but needed in the future).

        :raises asyncio.TimeoutError: if timeout on recv is exceeded
        :raises RuntimeError: on bad logic or bad syntax of incoming data
        """
        # for particular session recv, than to be concatenated to self.cache
        data = bytearray()

        while data.count(b"\a\b") == 0:

            tmp = await asyncio.wait_for(
                self.loop.sock_recv(self.sock, 100), timeout
            )

            data += tmp

            if tmp == b"" or len(data) >= max_len:
                break

            if len(data) > max_len and data.count(b"\a\b") == 0:
                logging.debug("Maximum message size (%d) reached.", max_len)
                await self.send(SERVER_SYNTAX_ERROR)
                raise RuntimeError  # to close socket

        self.cache += data
        logging.debug("Received: %s", bytes(data))

    async def recv(self, timeout: int = TIMEOUT, max_len: int = 12) -> bytes:
        """
        Returns data from cache or receives new from robot.

        :param int timeout: timeout during which to maintain
            a connection with robot
        :param int max_len: maximum length of the message to return
        :return: data received from robot (or from cache, received earlier)
        :rtype: bytes
        :raises asyncio.TimeoutError: if timeout on recv is exceeded
        :raises RuntimeError: on bad logic or bad syntax of incoming data
        """
        # have no cache (it's empty)
        # or it's has no complete data (does not end with \a\b sequence)
        if self.cache.count(b"\a\b") == 0:
            await self._recv(timeout, max_len)

        # otherwise had some accumulated messages (like 2 in one recv)
        # or simply waited for next

        # find first sequence of \a\b
        # (+2 because it finds where is starts, but we need it with \a\b)
        message_end_index = self.cache.find(b"\a\b") + 2

        # save this message for user and return it later
        data = self.cache[:message_end_index]

        # remove it from cache
        del self.cache[:message_end_index]

        if data == CLIENT_RECHARGING:
            # wait for FULL_POWER
            # little recursion
            if await self.recv(TIMEOUT_RECHARGING, 12) != CLIENT_FULL_POWER:
                await self.send(SERVER_LOGIC_ERROR)
                raise RuntimeError  # to close socket

            # little recursion again
            return await self.recv(max_len=max_len)

        if (
            message_end_index > max_len
            or message_end_index == 1
            or not data.endswith(b"\a\b")
        ):
            logging.debug("Packet is corrupted")
            await self.send(SERVER_SYNTAX_ERROR)
            raise RuntimeError  # to close socket

        # for consistency (bytearray would be also fine)
        return bytes(data)


def parse_position(robot_response: bytes) -> Position:
    """
    :param bytes robot_response: bytes representation of robots response,
    which should be OK with 2 integers and \a\b end sequence.
    :return: position (tuple of 2 coordinates - x and y) parsed from bytes
    :rtype: Position

    :raises AttributeError: on wrong format (regex didn't match with data)
    :raises ValueError: on wrong format (expect 2 valid integers after OK)
    """

    # type ignore is used to supress mypy's warning about optional match
    # `Item "None" of "Optional[Match[bytes]]" has no attribute "groups"`
    # It is INTENTIONAL if function will raise exception -> there is something
    # wrong in communication, functions that call parse_position()
    # will handle it.
    bytes_x, bytes_y = re.match(  # type: ignore
        # \b in Python regex is a word, so using hex
        rb"OK (-?\d+) (-?\d+)\x07\x08",
        robot_response,
    ).groups()

    return int(bytes_x), int(bytes_y)


async def initial_position_and_direction(
    socket_wrapper: SocketWrapper,
) -> Tuple[Position, Direction]:
    """
    Sends TURN_LEFT (to get position) and TURN_RIGHT (to fix initial
    direction), then MOVE to understand which direction has robot.
    Returns position (not initial, but first next position) and direction.

    :param SocketWrapper socket_wrapper: again shared context
    :return: guessed position and direction of the robot
    :rtype: Tuple[Position, Direction]

    :raises asyncio.TimeoutError: if timeout on recv is exceeded
    :raises RuntimeError: on wrong format of data received from robot
    """
    # first TURN_LEFT to get location
    await socket_wrapper.send(SERVER_TURN_LEFT)
    data = await socket_wrapper.recv()

    try:
        initial_position = parse_position(data)
    except (AttributeError, ValueError):
        await socket_wrapper.send(SERVER_SYNTAX_ERROR)
        raise RuntimeError  # to close socket

    # TURN_RIGHT to save initial direction
    await socket_wrapper.send(SERVER_TURN_RIGHT)

    # just to flush cache in socket_wrapper
    await socket_wrapper.recv()

    new_position = initial_position

    while new_position == initial_position:
        # move to get direction
        await socket_wrapper.send(SERVER_MOVE)
        data = await socket_wrapper.recv()
        try:
            new_position = parse_position(data)
        except (AttributeError, ValueError):
            await socket_wrapper.send(SERVER_SYNTAX_ERROR)
            raise RuntimeError  # to close socket

    # check X
    if new_position[0] - initial_position[0] > 0:
        direction = Direction.RIGHT
    elif new_position[0] - initial_position[0] < 0:
        direction = Direction.LEFT
    # check Y
    elif new_position[1] - initial_position[1] > 0:
        direction = Direction.UP
    elif new_position[1] - initial_position[1] < 0:
        direction = Direction.DOWN

    return new_position, direction


async def login(socket_wrapper: SocketWrapper) -> None:
    """
    Gets shared context (socket_wrapper), tries to authenticate robot.
    """
    data = await socket_wrapper.recv()
    robot_username_hash = (sum(data.replace(b"\a\b", b"")) * 1000) % MOD_16BIT

    await socket_wrapper.send(
        str((robot_username_hash + SERVER_KEY) % MOD_16BIT).encode() + b"\a\b"
    )

    client_confirmation = await socket_wrapper.recv(max_len=7)

    if not client_confirmation[:-2].isdigit():
        logging.debug(
            "Client_confirmation contains something else than digits."
        )
        await socket_wrapper.send(SERVER_SYNTAX_ERROR)
        raise RuntimeError  # to close socket

    # compare hash computed by robot
    if (
        str((robot_username_hash + CLIENT_KEY) % MOD_16BIT).encode() + b"\a\b"
        == client_confirmation
    ):

        await socket_wrapper.send(SERVER_OK)
    else:
        await socket_wrapper.send(SERVER_LOGIN_FAILED)
        raise RuntimeError


def nearest(choices: Tuple[Position, ...], target: Position) -> Position:
    """
    Pure logic/math thing. Gets an iterable of Position (choices)
    and target position, finds and returns one of choices,
    which has minimum distance with target.

    :param Tuple[Position, ...] choices:
    :param Position target:
    :return: nearest position (from choices) to target
    :rtype: Position
    """
    return choices[
        min(
            enumerate(
                (
                    abs(choices[0][0] - target[0])
                    + abs(choices[0][1] - target[1]),
                    abs(choices[1][0] - target[0])
                    + abs(choices[1][1] - target[1]),
                    abs(choices[2][0] - target[0])
                    + abs(choices[2][1] - target[1]),
                    abs(choices[3][0] - target[0])
                    + abs(choices[3][1] - target[1]),
                )
            ),
            # enumerate indexes pairs,
            # so find minimum by tuple's second item (actual data, not index)
            key=lambda x: x[1],
        )[0]
        # but get its index in order to actually return the data
    ]


def get_move(  # pylint: disable=invalid-name
    # pylint suppressing for x and y
    x: int,
    y: int,
) -> Iterator[Position]:
    """
    Returns to which position should robot move.
    From initial position to the nearest corner of the zone
    and then traversing the 5x5 zone.
    Pure logic thing with no sockets interaction. To be used by next_move()

    :return: a generator (only iterator implemented) of position (2xint tuple).
    :rtype: Iterator[Position]
    """
    if (abs(x), abs(y)) != (2, 2):

        # choose the nearest corner to move to
        corner = nearest(((-2, -2), (-2, 2), (2, -2), (2, 2)), (x, y))

        # move from position to desired corner
        while (x, y) != corner:
            x, y = nearest(
                ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)), corner
            )
            yield x, y

    # spiral-like traversion of the 5x5 zone
    # (from top to bottom, from side to side and vice-versa)
    start_y, end_y = y, -y
    for i in range(x, -x + (-x // 2), -x // 2):
        for j in range(start_y, end_y + (end_y // 2), end_y // 2):
            yield i, j
        start_y, end_y = end_y, start_y


async def next_move(
    position: Position, direction: Direction, socket_wrapper: SocketWrapper
) -> AsyncIterator[Position]:
    """
    AsyncIterator which gets position, direction and shared socket wrapper,
    starts get_move() iterator, from which takes which next position
    to send robot to, handles communication with sockets (moves and turnings),
    yields visited position to be checked for a hidden message.

    :param Position position: first position after login and
        guessing where robot is located
    :param Direction direction:
    :param SocketWrapper socket_wrapper: shared socket wrapper

    :return: yields visited positions to be checked for a hidden message
    :rtype: AsyncIterator[Position]

    :raises asyncio.TimeoutError: if timeout on recv is exceeded
    :raises RuntimeError: on wrong format of data received from robot
    """
    # cache visited positions
    visited = set()

    for new_position in get_move(*position):

        # prevents second SERVER_PICK_UP on already visited position
        if position not in visited:
            visited.add(position)
            yield position

        # determine which direction should it be
        if new_position == (position[0] - 1, position[1]):
            desired_direction = Direction.LEFT
        elif new_position == (position[0] + 1, position[1]):
            desired_direction = Direction.RIGHT
        elif new_position == (position[0], position[1] + 1):
            desired_direction = Direction.UP
        else:
            desired_direction = Direction.DOWN

        # turn right until the direction is correct
        # could be optimised (1 x SERVER_TURN_LEFT instead of
        # 3 x SERVER_TURN_RIGHT for example), but not needed in particular task
        while direction != desired_direction:
            await socket_wrapper.send(SERVER_TURN_RIGHT)
            await socket_wrapper.recv()
            direction = Direction((direction.value + 1) % 4)

        # robot can "ignore" SERVER_MOVE and remain on the same position
        # (the age of robot or whatever), so while loop is used
        while position != new_position:
            await socket_wrapper.send(SERVER_MOVE)
            data = await socket_wrapper.recv()
            try:
                position = parse_position(data)
            except (AttributeError, ValueError):
                await socket_wrapper.send(SERVER_SYNTAX_ERROR)
                raise RuntimeError  # to close socket

    # last yield, because it wouldn't be yielded
    # otherwise after loop's StopIteration
    yield position


async def manage_robot(socket_wrapper: SocketWrapper) -> None:
    """
    Does authenticating, manipulating robot and searching for cached message.
    Closes socket on exceeded timeout, logic error
    or successful find of the message.

    :param SocketWrapper socket_wrapper: a wrapper around client socket
    for the ease of manipulation
    :rtype: None
    """
    try:
        await login(socket_wrapper)

        data = await initial_position_and_direction(socket_wrapper)
        async for move in next_move(*data, socket_wrapper):

            # particular section (if scope) could be as well implemented in
            # next_move(), but was intentionally implemented here
            if abs(move[0]) <= 2 and abs(move[1]) <= 2:

                await socket_wrapper.send(SERVER_PICK_UP)
                message = await socket_wrapper.recv(max_len=100)

                if message not in (b"", b"\a\b"):
                    logging.info("Found message: %s", message.decode())
                    await socket_wrapper.send(SERVER_LOGOUT)
                    break

    except asyncio.TimeoutError:
        logging.debug("Timeout has exceeded.")
    except RuntimeError:
        logging.debug("Logic expects closing the client socket.")
    finally:
        socket_wrapper.close_socket()


async def main(addr: str, port: int) -> None:
    """
    Dispatcher of the server.
    Accepts incoming connections and assigns concurrent handles for them.

    :param str addr: physical address to bind
    :param int port: server's port to bind
    :rtype: None
    """
    loop = asyncio.get_event_loop()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # make it reusable (prevent waiting after program restart)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((addr, port))
    logging.info("Server started on %s:%d", addr, port)

    sock.listen()
    sock.setblocking(False)

    with sock:
        while True:
            client_socket, client_addr_info = await loop.sock_accept(sock)
            logging.debug("Accepted request from: %s", client_addr_info)
            loop.create_task(manage_robot(SocketWrapper(client_socket)))


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(
        description=__doc__,
        # Dynamically created class based from 3 default formatters.
        # Unfortunately there is no default class with all these features,
        # so metaclass thing was used.
        # ---
        # first formatter fixes whitespaces when dealing with __doc__,
        # so it can be shown when -h/--help hit as you can see it in the code.
        # second formatter fixes showing default values for arguments.
        # third formatter fixes showing argument values types.
        formatter_class=type(
            "",
            (
                argparse.RawDescriptionHelpFormatter,
                argparse.ArgumentDefaultsHelpFormatter,
                argparse.MetavarTypeHelpFormatter,
            ),
            {},
        ),
        allow_abbrev=False,  # disallow abbreviations, be explicit!
    )

    PARSER.add_argument(
        "-p", "--port", default=8080, type=int, help="Server port.",
    )

    PARSER.add_argument(
        "-a", "--addr", default="127.0.0.1", type=str, help="Server address.",
    )

    PARSER.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="Show logging output.",
    )

    ARGS = PARSER.parse_args()

    if ARGS.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s] %(levelname)6s: %(message)s",
        )

    try:
        asyncio.run(main(ARGS.addr, ARGS.port))
    except KeyboardInterrupt:
        logging.info("Server stopped")
