from pydantic import BaseModel, ConfigDict, Field


class _B(BaseModel):
    model_config = ConfigDict(
        extra="ignore", populate_by_name=True
    )  # Telegram adds fields freely


class User(_B):
    id: int
    is_bot: bool = False
    first_name: str = ""
    last_name: str | None = None
    username: str | None = None


class Chat(_B):
    id: int
    type: str = "private"


class PhotoSize(_B):
    file_id: str
    width: int = 0
    height: int = 0
    file_size: int | None = None


class Voice(_B):
    file_id: str
    duration: int = 0
    mime_type: str | None = None
    file_size: int | None = None


class Document(_B):
    file_id: str
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


class Message(_B):
    message_id: int
    from_: User | None = Field(default=None, alias="from")
    chat: Chat
    date: int = 0
    text: str | None = None
    caption: str | None = None
    photo: list[PhotoSize] | None = None
    voice: Voice | None = None
    audio: Voice | None = None
    document: Document | None = None

    @property
    def body(self) -> str:
        return self.text or self.caption or ""


class CallbackQuery(_B):
    id: str
    from_: User = Field(alias="from")
    message: Message | None = None
    data: str | None = None


class Update(_B):
    update_id: int
    message: Message | None = None
    callback_query: CallbackQuery | None = None
