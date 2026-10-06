import heapq

from graph import Graph
from models import Connection, Zone

State = tuple[str, int]  # (zone name, turn)


class PlanningError(Exception):
    """Raised when no valid path exists."""


class Move:
    """One trip between two zones that starts at turn `depart`."""

    def __init__(
        self,
        origin: Zone,
        target: Zone,
        conn: Connection,
        depart: int,
        duration: int,
    ) -> None:
        """Store the trip; the drone is at `origin` at time `depart`."""
        self.origin = origin
        self.target = target
        self.conn = conn
        self.depart = depart
        self.duration = duration

    def turn_labels(self) -> list[tuple[int, str]]:
        """Return (turn, text) pairs for the output lines."""
        if self.duration == 1:
            return [(self.depart + 1, self.target.name)]
        link = f"{self.origin.name}-{self.target.name}"
        return [(self.depart + 1, link), (self.depart + 2, self.target.name)]


class ReservationTable:
    """Counts the drones using each zone and link at each turn."""

    def __init__(self) -> None:
        """Start with nothing reserved."""
        self.zone_use: dict[tuple[Zone, int], int] = {}
        self.link_use: dict[tuple[Connection, int], int] = {}

    def zone_has_space(self, zone: Zone, turn: int) -> bool:
        """Tell if one more drone fits in `zone` at the end of `turn`."""
        return zone.can_hold(self.zone_use.get((zone, turn), 0))

    def link_has_space(
        self, conn: Connection, depart: int, duration: int
    ) -> bool:
        """Tell if the link is free during every turn of the trip."""
        for turn in range(depart + 1, depart + duration + 1):
            used = self.link_use.get((conn, turn), 0)
            if used >= conn.max_link_capacity:
                return False
        return True

    def reserve(self, moves: list[Move], start: Zone) -> None:
        """Book everything a planned drone will use."""
        zone = start
        arrival = 0
        for move in moves:
            for turn in range(arrival, move.depart + 1):
                zkey = (zone, turn)
                self.zone_use[zkey] = self.zone_use.get(zkey, 0) + 1
            end_turn = move.depart + move.duration
            for turn in range(move.depart + 1, end_turn + 1):
                lkey = (move.conn, turn)
                self.link_use[lkey] = self.link_use.get(lkey, 0) + 1
            zone = move.target
            arrival = end_turn


class Pathfinder:
    """Plans every drone, one after the other, around earlier plans."""

    def __init__(self, graph: Graph, nb_drones: int) -> None:
        """Prepare the planner and a safety limit on the search time."""
        self.graph = graph
        self.nb_drones = nb_drones
        self.max_time = 2 * len(graph.zones) * (nb_drones + 1)

    def plan_all(self) -> list[list[Move]]:
        """Return one list of moves per drone."""
        start, _ = self._endpoints()
        table = ReservationTable()
        plans: list[list[Move]] = []
        for _ in range(self.nb_drones):
            moves = self.find_path(table)
            table.reserve(moves, start)
            plans.append(moves)
        return plans

    def find_path(self, table: ReservationTable) -> list[Move]:
        """Dijkstra over (zone, turn) states; earliest arrival wins."""
        start, end = self._endpoints()
        first: State = (start.name, 0)
        best: dict[State, int] = {first: 0}
        parents: dict[State, tuple[State, Move | None]] = {}
        visited: set[State] = set()
        queue: list[tuple[int, int, str]] = [(0, 0, start.name)]
        while queue:
            time, penalty, name = heapq.heappop(queue)
            state: State = (name, time)
            if state in visited:
                continue
            visited.add(state)
            if name == end.name:
                return self._rebuild(parents, state)
            if time >= self.max_time:
                continue
            zone = self.graph.zones[name]
            for nxt, extra, move in self._expand(zone, time, table):
                new_penalty = penalty + extra
                if nxt in visited:
                    continue
                if nxt in best and best[nxt] <= new_penalty:
                    continue
                best[nxt] = new_penalty
                parents[nxt] = (state, move)
                heapq.heappush(queue, (nxt[1], new_penalty, nxt[0]))
        raise PlanningError("no valid path from start to end")

    def _expand(
        self, zone: Zone, time: int, table: ReservationTable
    ) -> list[tuple[State, int, Move | None]]:
        """List every wait or move possible from `zone` at `time`."""
        options: list[tuple[State, int, Move | None]] = []
        if table.zone_has_space(zone, time + 1):
            options.append(((zone.name, time + 1), 0, None))
        for neighbor, conn in self.graph.get_neighbors(zone):
            if neighbor.is_blocked():
                continue
            duration = neighbor.entry_cost()
            if not table.link_has_space(conn, time, duration):
                continue
            if not table.zone_has_space(neighbor, time + duration):
                continue
            extra = 0 if neighbor.type_zone == "priority" else 1
            move = Move(zone, neighbor, conn, time, duration)
            options.append(((neighbor.name, time + duration), extra, move))
        return options

    def _rebuild(
        self,
        parents: dict[State, tuple[State, Move | None]],
        state: State,
    ) -> list[Move]:
        """Walk the parents back to the start and return the moves."""
        moves: list[Move] = []
        while state in parents:
            state, move = parents[state]
            if move is not None:
                moves.append(move)
        moves.reverse()
        return moves

    def _endpoints(self) -> tuple[Zone, Zone]:
        """Return (start, end), failing if the graph lacks one."""
        start = self.graph.start
        end = self.graph.end
        if start is None or end is None:
            raise PlanningError("graph has no start or end zone")
        return start, end
