from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class PromptMessageRole(Enum):
    """
    Enum class for prompt message.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

    @classmethod
    def value_of(cls, value: str) -> "PromptMessageRole":
        """
        Get value of given mode.

        :param value: mode value
        :return: mode
        """
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"invalid prompt message type value {value}")


class PromptMessageTool(BaseModel):
    """
    Model class for prompt message tool.
    """

    name: str

    description: str
    parameters: dict


class PromptMessageFunction(BaseModel):
    """
    Model class for prompt message function.
    """

    type: str = "function"
    function: PromptMessageTool


class PromptMessageContentType(Enum):
    """
    Enum class for prompt message content type.
    """

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class PromptMessageContent(BaseModel):
    pass


class TextPromptMessageContent(PromptMessageContent):
    """
    Model class for text prompt message content.
    """

    type: Literal[PromptMessageContentType.TEXT] = PromptMessageContentType.TEXT
    data: str


class MultiModalPromptMessageContent(PromptMessageContent):
    """
    Model class for multi-modal prompt message content.
    """

    format: str = Field(default=..., description="the format of multi-modal file")
    base64_data: str = Field(default="", description="the base64 data of multi-modal file")
    url: str = Field(default="", description="the url of multi-modal file")
    mime_type: str = Field(default=..., description="the mime type of multi-modal file")

    @property
    def data(self):
        return self.url or f"data:{self.mime_type};base64,{self.base64_data}"


class VideoPromptMessageContent(MultiModalPromptMessageContent):
    type: Literal[PromptMessageContentType.VIDEO] = PromptMessageContentType.VIDEO


class AudioPromptMessageContent(MultiModalPromptMessageContent):
    type: Literal[PromptMessageContentType.AUDIO] = PromptMessageContentType.AUDIO


class ImagePromptMessageContent(MultiModalPromptMessageContent):
    class DETAIL(Enum):
        LOW = "low"
        HIGH = "high"

    type: Literal[PromptMessageContentType.IMAGE] = PromptMessageContentType.IMAGE
    detail: DETAIL = DETAIL.LOW


class DocumentPromptMessageContent(MultiModalPromptMessageContent):
    type: Literal[PromptMessageContentType.DOCUMENT] = PromptMessageContentType.DOCUMENT


PromptMessageContentUnionTypes = Annotated[
    Union[
        TextPromptMessageContent,
        ImagePromptMessageContent,
        DocumentPromptMessageContent,
        AudioPromptMessageContent,
        VideoPromptMessageContent,
    ],
    Field(discriminator="type"),
]


class PromptMessage(BaseModel):
    """
    Model class for prompt message.
    """

    role: PromptMessageRole
    content: Optional[str | list[PromptMessageContentUnionTypes]] = None
    name: Optional[str] = None

    def is_empty(self) -> bool:
        """
        Check if prompt message is empty.

        :return: True if prompt message is empty, False otherwise
        """
        return not self.content

    @field_validator("content", mode="before")
    @classmethod
    def transform_content(
        cls, value: list[dict] | Sequence[PromptMessageContent] | str | None
    ) -> Optional[str | list[PromptMessageContent]]:
        """
        Transform content to list of prompt message content.
        """
        if isinstance(value, str):
            return value
        else:
            result = []
            for content in value or []:
                if isinstance(content, PromptMessageContent):
                    result.append(content)
                    continue
                if content.get("type") == PromptMessageContentType.TEXT.value:
                    result.append(TextPromptMessageContent(**content))
                elif content.get("type") == PromptMessageContentType.IMAGE.value:
                    result.append(ImagePromptMessageContent(**content))
                elif content.get("type") == PromptMessageContentType.DOCUMENT.value:
                    result.append(DocumentPromptMessageContent(**content))
                elif content.get("type") == PromptMessageContentType.AUDIO.value:
                    result.append(AudioPromptMessageContent(**content))
                elif content.get("type") == PromptMessageContentType.VIDEO.value:
                    result.append(VideoPromptMessageContent(**content))
            return result


class UserPromptMessage(PromptMessage):
    """
    Model class for user prompt message.
    """

    role: PromptMessageRole = PromptMessageRole.USER


class AssistantPromptMessage(PromptMessage):
    """
    Model class for assistant prompt message.
    """

    class ToolCall(BaseModel):
        """
        Model class for assistant prompt message tool call.
        """

        class ToolCallFunction(BaseModel):
            """
            Model class for assistant prompt message tool call function.
            """

            name: str
            arguments: str

        id: str
        type: str
        function: ToolCallFunction

        @field_validator("id", mode="before")
        @classmethod
        def transform_id_to_str(cls, value) -> str:
            if not isinstance(value, str):
                return str(value)
            else:
                return value

    role: PromptMessageRole = PromptMessageRole.ASSISTANT
    tool_calls: list[ToolCall] = []

    def is_empty(self) -> bool:
        """
        Check if prompt message is empty.

        :return: True if prompt message is empty, False otherwise
        """
        return not (not super().is_empty() and not self.tool_calls)


class SystemPromptMessage(PromptMessage):
    """
    Model class for system prompt message.
    """

    role: PromptMessageRole = PromptMessageRole.SYSTEM


class ToolPromptMessage(PromptMessage):
    """
    Model class for tool prompt message.
    """

    role: PromptMessageRole = PromptMessageRole.TOOL
    tool_call_id: str

    def is_empty(self) -> bool:
        """
        Check if prompt message is empty.

        :return: True if prompt message is empty, False otherwise
        """
        return not (not super().is_empty() and not self.tool_call_id)
