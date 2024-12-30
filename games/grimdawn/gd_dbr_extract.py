import random
from dataclasses import dataclass
from pathlib import Path

from .gd_file_util import PathUtil

from .gd_data import MultiStepProgress

from PyQt6.QtCore import QProcess, qDebug, QTemporaryDir, QRunnable, pyqtSignal, pyqtSlot, QObject

class dbr:
    def __init__(self, relative_path: str, dbdata: dict[str, str]):
        self.relative_path = relative_path

class WorkerSignals(QObject):
    started = pyqtSignal(MultiStepProgress)
    progress = pyqtSignal(MultiStepProgress)
    finished = pyqtSignal(MultiStepProgress)

@dataclass
class ExtractPaths:
    _source_path: Path
    _temp_extract_dir: QTemporaryDir
    _destination_path: Path

    def source_path(self) -> Path: return self._source_path
    def temp_extract_dir(self) -> QTemporaryDir: return self._temp_extract_dir
    def destination_path(self) -> Path: return self._destination_path

class ModExtractor(QObject, QRunnable):
    GameExtractPath: Path
    ModsExtractPath: Path
    
    started = pyqtSignal(MultiStepProgress)
    progress = pyqtSignal(MultiStepProgress)
    finished = pyqtSignal(MultiStepProgress)

    _game_path: Path
    # _data_path: Path
    _database_paths: list[Path]
    _extract_path: Path
    _archive_tool: Path
    # _signals: WorkerSignals
    _EXTRACT_STEPS: int = 3
    _EXTRACT_MESSAGES = [
        "Starting Database Extractions...",
        "Removing Previous Extract(s)",
        "Extracting Databases",
        "Merging Files",
        "Done!"
    ]

    def __init__(self, game_path: Path, database_paths: list[Path], extract_path: Path):
        super().__init__()
        self._game_path = game_path
        self._database_paths = database_paths
        self._extract_path = extract_path
        self._archive_tool = self._game_path.joinpath("ArchiveTool.exe")
        # self.GameExtractPath = self._data_path.joinpath("game_data")
        # self.ModsExtractPath = self._data_path.joinpath("mods")
    

    @staticmethod
    def generate_extraction_id() -> int:
        """
        Generates a new unique extraction id.
        """
        return random.randint(100, 100000) 
    
    def _delete_contents(self, content_directory: Path):
        step_no = 1
        contents = list(Path('.').glob('*'))
        max_progress = len(contents)
        start_signal = MultiStepProgress(0, max_progress, f'Deleting "{content_directory}" contents', step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
        self.progress.emit(start_signal)
        
        progress: int = 0
        for c in contents:
            progress_signal = MultiStepProgress(progress, max_progress, f'Removing "{c}"', step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
            self.progress.emit(progress_signal)
            if c.is_dir():
                PathUtil.delete_contents(c, True)
            else:
                c.unlink()
            progress += 1

        progress_signal = MultiStepProgress(progress, max_progress, f"Removed {progress} files and folders", step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
        self.progress.emit(progress_signal)

    def _merge_extracts(self, database_paths: dict[Path, ExtractPaths]):
        
        max_progress = len(database_paths) - 1
        # # Send signal starting next step
        # step: int = 2
        # start_signal = MultiStepProgress(0, max_progress, "", step, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step])
        # self.progress.emit(start_signal)

        # recreated_dirs: list[Path] = []
        # dirs_cleaned: int = 0
        # for exp in database_paths.values():
        #     prog_msg = f"Deleting contents from {exp.destination_path()}"
        #     delete_signal = MultiStepProgress(dirs_cleaned, max_progress, prog_msg, step, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step])
        #     self.progress.emit(delete_signal)
        #     if exp.destination_path().exists() and exp.destination_path() not in recreated_dirs:
        #         PathUtil.delete_contents(exp.destination_path())
        #     elif not exp.destination_path().exists():
        #         exp.destination_path().mkdir()
        #     dirs_cleaned += 1
        
        # delete_signal = MultiStepProgress(dirs_cleaned, max_progress, "", step, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step])
        # self.progress.emit(delete_signal)
        
        step_no = 3
        moves: int = 0
        for exp in database_paths.values():
            move_signal = MultiStepProgress(moves, max_progress, f"Merging database extract {exp.source_path().name}...", step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
            self.progress.emit(move_signal)
            PathUtil.move_tree(Path(exp.temp_extract_dir().path()), exp.destination_path(), True)
            moves += 1
        
        qDebug(f"Merging extracts complete.")
        move_signal = MultiStepProgress(moves, max_progress, f"Merging complete.", step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
        self.progress.emit(move_signal)
        
    def _on_extract_complete(self, extract_paths: ExtractPaths, remaining_dbs: dict[Path, None], database_paths: dict[Path, ExtractPaths]):
        
        step_no = 2
        qDebug(f"Finished extracting to {extract_paths.temp_extract_dir().path()}")
        
        del remaining_dbs[extract_paths.source_path()]
        max_progress = len(database_paths)
        progress = max_progress - len(remaining_dbs)
        
        # progress_update = Progress(progress, max_progress, f"({progress}/{max_progress}) Extracted database {extract_paths.source_path()}.")
        if (progress < max_progress):
            remaining_names = ", ".join(db.name for db in remaining_dbs)
            status_msg = f"Extracting {remaining_names}"
            progress_signal = MultiStepProgress(progress, max_progress, status_msg, step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
            self.progress.emit(progress_signal)
        else:
            progress_signal = MultiStepProgress(progress, max_progress, "Extraction complete. Preparing to merge.", step_no, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[step_no])
            self.progress.emit(progress_signal)
       
    def _extract_databases(
        self,
        databases: list[Path],
        out_path: Path) -> dict[Path, ExtractPaths]:

        database_extracts: dict[Path, ExtractPaths] = {}
        process_pool: dict[Path, QProcess] = {}
        remaining_dbs: dict[Path, None] = {}
        
        for db in databases:
            database_extracts[db] = ExtractPaths(db, QTemporaryDir(), out_path)
            process_pool[db] = QProcess()
            remaining_dbs[db] = None

        # Signal process started
        start_msg = f"Extracting {", ".join(db.source_path().name for db in database_extracts.values())}"
        progress = MultiStepProgress(0, len(database_extracts), start_msg, 1, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[0])
        self.progress.emit(progress)

        for db in database_extracts:
            process = process_pool[db]
            extract_paths = database_extracts[db]
            # process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            process.finished.connect(lambda exitCode, exitStatus, ex_paths=extract_paths: self._on_extract_complete(ex_paths, remaining_dbs, database_extracts) )
            process.start(str(self._archive_tool.absolute()), [str(extract_paths.source_path().absolute()), "-database", str(extract_paths.temp_extract_dir().path())])
            qDebug(f"Starting extract of {extract_paths.source_path()} to {extract_paths.temp_extract_dir().path()}.")

        for process in process_pool.values():
            process.waitForStarted()
            process.waitForFinished()

        return database_extracts

    @pyqtSlot()
    def run(self):
        qDebug(f'Deleting contents of "{self._extract_path}" directory.')
        self._delete_contents(self._extract_path)
        qDebug(f"Running extracts of {len(self._database_paths)} databases.")
        db_extracts = self._extract_databases(self._database_paths, self._extract_path)
        qDebug(f"Extraction of databases complete. Merging in order.")
        self._merge_extracts(db_extracts)
        finished_signal = MultiStepProgress(1, 1, "", self._EXTRACT_STEPS, self._EXTRACT_STEPS, self._EXTRACT_MESSAGES[4])
        self.finished.emit(finished_signal)
        
    # @pyqtSlot()
    # def extract_databases(self,
    #     database_paths: list[Path],
    #     mod_extract_folder: str,
    #     extraction_id: Optional[int]) -> int:
    #     """
    #     Extracts the databases in a background thread to a subfolder of the ModsExtractPath.

    #     Args:
    #         database_paths (set[Path]): The absolute paths to the databases to extract.
    #         mod_extract_folder (str): The mod folder name to extract the databases to. This will be a subfolder of the ModsExtractPath path.
    #         extraction_id (Optional[int]): An optional id to track the extraction progress. If not provided, a new id will be generated.
    #     Returns:
    #         extraction_id: The extraction id assigned to this extraction process.
    #     """
    #     absolute_out_path = self.ModsExtractPath.joinpath(mod_extract_folder)
    #     if not extraction_id:
    #         extraction_id = self.generate_extraction_id()

    #     self._extract_databases(database_paths, absolute_out_path, extraction_id)

    #     return extraction_id
    
    # @pyqtSlot()
    # def extract_grimdawn(self, extraction_id: Optional[int]) -> int:
    #     """
    #     Extracts the Grim Dawn databases from the game to the GameExtractPath in a background thread.

    #     Args:
    #         extraction_id (Optional[int]): An optional id to track the extraction progress. If not provided, a new id will be generated.

    #     Returns:
    #         extraction_id: The extraction id assigned to this extraction process.
    #     """
    #     databases = [
    #         Path(self._game_path, "database", "database.arz"),
    #         Path(self._game_path, "survivalmode1", "database", "SurvivalMode1.arz"),
    #         Path(self._game_path, "survivalmode2", "database", "SurvivalMode2.arz"),
    #         Path(self._game_path, "gdx1", "database", "GDX1.arz"),
    #         Path(self._game_path, "gdx2", "database", "GDX2.arz")
    #     ]

    #     db_extract_path = self.GameExtractPath.joinpath("database")
    #     if not extraction_id:
    #         extraction_id = self.generate_extraction_id()

    #     self._extract_databases(databases, db_extract_path, extraction_id)
 
    #     return extraction_id