from graph import Graph
from models import EndHub, StartHub, Zone

VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


class ParsingError(Exception):
    """Raised when the map file is invalid."""


class Parser:
    """Reads a map file and builds a Graph."""

    def __init__(self, file_path: str) -> None:
        """Store the path and prepare an empty graph."""
        self.file_path = file_path
        self.graph = Graph()
        self.nb_drones: int = 0

    def parse(self) -> Graph:
        """Parse the whole file; raise ParsingError on any problem."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    clean = line.split("#")[0].strip()
                    if not clean:
                        continue
                    try:
                        self._process_line(clean)
                    except ValueError as e:
                        raise ParsingError(f"line {line_num}: {e}") from e
        except (OSError, UnicodeDecodeError) as e:
            raise ParsingError(f"cannot read '{self.file_path}': {e}") from e
        self._validate_final()
        return self.graph

    def _process_line(self, line: str) -> None:
        """Dispatch a cleaned line to the right handler."""
        keyword, sep, content = line.partition(":")
        if not sep:
            raise ValueError("missing ':' after keyword")
        keyword = keyword.strip()
        content = content.strip()
        if self.nb_drones == 0 and keyword != "nb_drones":
            raise ValueError("first line must be 'nb_drones: <number>'")
        if keyword == "nb_drones":
            self._parse_nb_drones(content)
        elif keyword in ("hub", "start_hub", "end_hub"):
            self._parse_zone(keyword, content)
        elif keyword == "connection":
            self._parse_connection(content)
        else:
            raise ValueError(f"unknown keyword '{keyword}'")

    def _parse_nb_drones(self, content: str) -> None:
        """Read the number of drones."""
        if self.nb_drones != 0:
            raise ValueError("nb_drones defined more than once")
        self.nb_drones = self._positive_int(content, "nb_drones")

    def _parse_zone(self, keyword: str, content: str) -> None:
        """Build a zone from a hub/start_hub/end_hub line."""
        body, tags = self._split_metadata(content)
        fields = body.split()
        if len(fields) != 3:
            raise ValueError("zone needs '<name> <x> <y>'")
        name, raw_x, raw_y = fields
        if "-" in name:
            raise ValueError(f"zone name '{name}' cannot contain dashes")
        try:
            x, y = int(raw_x), int(raw_y)
        except ValueError:
            raise ValueError("coordinates must be integers") from None
        self._check_keys(tags, {"zone", "color", "max_drones"})
        zone_type = tags.get("zone", "normal")
        if zone_type not in VALID_ZONE_TYPES:
            raise ValueError(f"invalid zone type '{zone_type}'")
        color = tags.get("color", "none")
        zone: Zone
        if keyword == "start_hub":
            zone = StartHub(name, x, y, color, 1, zone_type)
        elif keyword == "end_hub":
            zone = EndHub(name, x, y, color, 1, zone_type)
        else:
            max_drones = 1
            if "max_drones" in tags:
                max_drones = self._positive_int(
                    tags["max_drones"], "max_drones"
                )
            zone = Zone(name, x, y, color, max_drones, zone_type)
        self.graph.add_zone(zone)

    def _parse_connection(self, content: str) -> None:
        """Build a connection from a connection line."""
        body, tags = self._split_metadata(content)
        names = body.split("-")
        if len(names) != 2 or not all(names) or " " in body:
            raise ValueError("connection needs '<zone1>-<zone2>'")
        self._check_keys(tags, {"max_link_capacity"})
        capacity = 1
        if "max_link_capacity" in tags:
            capacity = self._positive_int(
                tags["max_link_capacity"], "max_link_capacity"
            )
        self.graph.add_connection(names[0], names[1], capacity)

    def _split_metadata(self, content: str) -> tuple[str, dict[str, str]]:
        """Split 'text [k=v k=v]' into the text and a tag dictionary."""
        if "[" not in content and "]" not in content:
            return content, {}
        if (content.count("[") != 1 or content.count("]") != 1
                or not content.endswith("]")):
            raise ValueError("malformed metadata block")
        body, _, meta = content.partition("[")
        tags: dict[str, str] = {}
        for token in meta[:-1].split():
            key, sep, value = token.partition("=")
            if not sep or not key or not value:
                raise ValueError(f"invalid metadata tag '{token}'")
            if key in tags:
                raise ValueError(f"duplicate metadata tag '{key}'")
            tags[key] = value
        return body.strip(), tags

    def _check_keys(self, tags: dict[str, str], allowed: set[str]) -> None:
        """Reject metadata keys that are not allowed here."""
        for key in tags:
            if key not in allowed:
                raise ValueError(f"unknown metadata key '{key}'")

    def _positive_int(self, text: str, label: str) -> int:
        """Convert text to an int > 0 or raise ValueError."""
        try:
            value = int(text)
        except ValueError:
            raise ValueError(
                f"{label} must be an integer, got '{text}'"
            ) from None
        if value <= 0:
            raise ValueError(f"{label} must be positive, got {value}")
        return value

    def _validate_final(self) -> None:
        """Check the things that can only be known after the last line."""
        if self.nb_drones == 0:
            raise ParsingError("missing 'nb_drones'")
        if self.graph.start is None:
            raise ParsingError("missing start_hub")
        if self.graph.end is None:
            raise ParsingError("missing end_hub")
