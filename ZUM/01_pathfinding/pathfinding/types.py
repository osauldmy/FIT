from typing import Tuple, Iterator

import dataclasses


Position = Tuple[int, int]

# each algorithm implementation is a generator function,
# which yields a tuple of Position and char (str) for animation reasons
CursesIterator = Iterator[Tuple[Position, str]]


@dataclasses.dataclass(frozen=True)
class Maze:
    """
    Representation of a maze with actual tuple of strings
    (can be accessed with x and y Cartesian coordinates
    like my_maze.maze[y][x]), start and end Cartesian coordinates.
    """

    width: int
    length: int
    maze: Tuple[str, ...]
    start: Position
    end: Position
