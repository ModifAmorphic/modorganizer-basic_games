import random
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, TypedDict, Union, Generic, TypeVar, Unpack
from pathlib import Path

from .gd_file_util import PathUtil

from .gd_data import MultiStepProgress

from PyQt6.QtCore import QObject, QProcess, QThread, qDebug, QTemporaryDir, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

T = TypeVar('T')

class RequestParams(TypedDict): ...

class WorkerSignals(QObject):
    started = pyqtSignal(MultiStepProgress)
    progress = pyqtSignal(MultiStepProgress)
    finished = pyqtSignal(MultiStepProgress)

class ProgressUpdate(Protocol):
    def __call__(self, progress: int) -> None: ...
class TaskFinished(Protocol):
    def __call__(self) -> None: ...

class Worker(QRunnable):

    signals: WorkerSignals

    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        ...

    def on_progress(self, progress: int):
        self.signals.progress.emit(progress)

    def on_finished(self):
        self.signals.finished.emit()

# class Worker(QObject):
#     _init_(self):

    
#     finished = pyqtSignal()
#     progress = pyqtSignal(int)
    
#     @pyqtSlot
#     def run(self):
#         """Long-running task."""
#         for i in range(5):
#             sleep(1)
#             self.progress.emit(i + 1)
#         self.finished.emit()

# class Manager():
#     _parent: Union[QObject, None] = None
#     _pool: QThreadPool

#     def __init__(self, parent: Union[QObject, None]):
#         self._parent = parent
#         self._pool = QThreadPool(self._parent)

#     def run_task(self, task: Worker):
#         thread = QThread(self._parent)
#         task.moveToThread(thread)
#         self._pool.start()
#         thread.started.connect(task.run)

