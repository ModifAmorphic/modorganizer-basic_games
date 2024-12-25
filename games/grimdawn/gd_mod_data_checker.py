from dataclasses import dataclass
from collections.abc import Generator
from PyQt6.QtCore import qInfo, qDebug #, QDir, QFileInfo, qFatal, qCritical, qWarning
from ...basic_features import BasicModDataChecker
from enum import Enum

from mobase import (
    ModDataChecker,
    IFileTree,
    FileTreeEntry,
)
import re

@dataclass
class ModFileStatus:
    HasValidFiles: bool = False
    HasInvalidParents: bool = False
    HasDeletes: bool = False
    IsUnknown: bool = False
    IsEmptyDir: bool = False

class MatchResult(Enum):
    VALID = 1
    FIXABLE = 2
    DELETE = 3
    EMPTY_DIR = 4
    UNKNOWN = 5

@dataclass
class ModFileTree:
    """Class encapsulating a FileTreeEntry, it's MatchResult and 'fixPath' if applicable.

    Args:
        entry (FileTreeEntry): The FileTreeEntry the match was performed on.
        matchResult (MatchResult): Result of a match performed on the entry (FileTreeEntry) argument.
        fixPath (str): The path for a MatchResult.FIXABLE matchResult which if moved to would result in the entry (FileTreeEntry) being fixed (MatchResult.VALID) on the next match attempt.
    """
    entry: FileTreeEntry
    matchResult: MatchResult = MatchResult.UNKNOWN
    fixPath: str = ''


