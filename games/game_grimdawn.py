import shutil
from hashlib import blake2b
from pathlib import Path
from typing import override

from mobase import (
    ExecutableForcedLoadSetting,
    ExecutableInfo,
    IModInterface,
    IOrganizer,
    ModState,
)
from PyQt6.QtCore import QDir, QFileInfo, QTimer, qDebug, qInfo
from PyQt6.QtWidgets import QMainWindow

from ..basic_game import BasicGame
from .grimdawn import (
    GD,
    GdProgressDialog,
    GrimDawnModDataChecker,
    HashUtil,
    ModExtractor,
    SimpleTask,
    TaskMaster,
)


class GrimDawnGame(BasicGame):
    _gd: GD
    Name = GD.PLUGIN_NAME
    Author = GD.PLUGIN_AUTHOR
    Version = GD.PLUGIN_VERSION
    GameName = GD.GAME_NAME
    GameShortName = GD.GAME_SHORT_NAME
    GameBinary = GD.GD_BINARY
    GameDataPath = GD.DATA_PATH
    GameSteamId = GD.STEAM_ID
    GameDocumentsDirectory = GD.DOC_DIRECTORY
    GameIniFiles = ", ".join(GD.INI_FILES)
    GameSavesDirectory = GD.SAVE_DIR
    GameSaveExtension = GD.GAME_SAVE_EXT

    _organizer: IOrganizer
    _mo_main_window: QMainWindow
    _task_masters: list[TaskMaster]
    _tm_monitor: QTimer

    # def __init__(self):
    #     super(GrimDawnGame, self).__init__()

    #####     BasicGame / IPluginGame Overrides     #####
    @override
    def init(self, organizer: IOrganizer) -> bool:
        super().init(organizer)

        self._organizer = organizer
        self._gd = GD(
            self.gameDirectory().absolutePath(),
            str(Path(organizer.pluginDataPath()).joinpath(self.GameShortName)),
        )
        self._task_masters: list[TaskMaster] = []
        qDebug("Registering feature GrimDawnModDataChecker()")
        self._register_feature(GrimDawnModDataChecker())
        qInfo(
            f"{self.GameName} plugin init. basePath: {organizer.basePath()}, Data directory: {self.dataDirectory().absolutePath()}, PluginDataPath: {organizer.pluginDataPath()}, downloadsPath: {organizer.downloadsPath()}"
        )

        self._gd.GAME_ROOT_EXTRACT_PATH().mkdir(parents=False, exist_ok=True)
        self._gd.GAME_DATA_EXTRACT_PATH().mkdir(parents=False, exist_ok=True)
        self._gd.MODS_DATA_EXTRACT_PATH().mkdir(parents=False, exist_ok=True)
        organizer.onUserInterfaceInitialized(self._onUserInterfaceInitialized)
        # organizer.onAboutToRun(self._onAboutToRun)
        organizer.modList().onModStateChanged(self._onModStateChanged)
        organizer.modList().onModInstalled(self._onModInstalled)
        organizer.modList().onModRemoved(self._onModRemoved)

        self._tm_monitor = QTimer()
        self._tm_monitor.timeout.connect(self._gc_task_managers)  # type: ignore
        self._tm_monitor.start(1000)
        return True

    def _gc_task_managers(self):
        finished = [tm for tm in self._task_masters if tm.is_finished()]
        self._task_masters = [tm for tm in self._task_masters if not tm.is_finished()]
        # for tm in finished:
        #     tm.task().deleteLater()
        #     tm.thread().deleteLater()

        f_count = len(finished)
        if f_count:
            qDebug(f"Removed references to {f_count} TaskMaster instances.")

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
            for library in GD.FORCED_LIBRARIES
        ]

    # def savesDirectory(self):
    #     return QDir(self.documentsDirectory().absoluteFilePath("gamesaves"))

    #####     Private Methods     #####
    def _onUserInterfaceInitialized(self, main_window: QMainWindow):
        self._mo_main_window = main_window
        self._extract_grim_dawn(main_window)

    # When a new mod is installed, extract everything and..
    # - for databases: create "diff" files that only include changes from the unmodded game files
    def _onModInstalled(self, mod: IModInterface):
        mod_path = Path(mod.absolutePath())
        mod_unpack_path = self._gd.MODS_DATA_EXTRACT_PATH().joinpath(mod.name())
        mod_unpack_path.mkdir(parents=False, exist_ok=True)
        qInfo(f"Mod {mod.name()} installed. Unpacking mod files to {mod_unpack_path}")
        databases: list[Path] = []
        for db in mod_path.glob("mods/*/database/*.arz", case_sensitive=False):
            databases.append(db)

        extractor = ModExtractor(self._gd.GAME_DIRECTORY(), databases, mod_unpack_path)
        progress_dialog = GdProgressDialog(
            self._mo_main_window,
            allowCancel=False,
            delayCloseMsec=500,
            delayShowMsec=0,
            autoClose=False,
        )
        task_master = TaskMaster(extractor, progress_dialog=progress_dialog)
        # self.progress_dialog.closed.connect(self._unload_task_master)
        task_master.task().finished_connect(lambda: self._create_hash(mod_unpack_path))
        task_master.start_task()
        self._task_masters.append(task_master)

    def _create_hash(self, mod_unpack_path: Path):
        hash_dialog = GdProgressDialog(
            self._mo_main_window,
            allowCancel=False,
            delayCloseMsec=500,
            delayShowMsec=0,
            autoClose=False,
        )
        simple_task = SimpleTask(
            lambda: HashUtil.hash_directory(mod_unpack_path, recursive=True),
            f"Calculating checksum for mod {mod_unpack_path}",
            progress_dialog=hash_dialog,
        )
        self._task_masters.append(simple_task)
        simple_task.result_connect(self._write_hash)
        simple_task.start_task()

    def _write_hash(self, hash: blake2b):
        qDebug(f"Hash: {hash.hexdigest()}")

    def _onModRemoved(self, mod_name: str):
        qInfo(f"Mod {mod_name} removed")
        mod_unpack_path = self._gd.MODS_DATA_EXTRACT_PATH().joinpath(mod_name)
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

    def _extract_grim_dawn(self, main_window: QMainWindow):
        extractor = ModExtractor(
            self._gd.GAME_DIRECTORY(),
            self._gd.GAME_DATABASE_PATHS(),
            self._gd.GAME_DB_EXTRACT_PATH(),
        )
        progress_dialog = GdProgressDialog(
            self._mo_main_window,
            allowCancel=False,
            delayCloseMsec=500,
            delayShowMsec=0,
            autoClose=False,
        )
        task_master = TaskMaster(extractor, progress_dialog=progress_dialog)
        task_master.start_task()
        self._task_masters.append(task_master)
