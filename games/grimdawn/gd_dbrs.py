import subprocess
import threading
from dataclasses import dataclass
from os import path
from typing import Callable

# from PyQt6.QtCore import QDir, QFileInfo, qFatal, qCritical, qWarning, qInfo, qDebug


class dbr:
    def __init__(self, relative_path: str, dbdata: dict[str, str]):
        self.relative_path = relative_path


@dataclass
class ExtractStatus:
    _is_running: bool
    _status_msg: str

    def is_running(self) -> bool:
        return self._is_running

    def status(self) -> str:
        return self._status_msg


class ModExtractor:
    GameExtractPath: str
    ModsExtractPath: str

    _game_path: str
    _data_path: str
    _archive_tool: str

    def __init__(self, game_path: str, data_path: str):
        self._game_path = game_path
        self._data_path = data_path
        self._archive_tool = path.join(self._game_path, "ArchiveTool.exe")
        self.GameExtractPath = path.join(self._data_path, "game_data")
        self.ModsExtractPath = path.join(self._data_path, "mods")

    def extract_databases(
        self,
        databases: list[str],
        absolute_out_path: str,
        callback: Callable[[ExtractStatus], None],
    ):
        for db_path in databases:
            callback(
                ExtractStatus(True, f'Extracting "{db_path}" to "{absolute_out_path}"')
            )
            process = subprocess.Popen(
                [self._archive_tool, db_path, "-database", absolute_out_path]
            )
            # TODO: Nice to have - Callback with updates so they can be displayed in mod organizer.
            process.wait()
        callback(ExtractStatus(False, "Extraction of Grim Dawn Databases complete."))

    # def extract_resources(self, resource_paths: list[str], )

    # TODO: extend callback to caller of this function so it can display some kind of blocking UI element until
    # this process is complete
    def extract_grimdawn(self, callback: Callable[[ExtractStatus], None]) -> str:
        databases = [
            path.join(self._game_path, "database", "database.arz"),
            path.join(
                self._game_path, "survivalmode1", "database", "SurvivalMode1.arz"
            ),
            path.join(
                self._game_path, "survivalmode2", "database", "SurvivalMode2.arz"
            ),
            path.join(self._game_path, "gdx1", "database", "GDX1.arz"),
            path.join(self._game_path, "gdx2", "database", "GDX2.arz"),
        ]
        t = threading.Thread(
            target=self.extract_databases,
            args=[databases, self.GameExtractPath, callback],
        )
        t.daemon = False
        t.start()
        return self.GameExtractPath


# scratch code

# def extract_grimdawn_process(game_dir: str, out_dir: str, callback: Callable[[str], None]):
#     archive_tool = path.join(game_dir, "ArchiveTool.exe")
#     db_path = path.join(game_dir, "database", "database.arz")
#     process = subprocess.Popen([archive_tool, db_path, "-database", out_dir])
#     #TODO: Nice to have - Callback with updates so they can be displayed in mod organizer.
#     process.wait()
#     callback("complete")

# #TODO: extend callback to caller of this function so it can display some kind of blocking UI element until
# # this process is complete
# def extract_grimdawn(game_dir: str, out_dir: str):
#     t = threading.Thread(target=extract_grimdawn_process, args=[game_dir, out_dir, on_extract_complete])
#     t.daemon = False
#     t.start()

# #TODO: Remove this once the callers can handle their own events
# def on_extract_complete(status: str):
#     qInfo(f"Grim Dawn Extract completed with status \"{status}\"")

# import asyncio
# import multiprocessing
# import multiprocessing.process
# def extract_grimdawn(game_dir: str, out_dir: str):
# loop = asyncio.get_event_loop()
# loop.create_task(extract_actually(game_dir, out_dir))
# qInfo("before")
# loop.run_forever()
# qInfo("after")
# archive_tool = path.join(game_dir, "ArchiveTool.exe")
# db_path = path.join(game_dir, "database", "database.arz")
# # qInfo("before")

# # asyncio.create_task(main())
# # qInfo("after")
# # subprocess.run([archive_tool, db_path, "-database", out_dir], capture_output=True, text=True)
# process = subprocess.Popen([archive_tool, db_path, "-database", out_dir])
# i: int = 0

# while process.poll() is None:
#     time.sleep(10)
#     i = i + 10
#     qInfo(f"Extracting Grim Dawn for {i} seconds.")
#     pass

# with subprocess.Popen([archive_tool, db_path, "-database", out_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
#     for line in process.stdout:
#         qInfo(line.decode('utf8'))

# for line in iter(extract_proc.stdout.readline, b""):
#     sys.stdout.write(line.decode(sys.stdout.encoding))
#     qInfo(line)


# def extract(self, mod_name: str, mod_path: str):

# def read_dbr(self, file_path: str) -> dict[str, str]:
#     dbr_data: dict[str, str] = {}
#     with open(file_path) as dbrfile:
#         for line in dbrfile:
#             header = line.split(',')[0]
#             dbr_data[header] = line
#     return dbr_data

# async def extract_grimdawn_async(game_dir: str, out_dir: str):
#     archive_tool = path.join(game_dir, "ArchiveTool.exe")
#     db_path = path.join(game_dir, "database", "database.arz")
#     process = subprocess.Popen([archive_tool, db_path, "-database", out_dir])
#     i: int = 0
#     while process.poll() is None:
#         await asyncio.sleep(5)
#         i = i + 5
#         qInfo(f"Extracting Grim Dawn for {i} seconds.")
#         pass
