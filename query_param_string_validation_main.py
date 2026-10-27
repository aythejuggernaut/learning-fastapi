import random
from typing import Annotated
from fastapi import FastAPI, Query
from pydantic import AfterValidator

app = FastAPI()

data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}

# —————————— without Annotated ——————————
# @app.get("/items/")
# async def read_items(q: str | None = Query(default=None, max_length=50)):
#     results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
#     if q:
#         results.update({"q": q})
#     return results

# —————————— with Annotated ——————————
# @app.get("/items/")
# async def read_items(
#     q: Annotated[str | None, Query(min_length=3, max_length=50)] = None
# ):
#     results: dict[str, str | list[dict[str, str]]] = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
#     if q:
#         results.update({"q": q})
#     return results

# —————————— Query parameter list / multiple values ——————————
# @app.get("/items/")
# async def read_items(q: Annotated[list[str] | None, Query()] = None):
#     # http://localhost:8000/items/?q=foo&q=bar
#     # response => {"q": ["foo", "bar"]}
#     query_items = {"q": q}
#     return query_items


# —————————— Metadata ——————————
# @app.get("/items/")
# async def read_items(
#     q: Annotated[
#         str | None,
#         Query(
#             title="Query string",
#             description="Query string for the items to search in the database that have a good match",
#             min_length=3,
#         ),
#     ] = None,
# ):
#     results: dict[str, str | list[dict[str, str]]] = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
#     if q:
#         results.update({"q": q})
#     return results

# —————————— Alias parameters ——————————
# Imagine that you want the parameter to be item-query.
# Like in: http://127.0.0.1:8000/items/?item-query=foobaritems
# But item-query is not a valid Python variable name.

# @app.get("/items/")
# async def read_items(q: Annotated[str | None, Query(alias="item-query")] = None):
#     results: dict[str, str | list[dict[str, str]]] = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
#     if q:
#         results.update({"q": q})
#     return results

# —————————— Deprecated ——————————
# Now let's say you don't like this parameter anymore.
# You have to leave it there a while because there are clients using it, but you want the docs to clearly show it as deprecated. Then pass the parameter deprecated=True to Query:

# @app.get("/items/")
# async def read_items(
#     q: Annotated[
#         str | None,
#         Query(
#             alias="item-query",
#             title="Query string",
#             description="Query string for the items to search in the database that have a good match",
#             min_length=3,
#             max_length=50,
#             pattern="^fixedquery$",
#             deprecated=True
#         ),
#     ] = None
# ):
#     results: dict[str, str | list[dict[str, str]]] = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
#     if q:
#         results.update({"q": q})
#     return results

# —————————— Exclude parameters from OpenAPI ——————————
# To exclude a query parameter from the generated OpenAPI schema (and thus, from the automatic documentation systems), set the parameter include_in_schema of Query to False:

# @app.get("/items/")
# async def read_items(
#     hidden_query: Annotated[str | None, Query(include_in_schema=False)] = None,
# ):
#     if hidden_query:
#         return {"hidden_query": hidden_query}
#     else:
#         return {"hidden_query": "Not found"}


# —————————— Custom Validation ——————————
def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError(
            'Invalid ID format, it must start with "isbn-" or "imdb-'
        )
    return id

@app.get("/items/")
async def read_items(
    id: Annotated[str | None, AfterValidator(check_valid_id)] = None,
): 
    if id:
        item = data.get(id)
    else:
        id, item = random.choice(list(data.items()))
    return {"id": id, "name": item}

