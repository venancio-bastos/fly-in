import sys

from parser import Parser, ParsingError
from pathfinder import PlanningError
from simulation import Simulation
from validator import ValidationError, Validator
from visualizer import TerminalVisualizer

USAGE = "Usage: python3 main.py <map_file> [--plain]"


def main() -> None:
    """Parse the map, simulate, show the result and validate it."""
    flags = [arg for arg in sys.argv[1:] if arg.startswith("--")]
    paths = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if len(paths) != 1 or any(flag != "--plain" for flag in flags):
        print(USAGE, file=sys.stderr)
        sys.exit(1)
    parser = Parser(paths[0])
    try:
        graph = parser.parse()
    except ParsingError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    simulation = Simulation(graph, parser.nb_drones)
    try:
        lines = simulation.run()
    except PlanningError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    if flags:
        for line in lines:
            print(line)
    else:
        TerminalVisualizer(graph, parser.nb_drones).show(lines)
    validator = Validator(graph, parser.nb_drones)
    try:
        validator.validate(lines)
    except ValidationError as e:
        print(f"Invalid simulation: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Total turns: {len(lines)} (validated)", file=sys.stderr)


if __name__ == "__main__":
    main()
