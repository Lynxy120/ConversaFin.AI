from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Base(BaseModel):
    # Meta adds undocumented fields (from_user_id, internal_1p_only_data, ...). Never fail on them.
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Profile(_Base):
    name: str | None = None
    username: str | None = None


class Contact(_Base):
    wa_id: str | None = None
    user_id: str | None = None
    profile: Profile | None = None


class Metadata(_Base):
    display_phone_number: str | None = None
    phone_number_id: str | None = None


class TextBody(_Base):
    body: str = ""


class MediaBody(_Base):
    id: str | None = None
    mime_type: str | None = None
    sha256: str | None = None
    caption: str | None = None
    filename: str | None = None
    voice: bool | None = None


class InteractiveReply(_Base):
    id: str | None = None
    title: str | None = None
    description: str | None = None


class Interactive(_Base):
    type: str | None = None
    button_reply: InteractiveReply | None = None
    list_reply: InteractiveReply | None = None


class ButtonPayload(_Base):
    text: str | None = None
    payload: str | None = None


class MessageContext(_Base):
    from_: str | None = Field(default=None, alias="from")
    id: str | None = None


class OrderItem(_Base):
    product_retailer_id: str
    quantity: int = 1
    item_price: float | None = None
    currency: str | None = None


class OrderPayload(_Base):
    catalog_id: str | None = None
    text: str | None = None
    product_items: list[OrderItem] = Field(default_factory=list)


class Message(_Base):
    from_: str = Field(
        default="", alias="from"
    )  # filled from contacts by ChangeValue if Meta omits it
    from_user_id: str | None = None
    user_id: str | None = None
    id: str
    timestamp: str | int | None = None
    type: str = "unknown"
    text: TextBody | None = None
    image: MediaBody | None = None
    audio: MediaBody | None = None
    document: MediaBody | None = None
    interactive: Interactive | None = None
    button: ButtonPayload | None = None
    context: MessageContext | None = None
    order: OrderPayload | None = None

    @property
    def body_text(self) -> str:
        if self.text:
            return self.text.body
        if self.order and self.order.text:
            return self.order.text
        if self.interactive:
            r = self.interactive.button_reply or self.interactive.list_reply
            if r and r.title:
                return r.title
        if self.button and (self.button.text or self.button.payload):
            return self.button.text or self.button.payload or ""
        for media in (self.image, self.document):
            if media and media.caption:
                return media.caption
        return ""

    @property
    def reply_id(self) -> str | None:
        if self.interactive:
            r = self.interactive.button_reply or self.interactive.list_reply
            if r and r.id:
                return r.id
        return self.button.payload if self.button else None


class StatusError(_Base):
    code: int | None = None
    title: str | None = None
    message: str | None = None


class Status(_Base):
    id: str
    status: str
    timestamp: str | int | None = None
    recipient_id: str | None = None
    errors: list[StatusError] = Field(default_factory=list)


class ChangeValue(_Base):
    messaging_product: str | None = None
    metadata: Metadata | None = None
    contacts: list[Contact] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    statuses: list[Status] = Field(default_factory=list)

    @model_validator(mode="after")
    def _fill_sender(self) -> "ChangeValue":
        contact = next((c.wa_id for c in self.contacts if c.wa_id), "")
        for m in self.messages:
            if not m.from_:
                m.from_ = contact or m.from_user_id or m.user_id or ""
        return self


class Change(_Base):
    field: str
    value: ChangeValue


class Entry(_Base):
    id: str
    changes: list[Change] = Field(default_factory=list)


class WebhookPayload(_Base):
    object: str
    entry: list[Entry] = Field(default_factory=list)
