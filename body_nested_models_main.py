from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI()

# class Item(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     tax: float | None = None
#     # tags: list[str] = []
    
#     # With this, even if you receive a request with duplicate data, it will be 
#     # converted to a set of unique items. And whenever you output that data, 
#     # even if the source had duplicates, it will be output as a set of unique 
#     # items. And it will be annotated / documented accordingly too.
#     tags: set[str] = set()

# @app.put("/items/{item_id}")
# async def update_item(item_id: int, item: Item):
#     results = {"item_id": item_id, "item": item}
#     return results


# ———————————————————— Nested Models ————————————————————
# Each attribute of a Pydantic model has a type. But that type can itself be 
# another Pydantic model. So, you can declare deeply nested JSON "objects" with specific attribute names, types and validations.

class Image(BaseModel):
    url: HttpUrl
    name: str
    
# class Item(BaseModel):
#     name: str
#     description: str | None = None
#     price: float
#     tax: float | None = None
#     tags: set[str] = set()
#     image: Image | None = None
    
# @app.put("/items/{item_idd}")
# async def update_item(item_id: int, item: Item):
#     results = {"item_id": item_id, "item": item}
#     return results

# This would mean that FastAPI would expect a body similar to:
# {
#     "name": "Foo",
#     "description": "The pretender",
#     "price": 42.0,
#     "tax": 3.2,
#     "tags": ["rock", "metal", "bar"],
#     "image": {
#         "url": "http://example.com/baz.jpg",
#         "name": "The Foo live"
#     }
# }

#  ———————————————————— Deeply Nested Models ———————————————————— 
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()
    image: list[Image] | None = None
    
class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item]
    
@app.put("/offers/")
async def create_offer(offer: Offer):
    return offer

#  ———————————————————— Bodies of pure lists ————————————————————
@app.put("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images

#  ———————————————————— Bodies of arbitrary dicts ————————————————————
# You can also declare a body as a dict with keys of some type and values of 
# some other type. This way, you don't have to know beforehand what the valid 
# field/attribute names are (as would be the case with Pydantic models).
# This would be useful if you want to receive keys that you don't already know.
# Another useful case is when you want to have keys of another type (e.g., int).
# That's what we are going to see here.
# In this case, you would accept any dict as long as it has int keys with float values:
@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    return weights

# Keep in mind that JSON only supports str as keys.
# But Pydantic has automatic data conversion.
# This means that, even though your API clients can only send strings as keys, 
# as long as those strings contain pure integers, Pydantic will convert them 
# and validate them. And the dict you receive as weights will actually have int keys and float values.

