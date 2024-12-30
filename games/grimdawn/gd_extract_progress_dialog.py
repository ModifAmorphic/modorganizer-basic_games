import os
from PyQt6.QtWidgets import QWidget, QProgressDialog
from PyQt6.QtCore import Qt
from typing import Callable, Optional
from .gd_data import ExtractStatus, Progress, MultiStepProgress

class ExtractProgressDialog(QProgressDialog):
    _parent: QWidget
    _callback_id: int
    _callback: Callable[[ExtractStatus, int], None]

    def __init__(self, 
                 parent: QWidget,
                 callback_id: int, 
                 labelText: str = "Extracting Database(s)", 
                 cancelButtonText: str = "Cancel",
                 minimum: int = 0, 
                 maximum: int = 0) -> None: 
        super().__init__(
                labelText,
                cancelButtonText,
                minimum,
                maximum,
                parent
            )
        self._callback_id = callback_id
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumDuration(0)

    def show(self):
        self.setMinimumDuration(0)

    def on_step_update(self, progress_update: MultiStepProgress):
        msg = progress_update.step_status_msg() + os.linesep + progress_update.status_message()
        self._update_progress(progress_update.progress(), progress_update.max_progress(), msg)
        
    def on_steps_finished(self, progress_update: MultiStepProgress):
        msg = progress_update.step_status_msg() + os.linesep + progress_update.status_message()
        self._update_progress(progress_update.progress(), progress_update.max_progress(), msg)
        self.close()

    def on_progress_update(self, progress_update: Progress, extraction_id: int):
        self._update_progress(progress_update.progress(), progress_update.max_progress(), progress_update.status_message())

    def on_extract_update(self, extract_status: ExtractStatus, extraction_id: int):
        if extraction_id != self._callback_id:
            return
        self._update_progress(extract_status.progress(), extract_status.max_progress(), extract_status.status_message(), not extract_status.is_running())

    def on_extractor_update(self, progress: int, message: Optional[str], max_progress: Optional[int], is_finished: bool = False):
        if (self.windowModality() != Qt.WindowModality.ApplicationModal):
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._update_progress(progress, max_progress, message, is_finished)

    def _update_progress(self, progress: int, max_progress: Optional[int], message: Optional[str], is_finished: bool = False):
        self.setValue(progress)
        # qDebug(f"Progress: {progress}/{max_progress}, Message: {message}")
        if max_progress:
            self.setMaximum(max_progress)
        if message:
            self.setLabelText(message)
        
        # if is_finished:
        #     self.close()