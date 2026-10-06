from graph import Graph
from models import Connection, Drone, Zone

Plan = tuple[Drone, Zone, Connection, bool]  # drone, target, link, arrives


class ValidationError(Exception):
    """Raised when a simulation output breaks a rule."""


class Validator:
    """Replays the printed turns and checks every rule of the subject."""

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        """Store the map; the drones are created when validating."""
        self.graph = graph
        self.nb_drones = nb_drones
        self.drones: dict[int, Drone] = {}
        self.heading: dict[int, Zone] = {}

    def validate(self, lines: list[str]) -> None:
        """Replay all lines; raise ValidationError at the first problem."""
        start = self.graph.start
        end = self.graph.end
        if start is None or end is None:
            raise ValidationError("graph has no start or end zone")
        for drone_id in range(1, self.nb_drones + 1):
            self.drones[drone_id] = Drone(drone_id, start)
            start.enter_zone()
        for turn, line in enumerate(lines, 1):
            try:
                self._play_turn(line)
            except ValidationError as e:
                raise ValidationError(f"turn {turn}: {e}") from e
        for drone in self.drones.values():
            if drone.location is not end:
                raise ValidationError(
                    f"D{drone.drone_id} never reached '{end.name}'"
                )

    def _play_turn(self, line: str) -> None:
        """Check and apply one line of output."""
        moves = self._read_moves(line)
        for drone_id, drone in self.drones.items():
            if isinstance(drone.location, Connection):
                if drone_id not in moves:
                    raise ValidationError(
                        f"D{drone_id} cannot wait on a connection"
                    )
        plans = [
            self._plan_move(self.drones[drone_id], label)
            for drone_id, label in moves.items()
        ]
        # 1. drones leaving a zone free their place first
        for drone, _, _, _ in plans:
            if isinstance(drone.location, Zone):
                drone.location.leave_zone()
        # 2. drones starting a trip take a place on the link
        for drone, _, conn, _ in plans:
            if isinstance(drone.location, Zone):
                if not conn.enter_connection():
                    raise ValidationError(
                        f"link {conn.start_zone.name}-"
                        f"{conn.destination_zone.name} is full"
                    )
        # 3. drones that arrive take a place in the destination zone
        for drone, target, conn, arrives in plans:
            drone.count_reset()
            if arrives:
                if not target.enter_zone():
                    raise ValidationError(f"zone '{target.name}' is full")
                conn.leave_connection()
                drone.location = target
                self.heading.pop(drone.drone_id, None)
            else:
                drone.location = conn
                self.heading[drone.drone_id] = target
                drone.increase_turn()

    def _read_moves(self, line: str) -> dict[int, str]:
        """Split a line into {drone id: label after 'D<id>-'}."""
        moves: dict[int, str] = {}
        for item in line.split():
            head, sep, label = item.partition("-")
            if not sep or not label or not head.startswith("D"):
                raise ValidationError(f"malformed movement '{item}'")
            try:
                drone_id = int(head[1:])
            except ValueError:
                raise ValidationError(
                    f"malformed drone id in '{item}'"
                ) from None
            if drone_id not in self.drones:
                raise ValidationError(f"unknown drone D{drone_id}")
            if drone_id in moves:
                raise ValidationError(f"D{drone_id} appears twice")
            moves[drone_id] = label
        return moves

    def _plan_move(self, drone: Drone, label: str) -> Plan:
        """Work out what one drone does this turn, or fail."""
        location = drone.location
        if isinstance(location, Connection):
            target = self.heading[drone.drone_id]
            if label != target.name:
                raise ValidationError(
                    f"D{drone.drone_id} must arrive at '{target.name}'"
                )
            drone.increase_turn()
            if drone.turn_count != target.entry_cost():
                raise ValidationError(
                    f"D{drone.drone_id} flight did not last "
                    f"{target.entry_cost()} turns"
                )
            return drone, target, location, True
        if location is self.graph.end:
            raise ValidationError(
                f"D{drone.drone_id} moved after being delivered"
            )
        return self._plan_departure(drone, location, label)

    def _plan_departure(
        self, drone: Drone, origin: Zone, label: str
    ) -> Plan:
        """Check a drone leaving a zone for a neighbor."""
        flight = "-" in label
        if flight:
            names = label.split("-")
            if len(names) != 2 or names[0] != origin.name:
                raise ValidationError(
                    f"D{drone.drone_id}: bad connection '{label}'"
                )
            target_name = names[1]
        else:
            target_name = label
        target = self.graph.zones.get(target_name)
        if target is None:
            raise ValidationError(f"unknown zone '{target_name}'")
        key = frozenset((origin.name, target.name))
        conn = self.graph.connections.get(key)
        if conn is None:
            raise ValidationError(
                f"no connection {origin.name}-{target.name}"
            )
        if target.is_blocked():
            raise ValidationError(f"zone '{target.name}' is blocked")
        if (target.entry_cost() == 2) != flight:
            raise ValidationError(
                f"D{drone.drone_id}: wrong label '{label}' "
                f"for a move into '{target.name}'"
            )
        return drone, target, conn, not flight
