"""
A module with aux functions for validating maze, algorithmic/logic questions.

To be used with multiple different path searching algorithms
like BFS, DFS, Random search, Dijkstra, Greedy, A* etc.
"""
from typing import List, Tuple, Dict

import math
import textwrap

from pathfinding.types import Maze, Position


def valid_moves(
    maze: Maze, position: Position
) -> Tuple[Position, ...]:
    """
    An aux function for different algorithms
    to check valid moves from particular position.
    """
    x, y = position
    moves: List[Position] = []

    # forward
    if 0 < y - 1 < maze.length - 1 and maze.maze[y - 1][x] != "X":
        moves.append((x, y - 1))

    # backward
    if 0 < y + 1 < maze.length - 1 and maze.maze[y + 1][x] != "X":
        moves.append((x, y + 1))

    # left
    if 0 < x - 1 < maze.width - 1 and maze.maze[y][x - 1] != "X":
        moves.append((x - 1, y))

    # right
    if 0 < x + 1 < maze.width - 1 and maze.maze[y][x + 1] != "X":
        moves.append((x + 1, y))

    return tuple(moves)


def euclidean_distance(start: Position, end: Position) -> float:
    """Calculate and return Euclidean distance between two positions."""
    return math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)


def reconstruct_path(
    prev: Dict[Position, Position], end: Position
) -> List[Position]:
    """
    Gets a dictionary with ancestors for positions and end position,
    so path from end to start can be reconstructed.
    """
    path: List[Position] = []

    x = end

    if not prev:
        return []

    while x:
        path.append(x)
        try:
            x = prev[x]
        except KeyError:
            break

    # pop start and end
    path.pop()
    path.pop(0)

    return path


class BadMazeFormatException(ValueError):
    """
    Used for validation of maze file.
    """


def validate_maze(raw_maze: List[str]) -> Maze:
    """
    Gets a list of strings representing maze,
    validates format and returns maze object instance.

    :param typing.List[str] raw_maze: a list of strings representing maze
    :return: a Maze instance if validation succeeds
    :rtype: types.Maze
    :raises BadMazeFormatException: on wrong maze format
    """
    raw_maze = [line.strip() for line in raw_maze]

    last_2_lines_format = textwrap.dedent(
        """
        Check maze format!
        Last but one line should be in format "start X, Y",
        last line should be in format "end X, Y"!
        X and Y must be integers!
        """
    ).rstrip()

    maze_format = textwrap.dedent(
        """
        Minimal required format of maze is
                      XXX
                      X X
                      XXX
        Walls should consist of capital X letter.
        Maze should have walls at least as borders (rectangle).
        Holes in borders are not allowed.
        """
    ).rstrip()

    try:
        # format: "start X, Y"
        # remove "start" and cast X and Y to ints
        raw_maze[-2] = raw_maze[-2].replace("start", "")
        start_x = int(raw_maze[-2].split(",")[0])
        start_y = int(raw_maze[-2].split(",")[1])

        # format: "end X, Y"
        # remove "end" and cast X and Y to ints
        raw_maze[-1] = raw_maze[-1].replace("end", "")
        end_x = int(raw_maze[-1].split(",")[0])
        end_y = int(raw_maze[-1].split(",")[1])
    except (IndexError, ValueError) as error:
        raise BadMazeFormatException(last_2_lines_format) from error

    # getting rid of already parsed and validated last 2 lines (start & end)
    raw_maze = raw_maze[:-2]

    # "assert'ing" borders: are present, consist of 'X' and have no holes
    # so minimal requirement is rectangle created from 'X' symbols

    # horizontal borders
    if set(raw_maze[0]) != {"X"} or set(raw_maze[-1]) != {"X"}:
        raise BadMazeFormatException(maze_format)

    # vertical borders
    if {line[0] == "X" and line[-1] == "X" for line in raw_maze} != {True}:
        raise BadMazeFormatException(maze_format)

    # checking "start" and "end" coordinates are inside of maze
    if start_x >= len(raw_maze[0]) or start_y >= len(raw_maze):
        raise BadMazeFormatException("Start coordinate is out of the maze")

    if end_x >= len(raw_maze[0]) or end_y >= len(raw_maze):
        raise BadMazeFormatException("End coordinate is out of the maze")

    return Maze(
        len(raw_maze[0]),
        len(raw_maze),
        tuple(raw_maze),
        (start_x, start_y),
        (end_x, end_y),
    )
