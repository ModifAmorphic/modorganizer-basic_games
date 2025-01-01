from typing import Callable

from PyQt6.QtCore import QObject, QRunnable, QThread, pyqtSignal, qDebug

from .gd_data import MultiStepProgress, Progress
from .gd_progress_dialog import GdProgressDialog


class Task(QObject, QRunnable):
    started = pyqtSignal(Progress)
    progress = pyqtSignal(Progress)
    finished = pyqtSignal(Progress)

    def __init__(self):
        super().__init__()
    
    def run(self): ...

class MultiStepTask(Task):
    started = pyqtSignal(MultiStepProgress)
    progress = pyqtSignal(MultiStepProgress)
    finished = pyqtSignal(MultiStepProgress)

    def __init__(self):
        super(MultiStepTask, self).__init__()

class TaskMaster:
    _parent: QObject | None
    _thread: QThread
    _task: Task
    _task_started: bool
    _is_finished: bool
    def thread(self): 
        return self._thread
    def task(self): return self._task

    def __init__(self, task: Task, parent: QObject | None = None, progress_dialog: GdProgressDialog | None = None, **kwargs):
        super(TaskMaster, self).__init__(**kwargs)
        self._task_started = False
        self._is_finished = False
        self._parent = parent
        self._thread, self._task = self._bind_task(task)
        if progress_dialog:
            self.bind_dialog(progress_dialog)

    def _bind_task(self, task: Task) -> tuple[QThread, Task]:
        qDebug("Creating new QThread and binding task TaskMaster")
        thread = QThread(self._parent)
        task.moveToThread(thread)
        thread.started.connect(task.run)
        # task.finished.connect(task.deleteLater)
        task.finished.connect(task.deleteLater)
        task.finished.connect(thread.quit)
        thread.finished.connect(self._set_is_finished)
        # thread.finished.connect(thread.deleteLater)

        return thread, task
    
    def _set_is_finished(self):
        self._is_finished = True

    def bind_dialog(self, dialog: GdProgressDialog):
        qDebug("Binding progress dialog to TaskMaster")
        if isinstance(self._task, MultiStepTask):
            self._task.progress.connect(dialog.on_step_update)
            self._task.finished.connect(dialog.on_steps_finished)
        else:
            self._task.progress.connect(dialog.on_progress_update)
            self._task.finished.connect(dialog.on_finished)
        
        return dialog

    def start_task(self) -> QThread:
        if self._task_started:
            raise RuntimeError("Task has already been started. Tasks can only be ran once.")
        self._thread.start()
        self._task_started = True
        return self.thread()
    
    def is_started(self): return self._task_started
    def is_finished(self): return self._is_finished
    
    
    
class SimpleTask[T](TaskMaster, Task):
    started = pyqtSignal(Progress)
    progress = pyqtSignal(Progress)
    finished = pyqtSignal(Progress)
    result = pyqtSignal(object)
    _result: T

    
    def __init__(self, runnable: Callable[[], T], start_msg: str = "Started", finish_msg: str = "Finished", parent: QObject | None = None, progress_dialog: GdProgressDialog | None = None):
        # qDebug("Initializing SimpleTask")
        super(SimpleTask, self).__init__(task=self, parent=parent, progress_dialog=progress_dialog)
        # super(SimpleTask, self).__init__()
        self._runnable = runnable
        self._start_msg = start_msg
        self._finish_msg = finish_msg
        # qDebug(f"Done initializing SimpleTask with runnable {self._runnable}")
    
    def run(self):
        qDebug(f"Starting runnable task {self._runnable}")
        self.started.emit(Progress(0, 1, self._start_msg))
        self._result = self._runnable()
        self.result.emit(self._result)
        self.finished.emit(Progress(1, 1, self._finish_msg))
        # qDebug("Runnable task finished")
    
    def task_result(self) -> T: return self._result