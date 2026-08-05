import json
from pathlib import Path

class CounterStore:
    """
    Persistence abstraction responsible solely for loading and saving 
    the deterministic Work Order sequence state.
    """
    def __init__(self, filepath: Path | str | None = None):
        if filepath is None:
            # Canonical Work Order sequence storage
            self.filepath = Path(__file__).parent / "state" / "work_order_counter.json"
        else:
            self.filepath = Path(filepath)

    def load(self) -> int:
        if not self.filepath.exists():
            return 1
        try:
            data = json.loads(self.filepath.read_text(encoding="utf-8"))
            return data.get("next_sequence", 1)
        except (json.JSONDecodeError, IOError):
            return 1

    def save(self, next_sequence: int) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(json.dumps({"next_sequence": next_sequence}, indent=2), encoding="utf-8")