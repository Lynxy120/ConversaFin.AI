from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Profile(_Base):
    name: str | None = None


class Contact(_Base):
    wa_id: str
    profile: Profile | None = None


class Metadata(_Base):
    display_phone_number: str | None = None
    phone_number_id: str | None = None


class TextBody(_Base):
    body: str


class MediaBody(_Base):
    id: str | None = None
    mime_type: str | None = None
    sha256: str | None = None
    caption: str | None = None
    filename: str | None = None


class InteractiveReply(_Base):
    id: str | None = None
    title: str | None = None
    description: str | None = None


class Interactive(_Base):
    type: str | None = None
    button_reply: InteractiveReply | None = None
    list_reply: InteractiveReply | None = None


class MessageContext(_Base):
    from_: str | None = Field(default=None, alias="from")
    id: str | None = None


class Message(_Base):
    from_: str = Field(alias="from")
    id: str
    timestamp: str | None = None
    type: str = "unknown"
    text: TextBody | None = None
    image: MediaBody | None = None
    audio: MediaBody | None = None
    document: MediaBody | None = None
    interactive: Interactive | None = None
    context: MessageContext | None = None

    @property
    def body_text(self) -> str:
        if self.text:
            return self.text.body
        if self.interactive:
            reply = self.interactive.button_reply or self.interactive.list_reply
            if reply and reply.title:
                return reply.title
        for media in (self.image, self.document):
            if media and media.caption:
                return media.caption
        return ""


class Status(_Base):
    id: str
    status: str
    timestamp: str | None = None
    recipient_id: str | None = None


class ChangeValue(_Base):
    messaging_product: str | None = None
    metadata: Metadata | None = None
    contacts: list[Contact] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    statuses: list[Status] = Field(default_factory=list)


class Change(_Base):
    field: str
    value: ChangeValue


class Entry(_Base):
    id: str
    changes: list[Change] = Field(default_factory=list)


class WebhookPayload(_Base):
    object: str
    entry: list[Entry] = Field(default_factory=list)