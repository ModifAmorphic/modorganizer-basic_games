import os
from pathlib import Path
import random
import subprocess
import threading
from typing import Optional, Protocol, Union
from .gd_data import ExtractStatus
# from PyQt6.QtCore import QDir, QFileInfo, qFatal, qCritical, qWarning, qInfo, qDebug

class ExtractUpdate(Protocol):
    def __call__(self, extract_status: ExtractStatus, extraction_id: int) -> None: ...

class dbr:
    def __init__(self, relative_path: str, dbdata: dict[str, str]):
        self.relative_path = relative_path

class ThreadedModExtractor:
    GameExtractPath: Path
    ModsExtractPath: Path

    _game_path: Path
    _data_path: Path
    _archive_tool: Path
    # _update_callbacks: list[tuple[ExtractUpdate, int | None]] = []
    _update_callbacks: dict[ExtractUpdate, tuple[set[int], bool]] = {}

    def __init__(self, game_path: Path, data_path: Path):
        self._game_path = game_path
        self._data_path = data_path
        self._archive_tool = self._game_path.joinpath("ArchiveTool.exe")
        self.GameExtractPath = self._data_path.joinpath("game_data")
        self.ModsExtractPath = self._data_path.joinpath("mods")

    @staticmethod
    def generate_extraction_id() -> int:
        """
        Generates a new unique extraction id.
        """
        return random.randint(100, 100000) 
    
    def on_extract_update(self, subscriber: ExtractUpdate, extraction_id: Union[int, None] = None, all_updates: bool = False):
        """
        Subscribes a callback function to be called when an extraction update is available.

        Args:
            callback (ExtractUpdate): The callback function to call when an extraction update is available.
            extraction_id (Optional[int]): An optional id to track the extraction progress. If provided, the function will only be triggered for update events with a matching extraction_id.
            passthrough (Optional[object]): An optional object to pass through to the callback function.
        """

        if extraction_id is None and not all_updates:
            raise ValueError("extraction_id must be provided if all_updates is False.")

        if subscriber not in self._update_callbacks:
            extract_set: set[int] = { extraction_id } if extraction_id else set()
            self._update_callbacks[subscriber] = extract_set, all_updates
            return
        
        ids = self._update_callbacks[subscriber][0]
        if extraction_id is not None:
            if extraction_id not in ids:
                ids.add(extraction_id)
        
        self._update_callbacks[subscriber] =  ids, all_updates

    def _on_extract_update(self, extract_status: ExtractStatus, extraction_id: int):
        for subscriber in self._update_callbacks:
            ids = self._update_callbacks[subscriber][0]
            all_updates = self._update_callbacks[subscriber][1]
            if extraction_id in ids or all_updates:
                subscriber(extract_status, extraction_id)

    def _extract_databases(
        self,
        database_paths: list[Path],
        out_path: Path,
        callback_id: int = 0
    ):
        if callback_id == 0:
            callback_id = ThreadedModExtractor.generate_extraction_id()
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        db_extracted: list[Path] = []
        for db_path in database_paths:
            self._on_extract_update(
                    ExtractStatus(True, database_paths, db_extracted, f"Extracting database {db_path}", out_path),
                    callback_id)
            process = subprocess.Popen(
                [self._archive_tool, db_path.absolute(), "-database", out_path.absolute()]
                , startupinfo=startupinfo
            )
            process.wait()
            db_extracted.append(db_path)
        self._on_extract_update        (
            ExtractStatus(False, database_paths, db_extracted, "Extraction of all Databases complete.", out_path), 
            callback_id)

    def extract_grimdawn(self, extraction_id: Optional[int]) -> int:
        """
        Extracts the Grim Dawn databases from the game to the GameExtractPath in a background thread.

        Args:
            extraction_id (Optional[int]): An optional id to track the extraction progress. If not provided, a new id will be generated.
        
        Returns:
            extraction_id: The extraction id assigned to this extraction process.
        """
        databases = [
            Path(self._game_path, "database", "database.arz"),
            Path(self._game_path, "survivalmode1", "database", "SurvivalMode1.arz"),
            Path(self._game_path, "survivalmode2", "database", "SurvivalMode2.arz"),
            Path(self._game_path, "gdx1", "database", "GDX1.arz"),
            Path(self._game_path, "gdx2", "database", "GDX2.arz")
        ]
        if not extraction_id:
            extraction_id = ThreadedModExtractor.generate_extraction_id()
        
        status = ExtractStatus(True, databases, [], "Extracting Grim Dawn databases.")
        self._on_extract_update(status, extraction_id)
        
        t = threading.Thread(
            target=self._extract_databases,
            args=[databases, self.GameExtractPath, extraction_id],
        )
        t.daemon = False
        t.start()
        return extraction_id
    
    #callback: Callable[[ExtractStatus, int, dict[str, object]], None]
    def extract_mod_databases(self, mod_path: Path, mod_unpack_path: Path, extraction_id: Optional[int]) -> int:
        """
        Extracts the Mod databases from a mod path to the ModsExtractPath in a background thread.

        Args:
            mod_path (Path): The path of the mod containing databases to be extracted. Expected database path is "mods/*/database/*.arz".
            mod_unpack_path (Path): The path to extract the databases to.
            extraction_id (Optional[int]): An optional id to track the extraction progress. If not provided, a new id will be generated.

        Returns:
            extraction_id: The extraction id assigned to this extraction process.
        """

        databases: list[Path] = []
        for db in mod_path.glob("mods/*/database/*.arz", case_sensitive=False):
            databases.append(db)

        if not extraction_id:
            extraction_id = ThreadedModExtractor.generate_extraction_id()

        status = ExtractStatus(True, databases, _status_message=f"Extracting {mod_path} databases.", _extract_path=mod_unpack_path)
        self._on_extract_update(status,  extraction_id)

        t = threading.Thread(
            target=self._extract_databases,
            args=[databases, mod_unpack_path, extraction_id],
        )
        
        t.daemon = False
        t.start()
        return extraction_id
