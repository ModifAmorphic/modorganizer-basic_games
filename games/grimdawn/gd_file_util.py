from hashlib import blake2b
from pathlib import Path
from typing import Union


class HashUtil:
    @staticmethod
    def hash_file(file: Union[str, Path], hash: blake2b | None = None) -> blake2b:
        if not hash:
            hash = blake2b(digest_size=32)
        with open(str(file), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
        return hash

    @staticmethod
    def hash_directory(
        directory: Union[str, Path],
        hash: blake2b | None = None,
        recursive: bool = False,
    ) -> blake2b:
        assert Path(directory).is_dir()
        if not hash:
            hash = blake2b(digest_size=32)
        for path in sorted(Path(directory).iterdir(), key=lambda p: str(p).lower()):
            # qDebug(f"Hashing {path}")
            hash.update(path.name.encode())
            if path.is_file():
                hash = HashUtil.hash_file(path, hash)
            elif path.is_dir() and recursive:
                hash = HashUtil.hash_directory(path, hash, recursive)
        return hash


class PathUtil:
    @staticmethod
    def move_tree(source_dir: Path, dest_dir: Path, remove_source_dir: bool = False):
        # qDebug(f"Moving all files and folders in {source_dir} to {dest_dir}")
        for root, dirs, files in source_dir.walk(top_down=False):
            # Recreate all directories in the destination
            rel_path = root.relative_to(source_dir)
            for name in dirs:
                dest_path = dest_dir / rel_path / name
                # qDebug(f"Creating Dir: {dest_path}, name: {name}")
                dest_path.mkdir(parents=True, exist_ok=True)

            dest_root = dest_dir / rel_path
            # qDebug(f"Creating destination folder {dest_root}")
            dest_root.mkdir(parents=True, exist_ok=True)
            # Move all the files over to the destination
            for name in files:
                source_path = root / name
                rel_path = root.relative_to(source_dir)
                dest_path = dest_dir / rel_path / name
                # qDebug(f"Moving file to: {dest_path}, name: {name}")
                source_path.replace(dest_path)
            # Cleanup empty source directories
            for name in dirs:
                (root / name).rmdir()

        if remove_source_dir:
            source_dir.rmdir()

    @staticmethod
    def delete_contents(directory: Path, delete_directory: bool = False):
        """
        Deletes all files and folders in the directory path.

        Arguments:
            directory (Path): The directory whose contents should be removed.
            delete_directory (bool): (Optional) If True, also removes the directory Path in the first argument. Default is False.
        """
        if not directory.is_dir():
            raise ValueError(
                "Invalid argument Path. directory argument must be an actual directory."
            )

        for root, dirs, files in directory.walk(top_down=False):
            for name in files:
                (root / name).unlink()
            for name in dirs:
                (root / name).rmdir()

        if delete_directory:
            directory.rmdir()
