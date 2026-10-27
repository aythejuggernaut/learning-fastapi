from typing import Annotated
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field

app = FastAPI()

# class Item(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     tax: float | None = None

#     model_config = {
#         'json_schema_extra': {
#             "examples": [
#                 {
#                     "name": "Foo",
#                     "description": "A very nice Item",
#                     "price": 35.4,
#                     "tax": 3.2,
#                 }
#             ]
#         }
#     }
    
# @app.put("/items/{item_id}")
# async def update_items(item_id: int, item: Item):
#     results = { "item_id": item_id, "item": item}
#     return results


# ——————————————————— Field additional arguments ———————————————————
# class Item(BaseModel):
#     name: str = Field(examples=["Foo"])
#     description: str | None = Field(default=None, examples=["A very nice item"])
#     price: float = Field(examples=[35.4])
#     tax: float | None = Field(default=None, examples=[3.2])

# @app.put("/items/{item_id}")
# async def update_item(item_id: int, item: Item):
#     results = {"item_id": item_id, "item": item}
#     return results

# ——————————————————— Body with multiple examples ———————————————————
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    
# @app.put("/items/{item_id}")
# async def update_item(
#     *,
#     item_id: int, 
#     item: Annotated[
#         Item,
#         Body(
#             examples=[
                # {
                #     "name": "Foo",
                #     "description": "A very nice Item",
                #     "price": 35.4,
                #     "tax": 3.2,
                # },
#                 {
#                     "name": "Bar",
#                     "price": "35.4",
#                 },
#                 {
#                     "name": "Baz",
#                     "price": "thirty five point four",
#                 },
#             ]
#         )
#     ]
# ):
#     results = {"item_id": item_id, "item": item}
#     return results
# When you do this, the examples will be part of the internal JSON Schema for 
# that body data. Nevertheless, at the time of writing this, Swagger UI, the 
# tool in charge of showing the docs UI, doesn't support showing multiple 
# examples for the data in JSON Schema. But read below for a workaround.


# ——————————————————— OpenAPI-specific examples ———————————————————
# Since before JSON Schema supported examples, OpenAPI had support for a  
# different field also called examples. The shape of this OpenAPI-specific
# field examples is a dict with multiple examples (instead of a list), each 
# with extra information that will be added to OpenAPI too.
# This doesn't go inside of each JSON Schema contained in OpenAPI, this goes 
# outside, in the path operation directly.

@app.put("/items/{item_id}")
async def update_item(
    *,
    item_id: int, 
    item: Annotated[
        Item,
        Body(
            openapi_examples={
                "normal": {
                    "summary": "A normal example",
                    "description": " A **normal** item works correctly",
                    "value": {
                        "name": "Foo",
                        "description": "A very nice Item",
                        "price": 35.4,
                        "tax": 3.2,
                    }
                },
                "converted": {
                    "summary": "An example with converted data",
                    "description": "FastAPI can convert price `strings` to actual `numbers` automatically",
                    "value": {
                        "name": "Bar",
                        "price": "35.4",
                    },
                },
                "invalid": {
                    "summary": "Invalid data is rejected with an error",
                    "value": {
                        "name": "Baz",
                        "price": "thirty five point four",
                    },
                },
            }
        )
    ]
):
    results = {"item_id": item_id, "item": item}
    return

# Each specific example dict in the examples can contain:
# - summary: Short description for the example.
# - description: A long description that can contain Markdown text.
# - value: This is the actual example shown, e.g. a dict.
# - externalValue: alternative to value, a URL pointing to the example. Although this might not be supported by as many tools as value.

