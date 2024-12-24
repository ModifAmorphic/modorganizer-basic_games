from os import path, PathLike
from pathlib import Path
import shutil
from typing import (
    Sequence,
    Union
 )
import PyQt6.QtWidgets
from PyQt6.QtCore import QDir, QFileInfo, qFatal, qCritical, qWarning, qInfo, qDebug
import mobase
from mobase import (
    ModDataChecker,
    IFileTree,
    IOrganizer,
    FileTreeEntry,
    IModInterface,
    ModState,
    ExecutableInfo,
    ExecutableForcedLoadSetting
)
from ..basic_game import BasicGame
from ..basic_features import BasicModDataChecker, GlobPatterns
from .grimdawn import dbrs
import fnmatch
from .grimdawn.mod_data_checker import GrimDawnModDataChecker

# from datetime import datetime

class GrimDawnBaseMods(mobase.UnmanagedMods):
    _base_mods = {  
        'survivalmode': 'survivalmode',
        'survivalmode1': 'survivalmode1',
        'survivalmode2': 'survivalmode2',
        'gtx1': 'Ashes of Malmouth',
        'gtx2': 'Forgotten Gods',
    }
    def displayName(self, mod_name: str) -> str:
        if mod_name in self._base_mods:
            return self._base_mods[mod_name]
        return ""
    def referenceFile(self, mod_name: str) -> str:
        return ""
    def mods(self, official_only: bool) -> Sequence[str]:
        return ["survivalmode", "survivalmode1", "survivalmode2"]
    def secondaryFiles(self, mod_name: str) -> Sequence[Union[str, PathLike[str], QFileInfo]]:
        return []


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
        pattern = fnmatch.translate("*.tex")
        qDebug(f"Pattern: {pattern}")
        # self._register_feature(
        #     BasicModDataChecker(
        #         GlobPatterns(
        #             # unfold=[
        #             #     "database",
        #             #     "resources"
        #             # ],
        #             valid=[
        #                 "database",
        #                 "resources",
        #                 "*.arz",
        #                 "*.arc",
        #                 "DPYes.dll",
        #                 "settings"
        #             ],
        #             delete=[
        #                 "*.dbr",
        #                 "*.tex",
        #                 "caravaner",
        #                 "records"
        #             ],
        #             # move={
        #             #     "DPYes.dll": ".",
        #             #     "*.arz": "mods/database/",
        #             #     "*.arc": "mods/resources/"
        #             # },
        #         )
        #     )
        # )
        # self._register_feature(GrimDawnBaseMods())
        qInfo(f"{self.GameName} plugin init. basePath: {organizer.basePath()}, Data directory: {self.dataDirectory().absolutePath()}, PluginDataPath: {organizer.pluginDataPath()}, downloadsPath: {organizer.downloadsPath()}")
        # with open(os.path.join(organizer.basePath(), "grimdawn.log"), "a") as logfile:
        #     ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #     logfile.write(f"{ts}: Grim Dawn plugin init\n")
        self._game_data_path = path.join(organizer.pluginDataPath(), self.GameShortName)
        self._mods_unpack_path = path.join(self._game_data_path, "mods")
        self._db_dir = path.join(self._game_data_path, "game_data", "database")
        self._resources_dir = path.join(self._game_data_path, "game_data", "resources")
        Path(self._db_dir).mkdir(parents=True,exist_ok=True)
        Path(self._resources_dir).mkdir(parents=True,exist_ok=True)
        # organizer.onUserInterfaceInitialized(self.unpack)
        # organizer.onAboutToRun(self._onAboutToRun)
        # organizer.modList().onModStateChanged(self._onModStateChanged)
        # organizer.modList().onModInstalled(self._onModInstalled)
        # organizer.modList().onModRemoved(self._onModRemoved)
        # organizer.onPluginEnabled(mobase.WizardInstaller)
        
        return True
    # When a new mod is installed, extract everything and..
    # - for databases: create "diff" files that only include changes from the unmodded game files
    def _onModInstalled(self, mod: IModInterface):
        qInfo(f"Mod {mod.name()} installed")
        mod_unpack_path = path.join(self._mods_unpack_path, mod.name())
        Path(mod_unpack_path).mkdir(parents=True,exist_ok=True)
            # ft = mod.fileTree()
            # entry = ft.find("**/*.arz")

        # TODO: Extract mod databases and resources

    def _onModRemoved(self, mod_name: str):
        qInfo(f"Mod {mod_name} removed")
        mod_unpack_path = path.join(self._mods_unpack_path, mod_name)
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
        extractor = dbrs.ModExtractor(self.gameDirectory().absolutePath(), self._game_data_path)
        qInfo(f"Unpacking {self.GameName} databases to {extractor.GameExtractPath}")
        extractor.extract_grimdawn(self.on_extractor_update)

    #TODO: Remove this once the callers can handle their own events
    def on_extractor_update(self, status: dbrs.ExtractStatus):
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
            ).withArgument("/x64").withArgument("/basemods"),
            ExecutableInfo(
                "Grim Dawn (32bit)",
                QFileInfo(self.gameDirectory().absoluteFilePath(self.binaryName())),
            ),
            ExecutableInfo(
                "Grim Dawn (32bit, Merge Mods)",
                QFileInfo(self.gameDirectory().absoluteFilePath(self.binaryName())),
            ).withArgument("/basemods")
        ]
    
    def executableForcedLoads(self) -> list[ExecutableForcedLoadSetting]:
        return [
            ExecutableForcedLoadSetting(self.binaryName(), library).withEnabled(True)
            for library in self._libraries
        ]
    # def savesDirectory(self):
    #     return QDir(self.documentsDirectory().absoluteFilePath("gamesaves"))