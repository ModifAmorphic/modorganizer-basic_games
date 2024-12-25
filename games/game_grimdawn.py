import shutil
from os import path
from pathlib import Path

import PyQt6.QtWidgets
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
from PyQt6.QtCore import QDir, QFileInfo, qDebug, qInfo  # , qFatal, qCritical, qWarning

from ..basic_game import BasicGame
from .grimdawn import ExtractStatus, GrimDawnModDataChecker, ModExtractor


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

    # def __init__(self):
    #     super(GrimDawnGame, self).__init__()
    #     print("GrimDawnGame.__init__(self)")

    def init(self, organizer: IOrganizer) -> bool:
        super().init(organizer)
        qDebug("Registering feature GrimDawnModDataChecker()")
        self._register_feature(GrimDawnModDataChecker())
        qInfo(
            f"{self.GameName} plugin init. basePath: {organizer.basePath()}, Data directory: {self.dataDirectory().absolutePath()}, PluginDataPath: {organizer.pluginDataPath()}, downloadsPath: {organizer.downloadsPath()}"
        )

        self._game_data_path = path.join(organizer.pluginDataPath(), self.GameShortName)
        self._mods_unpack_path = path.join(self._game_data_path, "mods")
        self._db_dir = path.join(self._game_data_path, "game_data", "database")
        self._resources_dir = path.join(self._game_data_path, "game_data", "resources")
        Path(self._db_dir).mkdir(parents=True, exist_ok=True)
        Path(self._resources_dir).mkdir(parents=True, exist_ok=True)

        # organizer.onUserInterfaceInitialized(self.unpack)
        # organizer.onAboutToRun(self._onAboutToRun)
        organizer.modList().onModStateChanged(self._onModStateChanged)
        organizer.modList().onModInstalled(self._onModInstalled)
        organizer.modList().onModRemoved(self._onModRemoved)
        # organizer.onPluginEnabled(mobase.WizardInstaller)

        return True

    # When a new mod is installed, extract everything and..
    # - for databases: create "diff" files that only include changes from the unmodded game files
    def _onModInstalled(self, mod: IModInterface):
        qInfo(f"Mod {mod.name()} installed. Unpacking mod files")
        mod_unpack_path = path.join(self._mods_unpack_path, mod.name())
        Path(mod_unpack_path).mkdir(parents=True, exist_ok=True)
        # ft = mod.fileTree()
        # entry = ft.find("**/*.arz")

        # TODO: Extract mod databases and resources

    def _onModRemoved(self, mod_name: str):
        qInfo(f"Mod {mod_name} removed")
        mod_unpack_path = path.join(self._mods_unpack_path, mod_name)
        if Path(mod_unpack_path).exists():
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

    def unpack(self, main_window: PyQt6.QtWidgets.QMainWindow):
        # dbrs.extract_grimdawn(self.gameDirectory().absolutePath(), self._db_dir)
        extractor = ModExtractor(
            self.gameDirectory().absolutePath(), self._game_data_path
        )
        qInfo(f"Unpacking {self.GameName} databases to {extractor.GameExtractPath}")
        extractor.extract_grimdawn(self.on_extractor_update)

    # TODO: Remove this once the callers can handle their own events
    def on_extractor_update(self, status: ExtractStatus):
        qInfo(status.status())

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

    def executableForcedLoads(self) -> list[ExecutableForcedLoadSetting]:
        return [
            ExecutableForcedLoadSetting(self.binaryName(), library).withEnabled(True)
            for library in self._libraries
        ]

    # def savesDirectory(self):
    #     return QDir(self.documentsDirectory().absoluteFilePath("gamesaves"))
