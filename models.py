from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class FlightType(Enum):
    ARRIVAL = "A"
    DEPARTURE = "D"

    @property
    def emoji_label(self) -> str:
        return "🛬 도착" if self is FlightType.ARRIVAL else "🛫 출발"

    @property
    def operation(self) -> str:
        return "getFltArrivalsDeOdp" if self is FlightType.ARRIVAL else "getFltDeparturesDeOdp"


class Terminal(NamedTuple):
    name: str
    terminal_id: str


@dataclass(slots=True)
class FlightItem:
    flight_number: str = ""
    scheduled_datetime: str = ""
    actual_datetime: str = ""
    airport_name: str = ""
    aircraft_type: str = ""
    registration_number: str = ""
    gate_number: str = ""
    remark: str = ""
    terminal_id: str = ""
    codeshare: str = ""
    type_of_flight: str = ""

    @property
    def is_master(self) -> bool:
        return self.codeshare == "Master"
