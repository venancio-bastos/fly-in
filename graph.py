from models import Connection, EndHub, StartHub, Zone


class Graph:
    """Network of zones and the connections between them."""

    def __init__(self) -> None:
        """Create an empty graph."""
        self.zones: dict[str, Zone] = {}
        self.connections: dict[frozenset[str], Connection] = {}
        self.adjacency: dict[str, list[Connection]] = {}
        self.start: StartHub | None = None
        self.end: EndHub | None = None

    def add_zone(self, zone: Zone) -> None:
        """Register a zone; reject duplicates and extra start/end."""
        if zone.name in self.zones:
            raise ValueError(f"duplicate zone name '{zone.name}'")
        if isinstance(zone, StartHub):
            if self.start is not None:
                raise ValueError("more than one start_hub")
            self.start = zone
        elif isinstance(zone, EndHub):
            if self.end is not None:
                raise ValueError("more than one end_hub")
            self.end = zone
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

    def add_connection(
        self, name1: str, name2: str, max_link_capacity: int = 1
    ) -> None:
        """Link two existing zones; reject unknown, self and duplicates."""
        for name in (name1, name2):
            if name not in self.zones:
                raise ValueError(f"unknown zone '{name}'")
        if name1 == name2:
            raise ValueError(f"zone '{name1}' cannot connect to itself")
        key = frozenset((name1, name2))
        if key in self.connections:
            raise ValueError(f"duplicate connection {name1}-{name2}")
        conn = Connection(
            self.zones[name1], self.zones[name2], max_link_capacity
        )
        self.connections[key] = conn
        self.adjacency[name1].append(conn)
        self.adjacency[name2].append(conn)

    def get_neighbors(self, zone: Zone) -> list[tuple[Zone, Connection]]:
        """Return (neighbor, connection) pairs reachable from a zone."""
        result: list[tuple[Zone, Connection]] = []
        for conn in self.adjacency[zone.name]:
            if conn.start_zone is zone:
                other = conn.destination_zone
            else:
                other = conn.start_zone
            result.append((other, conn))
        return result
