# discover_model.py
from pydantic import ConfigDict, Field
from mcp_server.interfaces.tool import BaseToolInput


class DiscoverInput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"query": "LG 55UK6300"},
                {"query": "Samsung QN90A"},
            ]
        }
    )

    query: str = Field(
        ..., description="Brand and model", examples=["LG 55UK6300", "Samsung QN90A"]
    )


class Candidate(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "lg_55uk6300_nec1",
                    "brand": "LG",
                    "model": "55UK6300",
                },
                {
                    "id": "samsung_qn90a_nec",
                    "brand": "Samsung",
                    "model": "QN90A",
                },
            ]
        }
    )

    id: str = Field(
        ...,
        description="Stable identifier for this code set.",
        examples=["lg_55uk6300_nec1", "samsung_qn90a_nec"],
    )
    brand: str = Field(..., description="Device brand.", examples=["LG", "Samsung"])
    model: str = Field(..., description="Device model.", examples=["55UK6300", "QN90A"])


class DiscoverOutput(BaseToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "id": "lg_55uk6300_nec1",
                            "brand": "LG",
                            "model": "55UK6300",
                        },
                        {
                            "id": "samsung_qn90a_nec",
                            "brand": "Samsung",
                            "model": "QN90A",
                        },
                    ]
                }
            ]
        }
    )

    candidates: list[Candidate] = Field(
        ...,
        description="List of candidate devices matching the query.",
        examples=[
            {
                "id": "lg_55uk6300_nec1",
                "brand": "LG",
                "model": "55UK6300",
            },
            {
                "id": "samsung_qn90a_nec",
                "brand": "Samsung",
                "model": "QN90A",
            },
        ],
    )
    message: str = Field(
        ...,
        description="Additional information about the discovery process.",
        examples=["2 candidates found", "No candidates found"],
    )


