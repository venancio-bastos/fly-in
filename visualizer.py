import os
import sys

from graph import Graph

RESET = "\033[0m"
BOLD = "\033[1m"
RAINBOW = (196, 208, 226, 46, 51, 21, 129)

COLOR_CODES: dict[str, int] = {
    "black": 240, "gray": 245, "grey": 245, "white": 255,
    "red": 196, "darkred": 160, "crimson": 161, "maroon": 124,
    "orange": 208, "brown": 130, "gold": 220, "yellow": 226,
    "green": 34, "lime": 118, "cyan": 51, "blue": 33,
    "purple": 129, "violet": 177, "magenta": 201, "pink": 213,
}


class TerminalVisualizer:
    """Prints the simulation turn by turn, with colors and zone states."""

    def __init__(
        self, graph: Graph, nb_drones: int, use_color: bool | None = None
    ) -> None:
        """Prepare the replay state; colors only on a real terminal."""
        self.graph = graph
        self.nb_drones = nb_drones
        if use_color is None:
            use_color = "FORCE_COLOR" in os.environ or (
                sys.stdout.isatty() and "NO_COLOR" not in os.environ
            )
        self.use_color = use_color
        self.in_zone: dict[int, str] = {}
        self.in_flight: dict[int, tuple[str, str]] = {}
        self.arrival_turn: dict[int, int] = {}
        self.moves_per_turn: list[int] = []
        self.total_cost = 0

    def show(self, lines: list[str]) -> None:
        """Print every turn followed by a summary of the run."""
        start = self.graph.start
        if start is None:
            return
        self.in_zone = {d: start.name for d in range(1, self.nb_drones + 1)}
        self.in_flight = {}
        self.arrival_turn = {}
        self.moves_per_turn = []
        self.total_cost = 0
        for turn, line in enumerate(lines, 1):
            self._show_turn(turn, line)
        self._show_summary(len(lines))

    def _paint(self, text: str, color: str, bold: bool = False) -> str:
        """Wrap text in the ANSI code of a color name."""
        if not self.use_color:
            return text
        prefix = BOLD if bold else ""
        if color == "rainbow":
            letters = "".join(
                f"\033[38;5;{RAINBOW[i % len(RAINBOW)]}m{ch}"
                for i, ch in enumerate(text)
            )
            return f"{prefix}{letters}{RESET}"
        code = COLOR_CODES.get(color)
        if code is None:
            return f"{prefix}{text}{RESET}" if bold else text
        return f"{prefix}\033[38;5;{code}m{text}{RESET}"

    def _paint_zone(self, name: str, bold: bool = False) -> str:
        """Paint a zone name with the color given in the map file."""
        return self._paint(name, self.graph.zones[name].color, bold)

    def _apply_move(self, turn: int, token: str) -> str:
        """Update the replay state with one movement; return it colored."""
        head, _, label = token.partition("-")
        drone_id = int(head[1:])
        if "-" in label:
            origin, target = label.split("-")
            self.in_zone.pop(drone_id, None)
            self.in_flight[drone_id] = (origin, target)
            shown = f"{origin}-{self._paint_zone(target)}"
            return f"{head}-{shown}"
        self.in_flight.pop(drone_id, None)
        self.in_zone[drone_id] = label
        zone = self.graph.zones[label]
        self.total_cost += zone.entry_cost()
        end = self.graph.end
        if end is not None and label == end.name:
            self.arrival_turn[drone_id] = turn
        return f"{head}-{self._paint_zone(label)}"

    def _show_turn(self, turn: int, line: str) -> None:
        """Print the movements and the zone states of one turn."""
        tokens = line.split()
        self.moves_per_turn.append(len(tokens))
        painted = " ".join(self._apply_move(turn, t) for t in tokens)
        title = (
            f"Turn {turn}  |  delivered {len(self.arrival_turn)}"
            f"/{self.nb_drones}  |  in flight {len(self.in_flight)}"
        )
        print(self._paint(f"== {title}", "white", bold=True))
        print(painted if painted else "(no movement)")
        self._show_zone_states()
        print()

    def _show_zone_states(self) -> None:
        """Print every occupied zone, its load and the flying drones."""
        occupants: dict[str, list[int]] = {}
        for drone_id, name in sorted(self.in_zone.items()):
            occupants.setdefault(name, []).append(drone_id)
        end = self.graph.end
        start = self.graph.start
        for name, zone in self.graph.zones.items():
            ids = occupants.get(name)
            if not ids:
                continue
            tag = "" if zone.type_zone == "normal" else f" [{zone.type_zone}]"
            label = self._paint_zone(name, bold=True)
            if zone is end:
                print(f"  {label}{tag}  delivered: {len(ids)}")
                continue
            drones = " ".join(f"D{i}" for i in ids)
            if zone is start:
                print(f"  {label}{tag}  waiting: {drones}")
                continue
            full = " FULL" if len(ids) >= zone.max_drones else ""
            load = f"{len(ids)}/{zone.max_drones}"
            print(f"  {label}{tag}  {load}{full}  {drones}")
        for drone_id, (origin, target) in sorted(self.in_flight.items()):
            link = f"{origin}-{self._paint_zone(target)}"
            print(f"  ~ D{drone_id} on {link} (arrives next turn)")

    def _show_summary(self, total_turns: int) -> None:
        """Print the final numbers of the run."""
        print(self._paint("== Summary", "white", bold=True))
        print(f"  Total turns: {total_turns}")
        print(f"  Drones delivered: {len(self.arrival_turn)}/{self.nb_drones}")
        if total_turns:
            average = sum(self.moves_per_turn) / total_turns
            print(f"  Drones moving per turn (avg): {average:.2f}")
        if self.arrival_turn:
            mean = sum(self.arrival_turn.values()) / len(self.arrival_turn)
            print(f"  Turns per drone (avg): {mean:.2f}")
        print(f"  Total path cost: {self.total_cost}")
