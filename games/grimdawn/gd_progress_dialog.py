import os
from typing import Callable, Optional

from PyQt6.QtCore import Qt, QTimer, qDebug
from PyQt6.QtWidgets import QProgressDialog, QWidget

from .gd_data import MultiStepProgress, Progress


class GdProgressDialog(QProgressDialog):
    class Closed:
        _callbacks: list[Callable[[], None]] = []

        def callbacks(self):
            return self._callbacks

        def connect(self, callable: Callable[[], None] | None):
            # self._callbacks = []
            if callable:
                self._callbacks.append(callable)

    closed = Closed()

    _parent: QWidget | None
    _delay_close_msec: int
    _auto_close: bool

    def __init__(
        self,
        parent: QWidget | None = None,
        labelText: str = "Processing...",
        allowCancel: bool = True,
        cancelButtonText: str = "Cancel",
        delayShowMsec: int = 500,
        delayCloseMsec: int = 0,
        autoClose: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setLabelText(labelText)
        self._auto_close = autoClose
        # self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self._delay_close_msec = delayCloseMsec
        self.setMinimumDuration(delayShowMsec)
        self.setAutoClose(False)
        if not allowCancel:
            self.setCancelButton(None)
        else:
            self.setCancelButtonText(cancelButtonText)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def on_step_update(self, progress_update: MultiStepProgress):
        msg = (
            progress_update.step_status_msg()
            + os.linesep
            + progress_update.status_message()
        )

        if (
            self._auto_close
            and progress_update.step_progress() == progress_update.step_max_progress()
        ):
            if progress_update.progress() == progress_update.max_progress():
                self._on_finished(
                    progress_update.progress(), progress_update.max_progress(), msg
                )
                return

        self._update_progress(
            progress_update.progress(), progress_update.max_progress(), msg
        )

    def on_steps_finished(self, progress_update: MultiStepProgress):
        msg = (
            progress_update.step_status_msg()
            + os.linesep
            + progress_update.status_message()
        )
        self._on_finished(
            progress_update.step_progress(), progress_update.step_max_progress(), msg
        )

    def on_progress_update(self, progress_update: Progress):
        if (
            self._auto_close
            and progress_update.progress() == progress_update.max_progress()
        ):
            self._on_finished(
                progress_update.progress(),
                progress_update.max_progress(),
                progress_update.status_message(),
            )
        else:
            self._update_progress(
                progress_update.progress(),
                progress_update.max_progress(),
                progress_update.status_message(),
            )

    def on_finished(self, progress_update: Progress):
        self._on_finished(
            progress_update.progress(),
            progress_update.max_progress(),
            progress_update.status_message(),
        )

    def _update_progress(
        self,
        progress: Optional[int],
        max_progress: Optional[int],
        message: Optional[str],
    ):
        if progress:
            self.setValue(progress)
        if max_progress:
            self.setMaximum(max_progress)
        if message:
            self.setLabelText(message)

    def _on_finished(
        self,
        progress: Optional[int],
        max_progress: Optional[int],
        message: Optional[str],
    ):
        # If a delay is set, then delay closing
        if self._delay_close_msec:
            # If set to autoclose and progress is 100%, then disable autoClose before setting progress to avoid the dialog closing itself immediately.
            if self.autoClose() and progress and progress == max_progress:
                self.setAutoClose(False)
            self._update_progress(progress, max_progress, message)
            # Schedule this dialog to be closed
            qDebug(
                f"Delaying close of progress window by {self._delay_close_msec} ms. autoClose={self.autoClose()}"
            )
            QTimer(self).singleShot(self._delay_close_msec, self._close)  # type: ignore
            return

        self._update_progress(progress, max_progress, message)
        if (progress and progress != max_progress) or not self.autoClose():
            self._close()

    def _close(self):
        qDebug("Closing GDProgressDialog")
        calls = self.closed.callbacks()
        for c in calls:
            c()
        self.close()
