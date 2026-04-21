import json
from pathlib import Path
from typing import Any


def append_to_json_file(file_path: str, record: Any) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with open(path, "r+") as f:
            data = json.load(f)
            data.append(record)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
    else:
        with open(path, "w") as f:
            json.dump([record], f, indent=4)
