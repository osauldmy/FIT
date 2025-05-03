"""
Run example:
   python -m pathfinding --algorithm 'A*' --speed 1 dataset/100.txt
"""

from pathfinding import cli


if __name__ == "__main__":
    try:
        cli.main()
    except KeyboardInterrupt:
        # possible Ctrl+C interruption of running algorithm
        pass
