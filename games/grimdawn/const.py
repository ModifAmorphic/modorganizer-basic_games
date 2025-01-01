from pathlib import Path


class GD:
    PLUGIN_NAME = "Grim Dawn Support Plugin"
    PLUGIN_AUTHOR = "ModifAmorphic"
    PLUGIN_VERSION = "0.0.1"
    GAME_NAME = "Grim Dawn"
    GAME_SHORT_NAME = "grimdawn"
    GD_BINARY = "Grim Dawn.exe"
    DATA_PATH = ""
    STEAM_ID = 219990
    GAME_SAVE_EXT = "gdc"
    FORCED_LIBRARIES = ["DPYes.dll"]
    DOC_DIRECTORY = "%DOCUMENTS%/My Games/Grim Dawn/"
    INI_FILES = "%GAME_DOCUMENTS%/Settings/options.txt"
    SAVE_DIR = "%GAME_DOCUMENTS%/save"
    GAME_DATABASES = [
        str(Path("database").joinpath("database.arz")),
        str(Path("survivalmode1").joinpath("database", "SurvivalMode1.arz")),
        str(Path("survivalmode2").joinpath("database", "SurvivalMode2.arz")),
        str(Path("gdx1").joinpath("database", "GDX1.arz")),
        str(Path("gdx2").joinpath("database", "GDX2.arz")),
    ]

    _game_dir: Path
    _root_extract_dir: Path
    _game_db_paths: list[Path]
    _game_extract_path: Path
    _game_db_extract_path: Path
    _game_resources_extract_path: Path
    _mods_extract_path: Path

    def __init__(self, game_dir: str, root_extract_dir: str):
        self._game_dir = Path(game_dir)
        self._root_extract_dir = Path(root_extract_dir)
        self._set_paths()

    def _set_paths(self):
        self._game_db_paths = [self._game_dir.joinpath(db) for db in GD.GAME_DATABASES]
        self._game_extract_path = self._root_extract_dir.joinpath("game_data")
        self._game_db_extract_path = self._game_extract_path.joinpath("database")
        self._game_resources_extract_path = self._game_extract_path.joinpath(
            "resources"
        )
        self._mods_extract_path = self._root_extract_dir.joinpath("mods")

    def GAME_DIRECTORY(self):
        return self._game_dir

    def GAME_DATABASE_PATHS(self):
        return self._game_db_paths

    def GAME_ROOT_EXTRACT_PATH(self):
        return self._root_extract_dir

    def GAME_DATA_EXTRACT_PATH(self):
        return self._game_extract_path

    def GAME_DB_EXTRACT_PATH(self):
        return self._game_db_extract_path

    def GAME_RESOURCES_EXTRACT_PATH(self):
        return self._game_resources_extract_path

    def MODS_DATA_EXTRACT_PATH(self):
        return self._mods_extract_path
