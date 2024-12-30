import os
from PyQt6.QtWidgets import QWidget, QProgressDialog
from PyQt6.QtCore import Qt, QTimer
from typing import Optional
from .gd_data import Progress, MultiStepProgress

class GdProgressDialog(QProgressDialog):
    _parent: QWidget
    _delay_close_msec: int
    def __init__(self, 
                 parent: QWidget, 
                 labelText: str = "Processing...",
                 allowCancel: bool = True, 
                 cancelButtonText: str = "Cancel",
                 delayCloseMsec: int = 0,
                 autoClose: bool = True,
                 minimum: int = 0, 
                 maximum: int = 0) -> None: 
        super().__init__(
                labelText,
                cancelButtonText,
                minimum,
                maximum,
                parent
            )
        self._delay_close_msec = delayCloseMsec
        self.setAutoClose(autoClose)
        if not allowCancel:
            self.setCancelButton(None)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumDuration(1)

    def show(self):
        self.setMinimumDuration(1)

    def on_step_update(self, progress_update: MultiStepProgress):
        msg = progress_update.step_status_msg() + os.linesep + progress_update.status_message()
        self._update_progress(progress_update.progress(), progress_update.max_progress(), msg)
        
    def on_steps_finished(self, progress_update: MultiStepProgress):
        msg = progress_update.step_status_msg() + os.linesep + progress_update.status_message()
        self._update_progress(progress_update.progress(), progress_update.max_progress(), msg)
        self.close()

    def on_progress_update(self, progress_update: Progress):
        self._update_progress(progress_update.progress(), progress_update.max_progress(), progress_update.status_message())

    def _update_progress(self, progress: Optional[int], max_progress: Optional[int], message: Optional[str]):
        if progress:
            self.setValue(progress)
        if max_progress:
            self.setMaximum(max_progress)
        if message:
            self.setLabelText(message)
        
    def on_finished(self, progress_update: Progress):
        # If a delay is set, then delay closing
        if self._delay_close_msec:
            # If set to autoclose and progress is 100%, then disable autoClose before setting progress to avoid the dialog closing itself immediately.
            if self.autoClose() and progress_update.progress() == progress_update.max_progress():
                self.setAutoClose(False)
            self._update_progress(progress_update.progress(), progress_update.max_progress(), progress_update.status_message())
            # Schedule this dialog to be closed
            QTimer(self).singleShot(self._delay_close_msec, self.close)
            return
        
        self._update_progress(progress_update.progress(), progress_update.max_progress(), progress_update.status_message())
        if progress_update.progress() != progress_update.max_progress() or not self.autoClose():
            self.close()