"""Interfaces for tool abstractions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, ClassVar, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class BaseToolInput(BaseModel):
    """Base class for tool input models."""
    model_config = {"extra": "forbid"}


class ToolContent(BaseModel):
    """Model for content in tool responses."""
    type: str = Field(default="text", description="Content type identifier")
    content_id: Optional[str] = Field(None, description="Optional content identifier")
    text: Optional[str] = Field(None, description="Text content when type='text'")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON data when type='json'")
    model: Optional[Any] = Field(None, exclude=True, description="Pydantic model instance")

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to handle model conversion."""
        if self.model and not self.json_data:
            if isinstance(self.model, BaseModel):
                self.json_data = self.model.model_dump()
                if not self.type or self.type == "text":
                    self.type = "json"


class ToolResponse(BaseModel):
    """Model for tool responses."""
    content: List[ToolContent]

    @classmethod
    def from_model(cls, model: BaseModel) -> "ToolResponse":
        return cls(
            content=[
                ToolContent(type="json", json_data=model.model_dump(), model=model)
            ]
        )

    @classmethod
    def from_text(cls, text: str) -> "ToolResponse":
        return cls(content=[ToolContent(type="text", text=text)])


class Tool(ABC):
    """Abstract base class for all tools."""
    name: ClassVar[str]
    description: ClassVar[str]
    input_model: ClassVar[Type[BaseToolInput]]
    output_model: ClassVar[Optional[Type[BaseModel]]] = None

    @abstractmethod
    async def execute(self, input_data: BaseToolInput) -> ToolResponse:
        pass

    def get_schema(self) -> Dict[str, Any]:
        schema = {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
        }
        if self.output_model:
            schema["output"] = self.output_model.model_json_schema()
        return schema
