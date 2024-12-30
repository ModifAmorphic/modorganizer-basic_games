import random
from dataclasses import dataclass
from typing import Optional, Protocol, Union
from pathlib import Path

from .gd_file_util import PathUtil

from .gd_data import Progress

from PyQt6.QtCore import QProcess, qDebug, QTemporaryDir, QThreadPool

class dbr:
    def __init__(self, relative_path: str, dbdata: dict[str, str]):
        self.relative_path = relative_path

@dataclass
class ExtractPaths:
    _source_path: Path
    _temp_extract_dir: QTemporaryDir
    _destination_path: Path
    _process: QProcess
    _extraction_id: int

    def source_path(self) -> Path: return self._source_path
    def temp_extract_dir(self) -> QTemporaryDir: return self._temp_extract_dir
    def destination_path(self) -> Path: return self._destination_path
    def process(self) -> QProcess: return self._process
    def extraction_id(self) -> int: return self._extraction_id

class ExtractUpdate(Protocol):
    def __call__(self, progress_update: Progress, extraction_id: int) -> None: ...

class QtModExtractor:
    GameExtractPath: Path
    ModsExtractPath: Path

    _game_path: Path
    _data_path: Path
    _archive_tool: Path
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
            subscriber (ExtractUpdate): The subscribed callback function to execute when an extraction update is available.
            extraction_id (Union[int, None]): An optional id to track the extraction progress. If provided, the subscriber will only be called for update events with a matching extraction_id.
            all_updates (bool): An optional flag to enable calls for every update, regardless of extraction_id. Defaults to False
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
    
    def _send_extract_update(self, extract_progress: Progress, extraction_id: int):
        qDebug(f"Sending update to all subscribers of extraction_id {extraction_id}. Update: {extract_progress.status_message()}")
        for subscriber in self._update_callbacks:
            ids = self._update_callbacks[subscriber][0]
            all_updates = self._update_callbacks[subscriber][1]
            if extraction_id in ids or all_updates:
                qDebug(f"Sending update to subscriber {subscriber}")
                subscriber(extract_progress, extraction_id)
    
    def _merge_extracts(self, database_paths: dict[Path, ExtractPaths], extraction_id: int):
        max_progress = len(database_paths)
        recreated_dirs: list[Path] = []
        dirs_cleaned: int = 0
        for exp in database_paths.values():
            if exp.destination_path().exists() and exp.destination_path() not in recreated_dirs:
                PathUtil.delete_contents(exp.destination_path())
            elif not exp.destination_path().exists():
                exp.destination_path().mkdir()
            dirs_cleaned += 1
            cleanup_progress = Progress(dirs_cleaned, max_progress, f"({dirs_cleaned}/{max_progress}) Removing previous extract(s)...")
            self._send_extract_update(cleanup_progress, extraction_id)
        
        moves: int = 0
        for exp in database_paths.values():
            move_progress = Progress(moves, max_progress, f"({moves}/{max_progress}) Merging database extract {exp.source_path().name}...")
            self._send_extract_update(move_progress, extraction_id)
            PathUtil.move_tree(Path(exp.temp_extract_dir().path()), exp.destination_path(), True)
            moves += 1
        move_progress = Progress(moves, max_progress, f"({moves}/{max_progress}) Merging extracts complete")
        qDebug(f"Merging extracts complete.")
        self._send_extract_update(move_progress, extraction_id)

    def _on_all_extracts_complete(self, database_paths: dict[Path, ExtractPaths], extraction_id: int):
        qDebug(f"Extraction of databases complete. Merging in order.")
        max_progress = len(database_paths)
        progress_start = Progress(0, max_progress, f"Extraction of databases complete. Removing previous extracts and merging.")
        self._send_extract_update(progress_start, extraction_id)
        
        self._pool = QThreadPool()
        self._pool.start(lambda: self._merge_extracts(database_paths, extraction_id))
        #TODO: Run in background
        # runnable = QRunnable.create(lambda: self._merge_extracts(database_paths, extraction_id))
        # if runnable is not None:
        #     runnable.run()
        # self._merge_extracts(database_paths, extraction_id)
    
    def _run_somethin(self):
        print("I ran")
    def _on_extract_complete(self, extract_paths: ExtractPaths, remaining_dbs: dict[Path, None], database_paths: dict[Path, ExtractPaths]):
        qDebug(f"Finished extracting to {extract_paths.temp_extract_dir().path()}")
        
        del remaining_dbs[extract_paths.source_path()]
        max_progress = len(database_paths)
        progress = max_progress - len(remaining_dbs)
        
        progress_update = Progress(progress, max_progress, f"({progress}/{max_progress}) Extracted database {extract_paths.source_path()}.")
        self._send_extract_update(progress_update, extract_paths.extraction_id())
        
        if progress == max_progress:
            self._on_all_extracts_complete(database_paths, extract_paths.extraction_id())
        
    def _extract_databases(
        self,
        databases: list[Path],
        out_path: Path,
        extraction_id: int):
        
        database_paths: dict[Path, ExtractPaths] = {}
        remaining_dbs: dict[Path, None] = {}
        
        for db in databases:
            database_paths[db] = ExtractPaths(db, QTemporaryDir(), out_path, QProcess(), extraction_id)
            remaining_dbs[db] = None

        for extract_paths in database_paths.values():
            process = extract_paths.process()
            # process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            process.finished.connect(lambda exitCode, exitStatus, ex_paths=extract_paths: self._on_extract_complete(ex_paths, remaining_dbs, database_paths) )
            process.start(str(self._archive_tool.absolute()), [str(extract_paths.source_path().absolute()), "-database", str(extract_paths.temp_extract_dir().path())])
            qDebug(f"Starting extract of {extract_paths.source_path()} to {extract_paths.temp_extract_dir().path()}.")

    def extract_databases(self,
        database_paths: list[Path],
        mod_extract_folder: str,
        extraction_id: Optional[int]) -> int:
        """
        Extracts the databases in a background thread to a subfolder of the ModsExtractPath.

        Args:
            database_paths (set[Path]): The absolute paths to the databases to extract.
            mod_extract_folder (str): The mod folder name to extract the databases to. This will be a subfolder of the ModsExtractPath path.
            extraction_id (Optional[int]): An optional id to track the extraction progress. If not provided, a new id will be generated.
        Returns:
            extraction_id: The extraction id assigned to this extraction process.
        """
        absolute_out_path = self.ModsExtractPath.joinpath(mod_extract_folder)
        if not extraction_id:
            extraction_id = self.generate_extraction_id()

        self._extract_databases(database_paths, absolute_out_path, extraction_id)

        return extraction_id
    
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

        db_extract_path = self.GameExtractPath.joinpath("database")
        if not extraction_id:
            extraction_id = self.generate_extraction_id()

        self._extract_databases(databases, db_extract_path, extraction_id)
 
        return extraction_id