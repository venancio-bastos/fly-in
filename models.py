class Zone:
    """A zone of the map where drones can stay."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        color: str = "none",
        max_drones: int = 1,
        type_zone: str = "normal",
    ) -> None:
        """Store the zone data; the zone starts with no drones."""
        self.name = name
        self.x = x
        self.y = y
        self.type_zone = type_zone
        self.color = color
        self.max_drones = max_drones
        self.current_drones = 0

    def can_hold(self, count: int) -> bool:
        """Tell if the zone can take one more drone given `count`."""
        return count < self.max_drones

    def has_space_left(self) -> bool:
        """Tell if the zone has room right now."""
        return self.can_hold(self.current_drones)

    def enter_zone(self) -> bool:
        """Add a drone to the zone; return False if it is full."""
        if self.has_space_left():
            self.current_drones += 1
            return True
        return False

    def leave_zone(self) -> None:
        """Remove a drone from the zone."""
        if self.current_drones > 0:
            self.current_drones -= 1

    def entry_cost(self) -> int:
        """Return how many turns it takes to move into this zone."""
        return 2 if self.type_zone == "restricted" else 1

    def is_blocked(self) -> bool:
        """Tell if drones are forbidden to enter this zone."""
        return self.type_zone == "blocked"


class StartHub(Zone):
    """Start zone: no capacity limit."""

    def can_hold(self, count: int) -> bool:
        """Always has room."""
        return True


class EndHub(Zone):
    """End zone: no capacity limit."""

    def can_hold(self, count: int) -> bool:
        """Always has room."""
        return True


class Connection:
    """A bidirectional link between two zones."""

    def __init__(
        self,
        start_zone: Zone,
        destination_zone: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        """Store the two zones and the link capacity."""
        self.start_zone = start_zone
        self.destination_zone = destination_zone
        self.max_link_capacity = max_link_capacity
        self.current_drones = 0

    def has_space_left(self) -> bool:
        """Tell if the link can take one more drone."""
        return self.max_link_capacity > self.current_drones

    def enter_connection(self) -> bool:
        """Put a drone on the link; return False if it is full."""
        if self.has_space_left():
            self.current_drones += 1
            return True
        return False

    def leave_connection(self) -> None:
        """Take a drone off the link."""
        if self.current_drones > 0:
            self.current_drones -= 1


class Drone:
    """A drone that is in a zone or travelling on a connection."""

    def __init__(
        self,
        drone_id: int,
        location: Zone | Connection,
        turn_count: int = 0,
    ) -> None:
        """Store the drone id, its location and its turn counter."""
        self.drone_id = drone_id
        self.location = location
        self.turn_count = turn_count

    def count_reset(self) -> None:
        """Reset the turn counter to zero."""
        self.turn_count = 0

    def increase_turn(self) -> None:
        """Add one turn to the counter."""
        self.turn_count += 1
