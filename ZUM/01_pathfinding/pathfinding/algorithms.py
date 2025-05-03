"""
Module with different known algorithms for searching shortest path
implemented: BFS, DFS, Random Search, Dijkstra, Greedy, A*

Some implementations are very similar and only differ by few lines of code,
so DRY principle is not kept, it's intentional for study purposes.
"""
from typing import Deque, Tuple, List, Set, Dict, DefaultDict

import collections
import heapq
import random

from pathfinding import utils
from pathfinding.types import CursesIterator, Maze, Position


def bfs(maze: Maze) -> CursesIterator:

    # deque to be used as queue
    opened: Deque[Position] = collections.deque()
    opened.appendleft(maze.start)

    closed: Set[Position] = set()
    path: Dict[Position, Position] = {}

    yield maze.end, "E"

    while opened:
        current_move = opened.pop()

        if current_move == maze.end:
            break

        yield current_move, "#" if current_move != maze.start else "S"

        for move in utils.valid_moves(maze, current_move):
            if move not in opened and move not in closed:
                opened.appendleft(move)
                path[move] = current_move

        closed.add(current_move)

    if current_move != maze.end:
        raise utils.BadMazeFormatException(
            "There is no path from Start to End"
        )

    for move in reversed(utils.reconstruct_path(path, maze.end)):
        yield move, "@"


def dfs(maze: Maze) -> CursesIterator:

    # deque to be used as stack (append as push and pop as pop)
    opened: Deque[Position] = collections.deque()
    opened.append(maze.start)

    closed: Set[Position] = set()
    path: Dict[Position, Position] = {}

    yield maze.end, "E"

    while opened:
        current_move = opened.pop()

        if current_move == maze.end:
            break

        yield current_move, "#" if current_move != maze.start else "S"

        for move in utils.valid_moves(maze, current_move):
            if move not in opened and move not in closed:
                opened.append(move)
                path[move] = current_move

        closed.add(current_move)

    if current_move != maze.end:
        raise utils.BadMazeFormatException(
            "There is no path from Start to End"
        )

    for move in reversed(utils.reconstruct_path(path, maze.end)):
        yield move, "@"


def random_search(maze: Maze) -> CursesIterator:

    # set provides the fastest removal of random element
    # (comparing to list or collections.deque)
    opened: Set[Position] = set()
    opened.add(maze.start)

    closed: Set[Position] = set()
    path: Dict[Position, Position] = {}

    yield maze.end, "E"

    while opened:

        # though set() cannot be an argument to random.choice,
        # so needed to be copied (by reference, not by value) to tuple or list,
        # or random.sample(opened, 1)[0] should be used (but is slower)
        current_move = random.choice(tuple(opened))
        # pop random element
        opened.remove(current_move)

        if current_move == maze.end:
            break

        yield current_move, "#" if current_move != maze.start else "S"

        for move in utils.valid_moves(maze, current_move):
            if move not in opened and move not in closed:
                opened.add(move)
                path[move] = current_move

        closed.add(current_move)

    if current_move != maze.end:
        raise utils.BadMazeFormatException(
            "There is no path from Start to End"
        )

    for move in reversed(utils.reconstruct_path(path, maze.end)):
        yield move, "@"


def dijkstra(maze: Maze) -> CursesIterator:

    # using priority queue (standard list + heapq standard lib)
    # element is a tuple of 2 elements
    # (float distance/priority and position tuple);
    # heapq algorithm only works with list
    opened: List[Tuple[float, Position]] = []
    heapq.heappush(opened, (0, maze.start))

    # saving distances
    dist: DefaultDict[Position, float] = collections.defaultdict(
        lambda: float("inf")
    )

    dist[maze.start] = 0.0

    # saving path
    path: Dict[Position, Position] = {}

    yield maze.end, "E"

    while opened:
        # "drop" distance/priority, just use coordinates
        current_move = heapq.heappop(opened)[1]

        if current_move == maze.end:
            break

        yield current_move, "#" if current_move != maze.start else "S"

        for next_move in utils.valid_moves(maze, current_move):

            # as there are no weights in graph, particular implementation
            # only works with abs(1) price for every path,
            # so it may act very similar to BFS

            # check if move is in the priority queue;
            # generator is used instead of list comprehension
            # because of memory optimalization and speed
            if next_move not in (move for _, move in opened):

                distance = dist[current_move] + utils.euclidean_distance(
                    current_move, next_move
                )

                if distance < dist[next_move]:
                    dist[next_move] = distance
                    path[next_move] = current_move
                    heapq.heappush(opened, (distance, next_move))

    if current_move != maze.end:
        raise utils.BadMazeFormatException(
            "There is no path from Start to End"
        )

    for move in reversed(utils.reconstruct_path(path, maze.end)):
        yield move, "@"


