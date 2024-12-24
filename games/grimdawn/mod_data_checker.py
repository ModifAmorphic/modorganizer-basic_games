from os import path
from pathlib import Path
from collections.abc import Generator
from PyQt6.QtCore import QDir, QFileInfo, qFatal, qCritical, qWarning, qInfo, qDebug
import mobase
from ...basic_features import BasicModDataChecker

from mobase import (
    ModDataChecker,
    IFileTree,
    FileTreeEntry,
)
import re

class ModFileStatus:
    HasValidFiles: bool = False
    HasInvalidParents: bool = False
    HasDeletes: bool = False
    IsUnknown: bool = False
    IsEmptyDir: bool = False

    def __init__(self, hasValidFiles: bool = False, hasInvalidParents: bool = False, hasDeletes: bool = False, isUnknown: bool = False, isEmptyDir: bool = False):
        self.HasValidFiles = hasValidFiles
        self.HasInvalidParents = hasInvalidParents
        self.HasDeletes = hasDeletes
        self.IsUnknown = isUnknown
        self.IsEmptyDir = isEmptyDir

class ModFileTree:
    Status: ModFileStatus
    Entry: FileTreeEntry

class GrimDawnModDataChecker(BasicModDataChecker):

    _always_validate: set[str] = { "", "overwrite" }
    _valid_root_folders = {
        "mods",
        "settings"
    }
    _delete_files = {
        re.compile(r'.*\.tex$'),
        re.compile(r'.*\.dbr$'),
        re.compile(r'^templates.arc$'),
    }
    _required_mod_folders = {
        "database",
        "records"
    }
    # Dictionary containing
    #  - Regular Expression used to find valid mod files
    #  - The destination location of the mod files
    # This dictionary is used to determine if a mod is fixable, and if so how to fix it
    _search_paths = {
        re.compile(r'(?:.*/)?([a-zA-Z0-9-_.]+)+.arz$'): 'mods/{{mod_folder}}/database',
        re.compile(r'(?:.*/)?templates.arc$'): 'mods/{{mod_folder}}/database',
        re.compile(r'(?:.*/)?([a-zA-Z0-9-_.]+)+.arc$'): 'mods/{{mod_folder}}/resources',
        re.compile(r'(?:.*/)?videos/([a-zA-Z0-9-_.]+)+$'): 'mods/{{mod_folder}}/videos',
        re.compile(r'(?:.*/)?text_[a-zA-Z]{2}$'): 'settings',
        re.compile(r'(?:.*/)?([a-zA-Z0-9-_.]+)+.dll$'): ''
    }

    # Used to validate a mod. All files in the mod must match one of these regular expressions
    _valid_paths = [
        re.compile(r'^mods/([a-zA-Z0-9-_.]+)+/database/([a-zA-Z0-9-_.]+)+.arz$'),
        re.compile(r'^mods/([a-zA-Z0-9-_.]+)+/database/templates.arc$'),
        re.compile(r'^mods/([a-zA-Z0-9-_.]+)+/resources/([a-zA-Z0-9-_.]+)+.arc$'),
        re.compile(r'^mods/([a-zA-Z0-9-_.]+)+/videos/([a-zA-Z0-9-_.]+)+$'),
        re.compile(r'^settings/text_[a-zA-Z]{2}$'),
        re.compile(r'^([a-zA-Z0-9-_.]+)+.dll$')
    ]
    
    _settings_folder = "settings"
    _dir_regex = '([a-zA-Z0-9-_]+)+'
    _dir_pattern = re.compile(rf'{_dir_regex}')
    _archive_exts: dict[str, str] = {
        ".arz": 'mods/{{mod_folder}}/database',
        ".arc": 'mods/{{mod_folder}}/resources',
    }
    _archive_regex: dict[str, re.Pattern[str]] = {
        ".arz": re.compile(rf'mods/{_dir_regex}/database'),
        ".arc": re.compile(rf'mods/{_dir_regex}/resources')
    }

    # _archive_exts: list[str] = [
    #     ".arz",
    #     ".arc"
    # ]

    def __init__(self):
        super().__init__()
    
    def isValidFile(self, filetree: FileTreeEntry) -> bool:
        ext = Path(filetree.name()).suffix.casefold()
        # qDebug(f"Checking if file {filetree.name()} matches valid file criteria.")
        if ext in self._archive_exts: 
            qDebug(f"File {filetree.name()} matches valid file criteria.")
            return True

        if self.isSettingsFile(filetree):
            qDebug(f"File {filetree.name()} matches settings file criteria.")
            return True
        return False
    
    def isDeletedFile(self, filetree: FileTreeEntry) -> bool:
        name = filetree.name().casefold()
        # qDebug(f"Checking if file {name} matches criteria for deletion.")
        for r in self._delete_files:
            if r.match(name):
                qDebug(f"File {name} matched criteria for deletion.")
                return True
        
        return False
    
    def getParentPath(self, entry: FileTreeEntry) -> str:
        if entry.isDir():
            qWarning(f"Attempted to find parent path of directory '{entry.path()}'")
            return ''
        
        ext = Path(entry.name()).suffix.casefold()

        if ext in self._archive_exts:
            full_path = entry.path('/').casefold()
            if self._archive_regex[ext].match(full_path):
                return path.dirname(full_path)
            else:
                mod_folder = full_path.split('/')[0]
                return self._archive_exts[ext].replace('{{mod_folder}}', mod_folder)

            # return self._archive_exts[ext]
        
        if self.isSettingsFile(entry):
            full_path = entry.path('/').casefold()
            directories = full_path.split('/')
            settings_flag = False
            settings_dirs: list[str] = []
            for d in directories:
                if d == self._settings_folder:
                    settings_flag = True
                if settings_flag:
                    settings_dirs.append(d)
            
            settings_dirs.pop(-1)
            return str.join('/', settings_dirs)
        return ''
    
    def isSettingsFile(self, filetree: FileTreeEntry):
        full_path = filetree.path('/').casefold()
        if full_path.startswith(self._settings_folder + "/"):
            return True
        if ("/" + self._settings_folder + "/") in full_path:
            return True
        return False
    
    def isParentValid(self, filetree: FileTreeEntry) -> bool:
        ext = Path(filetree.name()).suffix.casefold()
        full_path = filetree.path('/').casefold()
        parent = filetree.parent()
        parent_dir = ""
        if parent is not None:
            parent_dir = full_path
        
        if ext in self._archive_exts:
            # qDebug(f"Checking if parent path \"{parent_dir}\" of entry {filetree.name()} is a valid path.")
            if self._archive_regex[ext].match(parent_dir):
                # qDebug(f"Parent path \"{parent_dir}\" is a valid path.")
                return True
            
        if full_path.startswith(self._settings_folder + "/"):
            qDebug(f"Found valid settings file path in \"{full_path}\".")
            return True
        
        return False
    
    def getFileStatus(self, file_entry: FileTreeEntry) -> ModFileStatus:
        fStatus = ModFileStatus()
        if self.isDeletedFile(file_entry):
            fStatus.HasDeletes = True
        elif self.isValidFile(file_entry):
            fStatus.HasValidFiles = True
            if not self.isParentValid(file_entry):
                fStatus.HasInvalidParents = True
        else:
            fStatus.IsUnknown = True
        
        return fStatus

    # Get's the next File entry in a tree. If the directory is empty, then returns that instead
    def getNextFileEntry(self, filetree: IFileTree, return_empty_dirs: bool = False) -> Generator[ModFileTree, None, None]:
        tree: ModFileTree = ModFileTree()
                
        for entry in filetree:
            if entry is not None:
                if entry.isDir() and type(entry) is IFileTree:
                    if len(entry) or return_empty_dirs == False:
                        # qDebug(f"Skipping return of directory {entry.name()}. Directory has children={len(entry)}, return_empty_dirs=={return_empty_dirs}")
                        yield from self.getNextFileEntry(entry, return_empty_dirs)
                    else:
                        tree.Entry = entry
                        tree.Status = ModFileStatus(False, False, False, False, True)
                        # qDebug(f"Return empty directory {entry.name()}")
                        yield tree
                else:
                    tree.Entry = entry
                    tree.Status = self.getFileStatus(entry)
                    yield tree 

    def getTreeRoot(self, filetree: IFileTree) -> IFileTree:
        parent: IFileTree | None = filetree
        root: IFileTree = parent

        # Get the root folder
        while (parent != None):
            parent = parent.parent()
            # parent = next_parent
            if (parent != None):
                root = parent
        
        return root

    def dataLooksValid(self, filetree: IFileTree) -> ModDataChecker.CheckReturn:
        qDebug(f"dataLooksValid: path=\"{filetree.path()}\", name=\"{filetree.name()}\"")
        if filetree.isDir() and filetree.path() not in self._always_validate:
             return ModDataChecker.FIXABLE
        
        qDebug(f"dataLooksValid: Scanning Filetree \"{filetree.path()}\"!")
        
        root = self.getTreeRoot(filetree)
        file_statuses = ModFileStatus()
        for modEntry in self.getNextFileEntry(root):
            qDebug(f"dataLooksValid: Determining Entry \"{modEntry.Entry.path()}\" validity.")
            if modEntry.Status.IsUnknown:
                # Found an unexpected file or path. Return invalid and get out of here
                return ModDataChecker.INVALID 
            if modEntry.Status.HasDeletes:
                file_statuses.HasDeletes = True
            if modEntry.Status.HasValidFiles:
                file_statuses.HasValidFiles = True
            if modEntry.Status.HasInvalidParents:
                file_statuses.HasInvalidParents = True

        if not file_statuses.HasValidFiles:
            qDebug(f"dataLooksValid() Returning status {ModDataChecker.INVALID}")
            return ModDataChecker.INVALID
        elif file_statuses.HasDeletes or file_statuses.HasInvalidParents:
            qDebug(f"dataLooksValid() Returning status {ModDataChecker.FIXABLE}. HasDeletes={file_statuses.HasDeletes}, HasInvalidParents={file_statuses.HasInvalidParents}")
            return ModDataChecker.FIXABLE
        else:
            qDebug(f"dataLooksValid() Returning status {ModDataChecker.VALID}")
            return ModDataChecker.VALID
        
    def pruneEmptyDirs(self, filetree: IFileTree, recursive: bool = False):
        qDebug(f"Pruning empty directories from path {filetree.path()}. recursive={recursive}")
        detaches: list[FileTreeEntry] = []
        tree = filetree
        if recursive:
            tree = self.getTreeRoot(filetree)

        for entry in self.getNextFileEntry(tree, True):
            # detach empty directory
            qDebug(f"Checking if entry \"{entry.Entry.name()}\", path=\"{entry.Entry.path()}\" is an empty directory.")
            if entry.Entry.isDir() and entry.Entry.name() != "":
                qDebug(f"Queuing Empty Directory {entry.Entry.path()} ({entry.Entry.name()}) for removal.")
                detaches.append(entry.Entry)
        
        for d in detaches:
            d.detach()
        
        # If recusive is set, redo the prune until all empty directories are removed
        if recursive:
            if detaches:
                qDebug(f"Last prune found {len(detaches)} empty directories. Continuing until no empty directories remain.")
                self.pruneEmptyDirs(tree, True)
                

    def fix(self, filetree: IFileTree) -> IFileTree:
        qInfo(f"Fixing filetree {filetree.name()}")
        detaches: list[FileTreeEntry] = []
        moves: list[FileTreeEntry] = []

        for entry in self.getNextFileEntry(filetree):
            # detach empty 
            qDebug(f"Fix: Processing entry {entry.Entry.path()}")
            if entry.Entry.isDir():
                qDebug(f"Appending Empty Directory {entry.Entry.path()}.")
                detaches.append(entry.Entry)
            elif entry.Status.HasDeletes:
                qDebug(f"Appending Entry to Delete {entry.Entry.path()}.")
                detaches.append(entry.Entry)
            elif entry.Status.HasInvalidParents:
                moves.append(entry.Entry)
                
        for d in detaches:
            d.detach()
        
        for m in moves:
            directory_path = self.getParentPath(m)
            qDebug(f"Moving {m.path()} to {directory_path}.")
            filetree.move(m, f"{directory_path}/{m.name()}")
        
        
        self.pruneEmptyDirs(filetree, True)
        # Recurse one final time, collecting any empy directories
        # detaches: list[FileTreeEntry] = []
        # root = self.getTreeRoot(filetree)
        # for entry in self.getNextFileEntry(root, True):
        #     # detach empty directory
        #     if entry.Entry.isDir():
        #         qDebug(f"Appending Empty Directory {entry.Entry.path()}.")
        #         detaches.append(entry.Entry)
        
        # for d in detaches:
        #     d.detach()
        # root_removes: list[FileTreeEntry] = []
        # for root in filetree:
        #     if root.name() not in self._valid_root_folders:
        #         root_removes.append(root)
        
        # for r in root_removes:
        #     r.detach()

        return filetree