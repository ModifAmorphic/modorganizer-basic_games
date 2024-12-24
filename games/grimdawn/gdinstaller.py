from typing import List, Union
import mobase
from mobase import IPluginInstallerSimple, GuessedString, InstallResult, IFileTree
import metadata

class GrimDawnInstaller(IPluginInstallerSimple):
    def author(self) -> str:
        return metadata.Author
    def description(self) -> str:
        return ""
    def enabledByDefault(self) -> bool:
        return True
    def name(self) -> str:
        return f"{metadata.GameName} Installer"
    def localizedName(self) -> str:
        return f"{metadata.GameName} Installer"
    def version(self) -> mobase.VersionInfo:
         return mobase.VersionInfo(value=metadata.Version,scheme=mobase.VersionScheme.DISCOVER)

    def __init__(self):
        super().__init__()  # You need to call this manually.

    def init(self, organizer: mobase.IOrganizer):
        self._organizer = organizer
        return True
    
    def isActive(self) -> bool:
        return bool(self._organizer.pluginSetting(self.name(), "enabled"))
    def isArchiveSupported(self, tree: mobase.IFileTree):
        return True
    def isManualInstaller(self) -> bool:
        return False
    def priority(self) -> int:
        return 100
    
    def settings(self) -> List[mobase.PluginSetting]:
        return [
            mobase.PluginSetting("enabled", "enable this plugin", True)
        ]
    # def install(self: IPluginInstallerSimple, name: GuessedString, tree: IFileTree, version: str, nexus_id: int) -> Union[InstallResult, IFileTree, tuple[InstallResult, IFileTree, str, int]]:
        