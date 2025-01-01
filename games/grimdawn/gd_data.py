import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Progress:
    _progress: int
    _max_progress: int
    _status_message: str

    def progress(self) -> int:
        return self._progress

    def max_progress(self) -> int:
        return self._max_progress

    def status_message(self) -> str:
        return self._status_message

    # def task_id(self) -> int:
    #     return self._task_id if self._task_id is not None else -1


@dataclass
class MultiStepProgress(Progress):
    _step_progress: int
    _step_max_progress: int
    _step_status_message: str

    def step_progress(self) -> int:
        return self._step_progress

    def step_max_progress(self) -> int:
        return self._step_max_progress

    def step_status_msg(self) -> str:
        return f"({self._step_progress} / {self._step_max_progress}) {self._step_status_message}"


@dataclass
class ExtractStatus:
    _is_running: bool
    _databases: list[Path]
    _databases_extracted: list[Path] = field(default_factory=list)
    _status_message: str = ""
    _extract_path: Path = Path()

    def is_running(self) -> bool:
        return self._is_running

    def progress(self) -> int:
        return len(self._databases_extracted)

    def max_progress(self) -> int:
        return len(self._databases)

    def databases(self) -> list[Path]:
        return self._databases

    def databases_extracted(self) -> list[Path]:
        return self._databases_extracted

    def status_message(self) -> str:
        return self._status_message

    def extract_path(self) -> Path:
        return self._extract_path


class ModExtractInfo:
    checksum: str
    game_version: str

    def _extract_data(self) -> dict[str, str]:
        extract_info: dict[str, str] = {}
        extract_info["checksum"] = self.checksum
        extract_info["game_version"] = self.game_version
        return extract_info

    @staticmethod
    def _map(source_data: dict[str, str], target: "ModExtractInfo") -> "ModExtractInfo":
        target.checksum = source_data["checksum"]
        target.game_version = source_data["game_version"]
        return target

    @staticmethod
    def serialize(mod_extract_info: "ModExtractInfo", json_file: Path):
        with json_file.open("w") as json_io:
            extract_data = mod_extract_info._extract_data()
            json.dump(extract_data, json_io)

    @staticmethod
    def serializes(mod_extract_info: "ModExtractInfo") -> str:
        extract_data = mod_extract_info._extract_data()
        return json.dumps(extract_data)

    @staticmethod
    def deserialize(json_file: Path) -> "ModExtractInfo":
        if not json_file.exists():
            return ModExtractInfo()
        with json_file.open("r") as json_io:
            extract_data = json.load(json_io)
            mod_extract_info: ModExtractInfo = ModExtractInfo._map(
                extract_data, ModExtractInfo()
            )
            return mod_extract_info

    @staticmethod
    def deserializes(json_text: str) -> "ModExtractInfo":
        extract_data = json.loads(json_text)
        mod_extract_info: ModExtractInfo = ModExtractInfo._map(
            extract_data, ModExtractInfo()
        )
        return mod_extract_info
