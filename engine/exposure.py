from collections import defaultdict
from typing import Dict, Tuple


class ExposureTracker:
    """
    Simple in-memory exposure tracker.

    Key: (asset, direction, window_key) -> contracts
    """

    def __init__(self, max_per_trade: int, max_per_direction_per_window: int):
        self.max_per_trade = max_per_trade
        self.max_per_direction_per_window = max_per_direction_per_window
        self._exposure: Dict[Tuple[str, str, str], int] = defaultdict(int)

    def get(self, asset: str, direction: str, window_key: str) -> int:
        return self._exposure[(asset, direction, window_key)]

    def can_add(self, asset: str, direction: str, window_key: str, size: int) -> bool:
        current = self.get(asset, direction, window_key)
        return current + size <= self.max_per_direction_per_window

    def add(self, asset: str, direction: str, window_key: str, size: int) -> None:
        self._exposure[(asset, direction, window_key)] += size
