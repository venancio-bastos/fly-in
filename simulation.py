from graph import Graph
from pathfinder import Move, Pathfinder


class Simulation:
    """Runs the planner and turns the plans into output lines."""

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        """Store the map and the number of drones."""
        self.graph = graph
        self.nb_drones = nb_drones
        self.plans: list[list[Move]] = []

    def run(self) -> list[str]:
        """Return one text line per simulation turn."""
        self.plans = Pathfinder(self.graph, self.nb_drones).plan_all()
        events: dict[int, list[str]] = {}
        for drone_id, moves in enumerate(self.plans, 1):
            for move in moves:
                for turn, label in move.turn_labels():
                    events.setdefault(turn, []).append(f"D{drone_id}-{label}")
        last = max(events) if events else 0
        return [" ".join(events.get(t, [])) for t in range(1, last + 1)]
