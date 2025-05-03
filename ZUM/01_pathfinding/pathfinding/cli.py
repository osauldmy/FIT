"""
Interactive CLI ncurses program dedicated to (shortest) path finding problem
with known and popular algorithms (BFS, DFS, Random Search, Dijkstra,
Greedy Search, A*): some are better, some are not,
but are implemented for study purposes.

Author: Dmytro Osaulenko, homework for BI-ZUM (Elements of AI) @ FIT CTU
Date: 1.5.2020
Requires: python >= 3.7


Run example:
   python -m pathfinding --algorithm 'A*' --speed 1 dataset/100.txt
"""

import argparse
import curses

from pathfinding import algorithms
from pathfinding.ui import draw
from pathfinding.utils import validate_maze


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-a",
        "--algorithm",
        required=True,
        choices=("BFS", "DFS", "Random", "Dijkstra", "Greedy", "A*"),
        help="(Shortest) path search algorithm to be used",
    )

    parser.add_argument(
        "-s",
        "--speed",
        required=False,
        type=float,
        default=1,
        help="Slowing/speeding animation drawing coefficient (in percents), "
        "type: float, default: 1.0",
    )

    parser.add_argument(
        "maze_file",
        metavar="maze-file",
        type=argparse.FileType("r"),
        help="A path to readable file with maze definition",
    )

    args = parser.parse_args()

    maze = validate_maze(args.maze_file.readlines())
    args.maze_file.close()

    curses.wrapper(
        draw,
        maze,
        {
            "Random": algorithms.random_search,
            "BFS": algorithms.bfs,
            "DFS": algorithms.dfs,
            "Dijkstra": algorithms.dijkstra,
            "Greedy": algorithms.greedy,
            "A*": algorithms.a_star,
        }[args.algorithm],
        args.speed,
    )
