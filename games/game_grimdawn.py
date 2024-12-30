import shutil
from pathlib import Path
import datetime
from typing import override

from PyQt6.QtWidgets import QMainWindow
from mobase import (
    ExecutableForcedLoadSetting,
    ExecutableInfo,
    # FileTreeEntry,
    IModInterface,
    # ModDataChecker,
    # IFileTree,
    IOrganizer,
    ModState,
)
from PyQt6.QtCore import QDir, QFileInfo, QThread, qDebug, qInfo  # , qFatal, qCritical, qWarning

from ..basic_game import BasicGame
from .grimdawn import GrimDawnModDataChecker, ExtractStatus, ModExtractor, ThreadedModExtractor, QtModExtractor, ExtractProgressDialog, GdProgressDialog, HashUtil, PathUtil



class GrimDawnGame(BasicGame):
    Name = "Grim Dawn Support Plugin"
    Author = "ModifAmorphic"
    Version = "0.0.1"
    GameName = "Grim Dawn"
    GameShortName = "grimdawn"
    GameBinary = "Grim Dawn.exe"
    GameDataPath = ""
    GameSteamId = 219990
    GameDocumentsDirectory = "%DOCUMENTS%/My Games/Grim Dawn/"
    GameIniFiles = "%GAME_DOCUMENTS%/Settings/options.txt"
    GameSavesDirectory = "%GAME_DOCUMENTS%/save"
    GameSaveExtension = "gdc"

    _libraries = ["DPYes.dll"]
    _organizer: IOrganizer
    _mo_main_window: QMainWindow

    # def __init__(self):
    #     super(GrimDawnGame, self).__init__()
    #     print("GrimDawnGame.__init__(self)")

    #####     BasicGame / IPluginGame Overrides     #####
    @override
    def init(self, organizer: IOrganizer) -> bool:
        super().init(organizer)
        
        self._organizer = organizer
        
        qDebug("Registering feature GrimDawnModDataChecker()")
        self._register_feature(GrimDawnModDataChecker())
        qInfo(
            f"{self.GameName} plugin init. basePath: {organizer.basePath()}, Data directory: {self.dataDirectory().absolutePath()}, PluginDataPath: {organizer.pluginDataPath()}, downloadsPath: {organizer.downloadsPath()}"
        )

        self._game_data_path = Path(organizer.pluginDataPath()).joinpath(self.GameShortName)
        self._mods_unpack_path = self._game_data_path.joinpath("mods")
        self._db_dir = self._game_data_path.joinpath("game_data", "database")
        self._resources_dir = self._game_data_path.joinpath("game_data", "resources")
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._resources_dir.mkdir(parents=True, exist_ok=True)
        self._extractor = ThreadedModExtractor(
                Path(self.gameDirectory().absolutePath()),
                self._game_data_path
            )
        organizer.onUserInterfaceInitialized(self._onUserInterfaceInitialized)
        # organizer.onAboutToRun(self._onAboutToRun)
        organizer.modList().onModStateChanged(self._onModStateChanged)
        organizer.modList().onModInstalled(self._onModInstalled)
        organizer.modList().onModRemoved(self._onModRemoved)
        # organizer.onPluginEnabled(mobase.WizardInstaller)

        return True
    
    @override
    def executables(self):
        return [
            # ExecutableInfo(
            #     "Grim Dawn (x64)",
            #     QFileInfo(os.path.join(self.gameDirectory().absolutePath(), "x64", self.binaryName())),
            # ).withArgument("/basemods"),
            ExecutableInfo(
                "Grim Dawn",
                QFileInfo(self.gameDirectory().absoluteFilePath(self.binaryName())),
            ).withArgument("/x64"),
            ExecutableInfo(
                "Grim Dawn (Merge Mods)",
                QFileInfo(self.gameDirectory().absoluteFilePath(self.binaryName())),
            )
            .withArgument("/x64")
            .withArgument("/basemods"),
            ExecutableInfo(
                "Grim Dawn (32bit)",
                QFileInfo(self.gameDirectory().absoluteFilePath(self.binaryName())),
            ),
            ExecutableInfo(
                "Grim Dawn (32bit, Merge Mods)",
                QFileInfo(self.gameDirectory().absoluteFilePath(self.binaryName())),
            ).withArgument("/basemods"),
        ]
    
    @override
    def executableForcedLoads(self) -> list[ExecutableForcedLoadSetting]:
        return [
            ExecutableForcedLoadSetting(self.binaryName(), library).withEnabled(True)
            for library in self._libraries
        ]

    #####     Private Methods     #####
    def _onUserInterfaceInitialized(self, main_window: QMainWindow):
        self._mo_main_window = main_window
        self._extract_grim_dawn(main_window)
        return
        self._unpack_gd_dbs_qt(self._mo_main_window)
        return
        extraction_id = ThreadedModExtractor.generate_extraction_id()
        qInfo(f"Unpacking {self.GameName} databases to {self._extractor.GameExtractPath}.")
        progress_window = ExtractProgressDialog(main_window, extraction_id)
        self._extractor.on_extract_update(progress_window.on_extract_update, extraction_id)
        self._extractor.on_extract_update(self._on_extract_update, extraction_id)        
        
        self._extractor.extract_grimdawn(extraction_id)
    
    # When a new mod is installed, extract everything and..
    # - for databases: create "diff" files that only include changes from the unmodded game files
    def _onModInstalled(self, mod: IModInterface):
        mod_unpack_path = self._mods_unpack_path.joinpath(mod.name())
        mod_unpack_path.mkdir(parents=True, exist_ok=True)
        qInfo(f"Mod {mod.name()} installed. Unpacking mod files to {mod_unpack_path}")
        extraction_id = ThreadedModExtractor.generate_extraction_id()

        if hasattr(self, '_mo_main_window'):
            progress_window = ExtractProgressDialog(self._mo_main_window, extraction_id)
            self._extractor.on_extract_update(progress_window.on_extract_update, extraction_id)
            self._extractor.on_extract_update(self._on_extract_update, extraction_id)
            self._extractor.extract_mod_databases(Path(mod.absolutePath()), mod_unpack_path, extraction_id)
            progress_window.done
        else:
            qInfo("Main window not initialized. Writing progress to logs.")
            self._extractor.on_extract_update(self._on_extract_update, extraction_id)
            self._extractor.extract_mod_databases(Path(mod.absolutePath()), mod_unpack_path, extraction_id)

        # qDebug(f"{datetime.datetime.now().time()}: Calculating checksum for mod directory {mod.absolutePath()}")
        # mod_hash = ModHash.hash_directory(mod_unpack_path, recursive=True)
        

    def _on_extract_update(self, extract_status: ExtractStatus, extraction_id: int):
        qDebug(f"Progress: {extract_status.progress()}/{extract_status.max_progress()}, Message: {extract_status.status_message()}")
          
        if not extract_status.is_running():
            qInfo(f"Extraction complete: {extract_status.status_message()}")
            qDebug(f"Calculating checksum for mod directory {extract_status.extract_path()}")
            mod_hash = HashUtil.hash_directory(extract_status.extract_path(), recursive=True)
            qDebug(f"Hash: {mod_hash.hexdigest()}")

    def _onModRemoved(self, mod_name: str):
        qInfo(f"Mod {mod_name} removed")
        mod_unpack_path = self._mods_unpack_path.joinpath(mod_name)
        if mod_unpack_path.exists():
            shutil.rmtree(mod_unpack_path)
        # TODO: Cleanup

    # When a mod is activated,
    def _onModStateChanged(self, mod_states: dict[str, ModState]):
        for m in mod_states.keys():
            # modstate: ModState = mod_states[m]
            if mod_states[m] & ModState.ACTIVE:
                qInfo(f"Mod: {m}, State: {mod_states[m]} (ACTIVE)")
            else:
                qInfo(f"Mod: {m}, State: {mod_states[m]}")

    def _onAboutToRun(self, app_path_str: str, wd: QDir, args: str) -> bool:
        qInfo(f"onAboutToRun app_path_str={app_path_str}, wd={wd}, args={args}")
        return True
    
    # def savesDirectory(self):
    #     return QDir(self.documentsDirectory().absoluteFilePath("gamesaves"))
    def _extract_grim_dawn(self, main_window: QMainWindow):
        game_path = Path(self.gameDirectory().absolutePath())
        database_paths = [
            game_path.joinpath("database", "database.arz"),
            game_path.joinpath("survivalmode1", "database", "SurvivalMode1.arz"),
            game_path.joinpath("survivalmode2", "database", "SurvivalMode2.arz"),
            game_path.joinpath("gdx1", "database", "GDX1.arz"),
            game_path.joinpath("gdx2", "database", "GDX2.arz")
        ]
        extract_path = self._game_data_path.joinpath("game_data", "database")
        self._extractor = ModExtractor(game_path, database_paths, extract_path)
        
        progress_window = GdProgressDialog(main_window, allowCancel=False, delayCloseMsec=500)
        # Thread setup
        self._thread = QThread(main_window)
        self._extractor.moveToThread(self._thread)
        self._thread.started.connect(self._extractor.run)
        # cleanup thread and extractor when finished
        self._extractor.finished.connect(self._extractor.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # hook up the progress steps
        # self._extractor.started.connect(progress_window.on_step_update)
        self._extractor.progress.connect(progress_window.on_step_update)
        self._extractor.finished.connect(progress_window.on_steps_finished)
        qInfo(f"Unpacking {self.GameName} databases to {extract_path}.")
        self._thread.start()
        # task.moveToThread(thread)
    def _unpack_gd_dbs_qt(self, main_window: QMainWindow):
        self._mo_main_window = main_window
        # progress_window = ExtractProgressDialog(main_window, 0)
        extraction_id = QtModExtractor.generate_extraction_id()
        progress_window = ExtractProgressDialog(main_window, extraction_id)
        self._qtextractor = QtModExtractor(
            Path(self.gameDirectory().absolutePath()), self._game_data_path)
        self._qtextractor.on_extract_update(progress_window.on_progress_update, extraction_id)
        # self._extractor.on_extract_update(self._on_extract_update, extraction_id)    
        qInfo(f"Unpacking {self.GameName} databases to {self._qtextractor.GameExtractPath}.")
        self._qtextractor.extract_grimdawn(extraction_id)