class GrimDawnModDataChecker(BasicModDataChecker):

    _REGEX_DIR_SEP = '/'
    _always_validate: set[str] = { "", "overwrite" }

    # Dictionary containing
    #  - Regular Expression used to find valid mod files that can be moved
    #  - The destination location of where the files should be placed to fix the mod
    # This dictionary is used to determine if a mod is fixable, and if so how to fix it
    _fixable_paths: dict[re.Pattern[str], str] = {
        re.compile(r'^.*\.arz$', re.IGNORECASE): 'mods/{{mod_folder}}/database',
        re.compile(r'^(?:.*/)?templates.arc$', re.IGNORECASE): 'mods/{{mod_folder}}/database',
        re.compile(r'^.*\.arc$', re.IGNORECASE): 'mods/{{mod_folder}}/resources',
        re.compile(r'^(?:.*/)?video/(?!.*/).*$', re.IGNORECASE): 'mods/{{mod_folder}}/video',
        re.compile(r'(?:^|(?<=/))(text_[a-zA-Z]{2})(?=/)(.*)', re.IGNORECASE): 'settings',
        re.compile(r'(?:^|(?<=/))(ui)(?=/)(.*\.(tex|psd))', re.IGNORECASE): "settings",
        re.compile(r'(?:^|(?<=/))(fonts)(?=/)(.*\.(bmp|fnt|ttf|txt))', re.IGNORECASE): "settings",
        re.compile(r'^.*\.dll$', re.IGNORECASE): ''
    }

    # Regular expression List of paths / files that are commonly added to mods but are safe to delete
    _delete_paths: set[re.Pattern[str]] = {
        re.compile(r'(^|/)resources/.*\.tex$', re.IGNORECASE),
        re.compile(r'(^|/)database/.*\.dbr$', re.IGNORECASE),
        re.compile(r'^.*\.7z$', re.IGNORECASE),
        re.compile(r'^.*\.rar$', re.IGNORECASE),
        re.compile(r'^.*\.zip$', re.IGNORECASE),
        re.compile(r'^(?:.*/)?(README|CHANGELOG).txt$', re.IGNORECASE),
        re.compile(r'^(?!.*/).*\.txt$', re.IGNORECASE)
    }

    # Used to validate a mod. All files in the mod must match one of these regular expressions
    _valid_paths: set[re.Pattern[str]]  = {
        re.compile(r'^mods/[^/]+/database/(?!.*/).*\.arz$', re.IGNORECASE),
        re.compile(r'^mods/[^/]+/database/templates.arc$', re.IGNORECASE),
        re.compile(r'^mods/[^/]+/resources/(?!.*/).*\.arc$', re.IGNORECASE),
        re.compile(r'^mods/[^/]+/video/(?!.*/).*$', re.IGNORECASE),
        re.compile(r'^settings/text_[a-zA-Z]{2}/.*$', re.IGNORECASE),
        re.compile(r'^settings/fonts/.*$', re.IGNORECASE),
        re.compile(r'^settings/ui/.*$', re.IGNORECASE),
        re.compile(r'^(?!.*/).*\.dll$', re.IGNORECASE)
    }

    def __init__(self):
        super().__init__()
    
    _root_folder: str = ''
    def modRootFolder(self):
        return self._root_folder

    def getFixedPath(self, fpath: re.Match[str]) -> str:
        return ''

    # Performs a match against various regex collections to determine a match status
    def match(self, filetree: FileTreeEntry) -> tuple[MatchResult, str]:
        """Performs regular expression matches using the FileTreeEntry's path() against various collections to determine if the entry is a valid or fixable mod file.

        Args:
            filetree (IFileTree): The filetree to perform regular expression matches against.
        
        Returns:
            tuple[MatchResult, str]: MatchResult - The result of the potential multiple regex matches executed on the filetree.path(). str - fix path set for MatchResult.FIXABLE results.
        """
        f_path = filetree.path(self._REGEX_DIR_SEP)
        qDebug(f"Performing matches on path '{f_path}'")
        if filetree.isDir() and type(filetree) is IFileTree:
            if not len(filetree):
                return MatchResult.EMPTY_DIR, ''
        
        for r in self._delete_paths:
            if r.search(f_path):
                qDebug(f"Path {f_path} matched criteria for deletion.")
                return MatchResult.DELETE, ''
         
        for r in self._valid_paths:
            if r.search(f_path):
                qDebug(f"Path {f_path} matched valid path criteria.")
                return MatchResult.VALID, ''
            
        for r in self._fixable_paths:
            sresult = r.search(f_path)
            if sresult:
                fix_path: str = self._fixable_paths[r].replace("{{mod_folder}}", self.modRootFolder())
                qDebug(f"Path {f_path} matched fixable path criteria. Raw fix_path=\"{self._fixable_paths[r]}\", Mod fix_path={fix_path}.")
                if fix_path == "settings":
                    # qDebug(f"Group 0: {lang_result.groups()[0]}, Group 1: {len(lang_result.groups()[1])}")
                    # Match includes filename
                    fix_path = self._fixable_paths[r] + self._REGEX_DIR_SEP + sresult[0]
                else:
                    # Append filename to path if not a settings file. Setting filename would already be appended.
                    qDebug(f"Joining \"{fix_path}\" path with filename \"{filetree.name()}\".")
                    fix_path = fix_path + self._REGEX_DIR_SEP + filetree.name()
                qDebug(f"Set fix_path to =\"{fix_path}\"")
                return MatchResult.FIXABLE, fix_path
            
        return MatchResult.UNKNOWN, ''
    
    # Get's the next File entry in a tree. If the directory is empty, then returns that instead
    def getNextFileEntry(self, filetree: IFileTree, return_empty_dirs: bool = False) -> Generator[ModFileTree, None, None]:
        """Iterates through an IFileTree getting the next file entry. Each file entry is tested for a match and the result is returned alongside the file entry.

        Args:
            filetree (IFileTree): The filetree to traverse.
            return_empty_dirs (bool): Optional. When True, will return empty directories in addition to files. Otherwise, empty directories are skipped.
        
        Returns:
            ModFileTree: A ModFileTree instance containing the IFileTree and MatchResult values for the yielded IFileTree entry.
        """
        for entry in filetree:
            # qDebug(f"getNextFileEntry: filetree={filetree.path(self._REGEX_DIR_SEP)}, return_empty_dirs={return_empty_dirs}")
            if entry is not None:
                if entry.isDir():
                    assert entry is IFileTree
                    if len(entry):
                        yield from self.getNextFileEntry(entry, return_empty_dirs)
                    elif return_empty_dirs:
                        result, fixpath = self.match(entry)
                        mod_tree = ModFileTree(entry, result, fixpath)
                        yield mod_tree
                    else:
                        yield from self.getNextFileEntry(entry, return_empty_dirs)
                else:
                    result, fixpath = self.match(entry)
                    mod_tree = ModFileTree(entry, result, fixpath)
                    yield mod_tree

    # Gets the root of the filetree
    def getTreeRoot(self, filetree: IFileTree) -> IFileTree:
        """Climbs the IFileTree until it finds the first / topmost entry.

        Args:
            filetree (IFileTree): The filetree to traverse.
        
        Returns:
            IFileTree: The root / topmost parent IFileTree.
        """
        parent: IFileTree | None = filetree
        root: IFileTree = parent

        # Get the root folder
        while (parent != None):
            parent = parent.parent()
            # parent = next_parent
            if (parent != None):
                root = parent
        
        return root
    
    # Detaches empty directories from the filetree
    def pruneEmptyDirs(self, filetree: IFileTree, recursive: bool = False):
        """Detaches empty directories from a IFileTree.

        Args:
            filetree (IFileTree): The filetree to prune empty directories from.
            recursive (recursive): If True, will recursively prune the filetree until no empty directories remain. Otherwise only prunes empty directories once.
        """

        qDebug(f"Pruning empty directories from path {filetree.path(self._REGEX_DIR_SEP)}. recursive={recursive}")
        detaches: list[FileTreeEntry] = []
        tree = filetree
        if recursive:
            tree = self.getTreeRoot(filetree)

        # Gather a list of empty folders to detach
        for mod_tree in self.getNextFileEntry(tree, True):
            # detach empty directory
            d_path = mod_tree.entry.path(self._REGEX_DIR_SEP)
            # qDebug(f"Checking if entry \"{mod_tree.entry.name()}\", path=\"{d_path}\" is an empty directory.")
            if mod_tree.entry.isDir() and mod_tree.entry.name() != "":
                qDebug(f"Queuing Empty Directory {d_path} ({mod_tree.entry.name()}) for removal.")
                detaches.append(mod_tree.entry)
        
        # Detach any empy folders
        for d in detaches:
            d.detach()
        
        # If recusive is set, redo the prune until all empty directories are removed
        if recursive:
            if detaches:
                qDebug(f"Last prune found {len(detaches)} empty directories. Continuing until no empty directories remain.")
                self.pruneEmptyDirs(tree, True)
                

    def dataLooksValid(self, filetree: IFileTree) -> ModDataChecker.CheckReturn:
        # qDebug(f"dataLooksValid: path=\"{filetree.path(self._REGEX_DIR_SEP)}\", name=\"{filetree.name()}\"")
        # Skips redundant checks from Mod Organizer
        ftree_path = filetree.path(self._REGEX_DIR_SEP)
        if filetree.isDir() and ftree_path not in self._always_validate:
             return ModDataChecker.FIXABLE
        
        qDebug(f"dataLooksValid: Scanning Filetree \"{ftree_path}\"!")
        self._root_folder = filetree.name()
        if (filetree.name() == "" and len(filetree)):
            self._root_folder = filetree[0].name()
        # root = self.getTreeRoot(filetree)
        return_status = ModDataChecker.INVALID
        
        for modEntry in self.getNextFileEntry(filetree):
            m_path = modEntry.entry.path(self._REGEX_DIR_SEP)
            # qDebug(f"dataLooksValid: Determining Entry \"{m_path}\" validity.")
            if modEntry.matchResult == MatchResult.UNKNOWN:
                # Found an unexpected file or path. Return invalid and get out of here
                qDebug(f"dataLooksValid() Unknown file \"{m_path}\" found. Returning status {ModDataChecker.INVALID}")
                return ModDataChecker.INVALID 
            if modEntry.matchResult == MatchResult.FIXABLE:
                return_status = ModDataChecker.FIXABLE
            if modEntry.matchResult == MatchResult.VALID and return_status == ModDataChecker.INVALID:
                return_status = ModDataChecker.VALID

        qDebug(f"dataLooksValid() returning status {return_status}")
        return return_status

    def fix(self, filetree: IFileTree) -> IFileTree:

        root = self.getTreeRoot(filetree)
        if len(root) and root.name() == "":
            qDebug(f"root.name() is an empty string. Assigning first child.")
            root = root[0]

        root_mod_folder = root.name()

        qInfo(f"Fixing filetree for mod folder '{root_mod_folder}'")
        detaches: list[FileTreeEntry] = []
        moves: list[ModFileTree] = []

        for mod_tree in self.getNextFileEntry(filetree):
            # m_path = mod_tree.entry.path(self._REGEX_DIR_SEP)
            # qDebug(f"Fix: Processing entry {m_path}")
            if mod_tree.matchResult == MatchResult.DELETE:
                #qDebug(f"Queuing \"{m_path}\" for deletion.")
                detaches.append(mod_tree.entry)
            if mod_tree.matchResult == MatchResult.FIXABLE:
                #qDebug(f"Queuing \"{m_path}\" for move.")
                moves.append(mod_tree)
                
        for d in detaches:
            qDebug(f"Detaching \"{d.path(self._REGEX_DIR_SEP)}\".")
            d.detach()
        
        for m in moves:
            qDebug(f"Moving file \"{m.entry.path(self._REGEX_DIR_SEP)}\" to \"{m.fixPath}\".")
            filetree.move(m.entry, m.fixPath)
        
        
        self.pruneEmptyDirs(filetree, True)

        return filetree