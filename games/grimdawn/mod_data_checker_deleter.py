# from os import path
# from pathlib import Path
# from collections.abc import Generator
# from PyQt6.QtCore import QDir, QFileInfo, qFatal, qCritical, qWarning, qInfo, qDebug
# import mobase
# from ...basic_features import BasicModDataChecker

# from mobase import (
#     ModDataChecker,
#     IFileTree,
#     FileTreeEntry,
# )
# import re

# class ModFileStatus:
#     HasValidFiles: bool = False
#     HasInvalidParents: bool = False
#     HasDeletes: bool = False

#     def __init__(self, hasValidFiles: bool = False, hasInvalidParents: bool = False, hasDeletes: bool = False):
#         self.HasValidFiles = hasValidFiles
#         self.HasInvalidParents = hasInvalidParents
#         self.HasDeletes = hasDeletes

# class ModFileTree:
#     Status: ModFileStatus
#     Entry: FileTreeEntry

# class GrimDawnModDataCheckerDeleter(BasicModDataChecker):

#     _valid_root_folders = {
#         "mods",
#         "settings"
#     }
#     _settings_folder = "settings"
#     _dir_regex = '([a-zA-Z0-9-_]+)+'
#     _dir_pattern = re.compile(rf'{_dir_regex}')
#     _archive_exts: dict[str, str] = {
#         ".arz": 'mods/{{mod_folder}}/database',
#         ".arc": 'mods/{{mod_folder}}/resources'
#     }
#     _archive_regex: dict[str, re.Pattern[str]] = {
#         ".arz": re.compile(rf'mods/{_dir_regex}/database'),
#         ".arc": re.compile(rf'mods/{_dir_regex}/resources')
#     }

#     # _archive_exts: list[str] = [
#     #     ".arz",
#     #     ".arc"
#     # ]

#     def __init__(self):
#         super().__init__()
    
#     def isValidFile(self, filetree: FileTreeEntry) -> bool:
#         ext = Path(filetree.name()).suffix.casefold()
#         if ext in self._archive_exts: 
#             return True

#         if self.isSettingsFile(filetree):
#             return True
#         return False
    
#     def getParentPath(self, entry: FileTreeEntry) -> str:
#         if entry.isDir():
#             qWarning(f"Attempted to find parent path of directory '{entry.path()}'")
#             return ''
        
#         ext = Path(entry.name()).suffix.casefold()

#         if ext in self._archive_exts:
#             full_path = entry.path('/').casefold()
#             if self._archive_regex[ext].match(full_path):
#                 return path.dirname(full_path)
#             else:
#                 mod_folder = full_path.split('/')[0]
#                 return self._archive_exts[ext].replace('{{mod_folder}}', mod_folder)

#             # return self._archive_exts[ext]
        
#         if self.isSettingsFile(entry):
#             full_path = entry.path('/').casefold()
#             directories = full_path.split('/')
#             settings_flag = False
#             settings_dirs: list[str] = []
#             for d in directories:
#                 if d == self._settings_folder:
#                     settings_flag = True
#                 if settings_flag:
#                     settings_dirs.append(d)
            
#             settings_dirs.pop(-1)
#             return str.join('/', settings_dirs)
#         return ''
    
#     def isSettingsFile(self, filetree: FileTreeEntry):
#         full_path = filetree.path('/').casefold()
#         if full_path.startswith(self._settings_folder + "/"):
#             return True
#         if ("/" + self._settings_folder + "/") in full_path:
#             return True
#         return False
    
#     def isParentValid(self, filetree: FileTreeEntry) -> bool:
#         ext = Path(filetree.name()).suffix.casefold()
#         full_path = filetree.path('/').casefold()
#         parent = filetree.parent()
#         parent_dir = ""
#         if parent is not None:
#             parent_dir = full_path
        
#         if ext in self._archive_exts:
#             qDebug(f"Checking if paths match mod_path={parent_dir}, valid_path={self._archive_exts[ext]}. result={self._archive_exts[ext] == parent_dir}")
#             if self._archive_regex[ext].match(parent_dir):
#             # if self._archive_exts[ext] == parent_dir:
#                 return True
            
#         if full_path.startswith(self._settings_folder + "/"):
#             return True
        
#         return False
    
#     def getFileStatus(self, file_entry: FileTreeEntry) -> ModFileStatus:
#         fStatus = ModFileStatus()
#         if self.isValidFile(file_entry):
#             fStatus.HasValidFiles = True
#             if not self.isParentValid(file_entry):
#                 fStatus.HasInvalidParents = True
#         else:
#             fStatus.HasDeletes = True
        
#         return fStatus

#     def getNextEntry(self, filetree: IFileTree) -> Generator[ModFileTree, None, None]:
#         tree: ModFileTree = ModFileTree()
                
#         for entry in filetree:
#             if entry is not None:
#                 if entry.isDir() and type(entry) is IFileTree:
#                     if len(entry):
#                         yield from self.getNextEntry(entry)
#                     else:
#                         tree.Entry = filetree
#                         tree.Status = ModFileStatus(False, False, False)
#                         yield tree
#                 else:
#                     tree.Entry = entry
#                     tree.Status = self.getFileStatus(entry)
#                     yield tree 

