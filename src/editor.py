from textual.app import ComposeResult
from textual import events
from textual.screen import Screen
from textual.message import Message
from textual.widgets import TextArea, Static


class EditorTextArea(TextArea):

    class Cancel(Message):
        pass

    class Save(Message):
        def __init__(self, code: str) -> None:
            self.code = code
            super().__init__()

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.post_message(self.Cancel())
            event.prevent_default()
        elif event.key == "ctrl+s":
            self.post_message(self.Save(self.text))
            event.prevent_default()


class EditorScreen(Screen[str | None]):
    BINDINGS = [
        ("ctrl+s", "apply_changes", "Update code & close"),
        ("escape", "app.pop_screen", "Cancel changes"),
    ]

    code: str = ""

    def compose(self) -> ComposeResult:
        yield EditorTextArea.code_editor(self.code, language="python")
        yield Static("Use ^s to save changes and close, Esc to cancel")

    def set_code(self, new_code: str) -> None:
        self.code = new_code

    def on_editor_text_area_save(self, message: EditorTextArea.Save):
        self.dismiss(message.code)

    def on_editor_text_area_cancel(self, message: EditorTextArea.Cancel):
        self.dismiss(None)