def greedy(maze: Maze) -> CursesIterator:

    # using priority queue (standard list + heapq standard lib)
    # element is a tuple of 2 elements
    # (float distance/priority and position tuple);
    # heapq algorithm only works with list
    opened: List[Tuple[float, Position]] = []
    heapq.heappush(
        opened, (utils.euclidean_distance(maze.start, maze.end), maze.start)
    )

    closed: Set[Position] = set()

    # saving path from S to E
    path: Dict[Position, Position] = {}

    yield maze.end, "E"

    while opened:
        # "drop" distance/priority, just use coordinates
        current_move = heapq.heappop(opened)[1]

        if current_move == maze.end:
            break

        yield current_move, "#" if current_move != maze.start else "S"

        for move in utils.valid_moves(maze, current_move):
            # check if move is in the priority queue;
            # generator is used instead of list comprehension
            # because of memory optimalization and speed
            if move not in (move for _, move in opened) and move not in closed:
                heapq.heappush(
                    opened, (utils.euclidean_distance(move, maze.end), move)
                )
                path[move] = current_move

        closed.add(current_move)

    if current_move != maze.end:
        raise utils.BadMazeFormatException(
            "There is no path from Start to End"
        )

    for move in reversed(utils.reconstruct_path(path, maze.end)):
        yield move, "@"


def a_star(maze: Maze) -> CursesIterator:

    # using priority queue (standard list + heapq standard lib)
    # element is a tuple of 2 elements
    # (float distance/priority and position tuple);
    # heapq algorithm only works with list
    opened: List[Tuple[float, Position]] = []
    heapq.heappush(opened, (0, maze.start))

    # saving dist
    dist: DefaultDict[Position, float] = collections.defaultdict(
        lambda: float("inf")
    )

    dist[maze.start] = 0.0

    # saving path
    path: Dict[Position, Position] = {}

    closed: Set[Position] = set()

    yield maze.end, "E"

    while opened:
        # "drop" distance/priority, just use coordinates
        current_move = heapq.heappop(opened)[1]

        if current_move == maze.end:
            break

        yield current_move, "#" if current_move != maze.start else "S"

        for next_move in utils.valid_moves(maze, current_move):

            # as there are no weights in graph, particular implementation
            # only works with +1 price for every path

            # check if move is in the priority queue;
            # generator is used instead of list comprehension
            # because of memory optimalization and speed
            if (
                next_move not in (move for _, move in opened)
                and next_move not in closed
            ):

                # distance (Dijkstra)
                distance = dist[current_move] + utils.euclidean_distance(
                    current_move, next_move
                )

                # heuristics (greedy search)
                heuristics = utils.euclidean_distance(next_move, maze.end)

                if distance < dist[next_move]:
                    dist[next_move] = distance
                    path[next_move] = current_move
                    # pushing the sum of distance +
                    # heuristics (distance to the end in particular case),
                    # so it will always find the shortest path
                    # and will be more intelligent, than Dijkstra
                    heapq.heappush(opened, (distance + heuristics, next_move))

        closed.add(current_move)

    if current_move != maze.end:
        raise utils.BadMazeFormatException(
            "There is no path from Start to End"
        )

    for move in reversed(utils.reconstruct_path(path, maze.end)):
        yield move, "@"