#     def getTreeStatus(self, filetree: IFileTree, return_status: ModFileStatus = ModFileStatus()) -> ModFileStatus:
#         for entry in filetree:
#             fStatus: ModFileStatus
#             # qDebug(f"getTreeStatus().return_status: HasValidFiles={return_status.HasValidFiles}, HasDeletes={return_status.HasDeletes}, HasInvalidParents={return_status.HasInvalidParents}")
#             if entry.isDir() and type(entry) is IFileTree:
#                 qDebug(f"Checking '{entry.name()}' path of '{entry.path('/').casefold()}'")
#                 if entry.name().casefold() == self._settings_folder:
#                     if entry.path('/').casefold() == self._settings_folder:
#                         fStatus = ModFileStatus(hasValidFiles=True)
#                     else:    
#                         qDebug(f"{entry.path('/').casefold()} != self._settings_folder")
#                         fStatus = ModFileStatus(hasValidFiles=True,hasInvalidParents=True)
#                 else:
#                     # Recurse through all directories
#                     fStatus = self.getTreeStatus(entry, return_status)
#             else:
#                 fStatus = self.getFileStatus(entry)

#             if fStatus.HasDeletes:
#                 return_status.HasDeletes = True
#             if fStatus.HasValidFiles:
#                 return_status.HasValidFiles = True
#             if fStatus.HasInvalidParents:
#                 return_status.HasInvalidParents = True
#         return return_status

#     _always_validate: set[str] = { "", "overwrite" }
#     def dataLooksValid(self, filetree: IFileTree) -> ModDataChecker.CheckReturn:
#         qDebug(f"dataLooksValid: path=\"{filetree.path()}\", name=\"{filetree.name()}\"")
#         if filetree.isDir() and filetree.path() not in self._always_validate:
#              return ModDataChecker.FIXABLE
        
#         qDebug(f"dataLooksValid: Scanning Filetree \"{filetree.path()}\"!")
        
#         parent: IFileTree | None = filetree
#         root: IFileTree = parent
        
#         # Get the root folder
#         while (parent != None):
#             parent = parent.parent()
#             # parent = next_parent
#             if (parent != None):
#                 root = parent
                
#         tree_status = self.getTreeStatus(root, ModFileStatus())

#         # # first_entry = filetree.ch
#         # mod_folder: str = filetree.name()
#         # # if isinstance(first_entry, mobase.IFileTree):
#         # #     mod_folder = first_entry.name()
#         # qDebug(f"dataLooksValid(\"{filetree.path()}\") mod_folder={mod_folder}. Got Statuses: HasValidFiles={tree_status.HasValidFiles}, HasDeletes={tree_status.HasDeletes}, HasInvalidParents={tree_status.HasInvalidParents}")
#         # return ModDataChecker.INVALID
#         if not tree_status.HasValidFiles:
#             qDebug(f"dataLooksValid() Returning status {ModDataChecker.INVALID}")
#             # return ModDataChecker.INVALID
#             return ModDataChecker.INVALID
#         elif tree_status.HasDeletes or tree_status.HasInvalidParents:
#             qDebug(f"dataLooksValid() Returning status {ModDataChecker.FIXABLE}")
#             return ModDataChecker.FIXABLE
#         else:
#             qDebug(f"dataLooksValid() Returning status {ModDataChecker.VALID}")
#             return ModDataChecker.VALID
        
#     def fix(self, filetree: IFileTree) -> IFileTree:
#         qInfo(f"Fixing filetree {filetree.name()}")
#         detaches: list[FileTreeEntry] = []
#         moves: list[FileTreeEntry] = []

#         for entry in self.getNextEntry(filetree):
#             # detach empty directory
#             if entry.Entry.isDir():
#                 qDebug(f"Appending Empty Directory {entry.Entry.path()}.")
#                 detaches.append(entry.Entry)
#             elif entry.Status.HasDeletes:
#                 qDebug(f"Appending Entry to Delete {entry.Entry.path()}.")
#                 detaches.append(entry.Entry)
#             elif entry.Status.HasInvalidParents:
#                 moves.append(entry.Entry)
                
#         for d in detaches:
#             d.detach()
        
#         for m in moves:
#             directory_path = self.getParentPath(m)
#             qDebug(f"Moving {m.path()} to {directory_path}.")
#             filetree.move(m, f"{directory_path}/{m.name()}")

#         root_removes: list[FileTreeEntry] = []
#         for root in filetree:
#             if root.name() not in self._valid_root_folders:
#                 root_removes.append(root)
        
#         for r in root_removes:
#             r.detach()

#         return filetree
    
# # class GrimDawnModDataChecker(ModDataChecker):
    
# #     _valid_folders: list[str] = [
# #         "mods",
# #         "settings"
# #     ]

# #     _archive_exts: list[str] = [
# #         "arz",
# #         "arc"
# #     ]

# #     # Check to ensure only directories listed in _valid_folders are at the root of the filetree
# #     def isTreeValid(self, fileTree: IFileTree) -> bool:
# #         for f in fileTree:
# #             if f.isDir():
# #                 if f.name().casefold() not in self._valid_folders:
# #                     return False
# #             else:
# #                 return False
# #         return True
    
# #     # Check to ensure only directories listed in _valid_folders are at the root of the filetree
# #     def isFixable(self, fileTree: IFileTree) -> bool:
# #         for f in fileTree:
# #             if f.isDir():
# #                 if f.name().casefold() not in self._valid_folders:
# #                     return False
# #             else:
# #                 return False
# #         return True
    
# #     # def fix(self, filetree: mobase.IFileTree):
# #     #     dbs = filetree.find("*.arz")
# #     #     Path()

# #     def dataLooksValid(self, filetree: IFileTree) -> ModDataChecker.CheckReturn:
# #         if self.isTreeValid(filetree):
# #             return ModDataChecker.VALID
# #         elif self.isFixable(filetree):
# #             return ModDataChecker.FIXABLE

# #         return ModDataChecker.INVALID