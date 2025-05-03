from typing import Any, Callable

import curses
import time

from pathfinding.types import CursesIterator, Maze
from pathfinding.utils import BadMazeFormatException


COLORS = {"S": 2, "E": 2, "#": 3, "@": 2}


def show_stats(
    console: Any,
    maze_len: int,
    nodes_expanded: int,
    path_len: int,
    fits: bool = True,
) -> None:

    normal_y = curses.LINES // 2 + maze_len // 2
    normal_x = curses.COLS // 2 - 15

    try:
        # try to print a message 2 lines above the maze
        # if will fail -> print it in the middle of the screen
        console.addstr(
            normal_y - maze_len - 2 if fits else 0,
            normal_x if fits else 0,
            "Press any key to continue.",
            curses.color_pair(2) | curses.A_BOLD,
        )

        # stats will be printed below the maze,
        # if it won't fit the screen,
        # will be printed in the center (rewriting already printed).
        # a fix for very big mazes that won't fit the terminal
        # even after maximum possible resize
        console.addstr(
            normal_y + 2 if fits else 2,
            normal_x if fits else 0,
            "S Start        E End",
        )

        console.addstr(
            normal_y + 3 if fits else 3,
            normal_x if fits else 0,
            "# Opened node  space Fresh node",
        )

        console.addstr(
            normal_y + 4 if fits else 4,
            normal_x if fits else 0,
            "@ Path         X Wall",
        )

        console.addstr(
            normal_y + 5 if fits else 5, normal_x if fits else 0, "-" * 35
        )

        console.addstr(
            normal_y + 6 if fits else 6,
            normal_x if fits else 0,
            f"Nodes expanded: {nodes_expanded}",
        )

        console.addstr(
            normal_y + 7 if fits else 7,
            normal_x if fits else 0,
            f"Path length: {path_len}",
        )

    except curses.error:
        # little recursion (only second try)
        if fits:
            show_stats(console, maze_len, nodes_expanded, path_len, fits=False)


def draw(
    console: Any,
    maze: Maze,
    algorithm: Callable[[Maze], CursesIterator],
    speed: float,
) -> None:

    # hide cursor
    curses.curs_set(0)

    # set up colors
    curses.start_color()
    curses.use_default_colors()

    for color in range(0, curses.COLORS):
        curses.init_pair(color + 1, color, -1)

    # draw maze
    for index, line in enumerate(reversed(maze.maze)):
        try:
            console.addstr(
                curses.LINES // 2 + maze.length // 2 - index,
                curses.COLS // 2 - maze.width // 2,
                line,
            )
        except curses.error:
            # curses cannot write some line
            # (not enough cols or lines, so screen should be resized)
            pass

    console.refresh()

    # set offset for even/odd length of maze
    offset = 1 if maze.length % 2 == 0 else 0

    # for showing stats at the end of animation
    path_len = 0
    nodes_expanded = 0

    try:
        for move, symbol in algorithm(maze):
            try:
                if symbol == "#":
                    nodes_expanded += 1
                elif symbol in ("@", "E"):
                    path_len += 1

                console.addstr(
                    curses.LINES // 2 - maze.length // 2 + move[1] + offset,
                    curses.COLS // 2 - maze.width // 2 + move[0],
                    symbol,
                    curses.color_pair(COLORS.get(symbol, 1)),
                )
                console.refresh()
            except curses.error:
                # curses cannot write some line
                # (not enough cols or lines, so screen should be resized)
                pass

            # slowing animation
            time.sleep(0.025 * speed)

    except BadMazeFormatException:
        # raised by algorithm function, when algorithm didn't find any path
        # from start to end
        console.addstr(
            curses.LINES // 2 + maze.length // 2 + 2,
            curses.COLS // 2 - 31,  # 31 is len(message) // 2
            "There is no path from start to end. Press any key to continue.",
            curses.color_pair(2) | curses.A_BOLD,
        )
        console.getch()
        return

    # rewrite with single @ if S == E
    if maze.start == maze.end:
        console.addstr(
            curses.LINES // 2 - maze.length // 2 + maze.end[1] + offset,
            curses.COLS // 2 - maze.width // 2 + maze.end[0],
            "@",
            curses.color_pair(2) | curses.A_BOLD,
        )

    show_stats(console, maze.length, nodes_expanded, path_len)
    # wait for the first key pressed, then end program
    console.getch()
