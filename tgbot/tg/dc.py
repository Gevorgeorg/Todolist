from dataclasses import dataclass, field
from typing import List, Optional
from dataclasses_json import dataclass_json, config
from marshmallow import EXCLUDE


@dataclass_json
@dataclass
class Chat:
    id: int
    type: str
    first_name: Optional[str] = None
    username: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None


@dataclass_json
@dataclass
class MessageFrom:
    id: int
    is_bot: bool
    first_name: str
    username: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


@dataclass_json
@dataclass
class Entity:
    offset: int
    length: int
    type: str


@dataclass_json
@dataclass
class Message:
    message_id: int
    date: int
    chat: Chat

    from_: Optional[MessageFrom] = field(
        default=None,
        metadata=config(
            field_name="from",
            letter_case=lambda x: "from"
        )
    )

    text: Optional[str] = None
    entities: Optional[List[Entity]] = None


@dataclass_json
@dataclass
class UpdateObj:
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    channel_post: Optional[Message] = None
    edited_channel_post: Optional[Message] = None


@dataclass_json
@dataclass
class GetUpdatesResponse:
    ok: bool
    result: List[UpdateObj]

    class Meta:
        unknown = EXCLUDE


@dataclass_json
@dataclass
class SendMessageResponse:
    ok: bool
    result: Message

    class Meta:
        unknown = EXCLUDE


@dataclass_json
@dataclass
class User:
    id: int
    is_bot: bool
    first_name: str
    username: Optional[str] = None
    can_join_groups: Optional[bool] = None
    can_read_all_group_messages: Optional[bool] = None
    supports_inline_queries: Optional[bool] = None


@dataclass_json
@dataclass
class GetMeResponse:
    ok: bool
    result: User

    class Meta:
        unknown = EXCLUDE
