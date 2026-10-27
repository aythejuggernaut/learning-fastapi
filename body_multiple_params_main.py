from typing import Annotated
from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class User(BaseModel):
    username: str
    full_name: str | None = None
    
# @app.put("/items/{item_id}")
# async def update_item(item_id: int, item: Item, user: User):
#     results = {"item_id": item_id, "item": item, "user": user}
#     return results

# In this case, FastAPI will notice that there is more than one body parameter 
# in the function (there are two parameters that are Pydantic models). 
# So, it will then use the parameter names as keys (field names) in the body, and expect a body like:
# {
#     "item": {
#         "name": "Foo",
#         "description": "The pretender",
#         "price": 42.0,
#         "tax": 3.2
#     },
#     "user": {
#         "username": "dave",
#         "full_name": "Dave Grohl"
#     }
# }

# —————————— Singular values in body ——————————
# The same way there is a Query and Path to define extra data for query and 
# path parameters, FastAPI provides an equivalent Body.
# For example, extending the previous model, you could decide that you want to 
# have another key importance in the same body, besides the item and user.
# If you declare it as is, because it is a singular value, FastAPI will assume that it is a query parameter.
# But you can instruct FastAPI to treat it as another body key using Body:

# @app.put("/items/{item_id}")
# async def update_item(
#     item_id: int, item: Item, user: User, importance: Annotated[int, Body()]
# ):
#     results = {"item_id": item_id, "item": item, "user": user}
#     return results

# {
#     "item": {
#         "name": "Foo",
#         "description": "The pretender",
#         "price": 42.0,
#         "tax": 3.2
#     },
#     "user": {
#         "username": "dave",
#         "full_name": "Dave Grohl"
#     },
#     "importance": 5
# }

# —————————— Multiple body params and query ——————————
# Of course, you can also declare additional query parameters whenever you need, additional to any body parameters.
# As, by default, singular values are interpreted as query parameters, you don't have to explicitly add a Query, you can just do:
# q: str | None = None
# @app.put("/items/{item_id}")
# async def update_item(
#     *,
#     item_id: int, 
#     item: Item, 
#     user: User, 
#     importance: Annotated[int, Body(gt=0)],
#     q: str | None = None
# ):
#     results = {"item_id": item_id, "item": item, "user": user}
#     if q:
#         results.update({"q": q})
#     return results


# —————————— Embedd a single body parameter ——————————
# Let's say you only have a single item body parameter from a Pydantic model 
# Item. By default, FastAPI will then expect its body directly.
# But if you want it to expect a JSON with a key item and inside of it the 
# model contents, as it does when you declare extra body parameters, you can 
# use the special Body parameter embed:
@app.put("/items/{item_id}")
async def update_item(
    item_id: int, item: Annotated[Item, Body(embed=True)]
):
    results = {"item_id": item_id, "item": item}
    return results

# In this case FastAPI will expect a body like:
# {
#     "item": {
#         "name": "Foo",
#         "description": "The pretender",
#         "price": 42.0,
#         "tax": 3.2
#     }
# }

# instead of:
# {
#     "name": "Foo",
#     "description": "The pretender",
#     "price": 42.0,
#     "tax": 3.2
# }

# You can add multiple body parameters to your path operation function, even 
# though a request can only have a single body. But FastAPI will handle it, 
# give you the correct data in your function, and validate and document the 
# correct schema in the path operation. You can also declare singular values to 
# be received as part of the body. And you can instruct FastAPI to embed the body in a key even when there is only a single parameter declared.

