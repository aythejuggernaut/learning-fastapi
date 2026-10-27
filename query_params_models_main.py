from datetime import date
from typing import Annotated, Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

app = FastAPI()

# —————————— Forbid Extra Query Parameters ——————————
# class FilterParams(BaseModel):
#     model_config = {"extra": "forbid"}
    
#     limit: int = Field(100, gt=0, le=100)
#     offset: int = Field(0, ge=0)
#     order_by: Literal["created_at", "updated_at"] = "created_at"
#     tags: list[str] = []
    
# @app.get('/items/')
# async def read_items(filter_query: Annotated[FilterParams, Query()]):
#     return filter_query

# —————————— Combine Parameter Models ——————————
# You can declare multiple query parameter models, and combine them with 
# individual query parameters or dependencies.
# class Pagination(BaseModel):
#     limit: int = Field(10, ge=1)
#     offset: int = Field(0, ge=0)

# class Filters(BaseModel):
#     tags: list[str] = []
    
# @app.get("/items/")
# def read_items(
#     pagination: Annotated[Pagination, Query()],
#     filters: Annotated[Filters, Query()],
#     search: str | None = None,
# ):
#     return {"pagination": pagination, "filters": filters, "search": search}
# https://example.com/items/?limit=5&offset=10&tags=red&tags=blue&search=shirt
# There are no pagination or filters keys in the query string. Each model validates the query parameters independently, with its own defaults, field validators, and model validators. The same applies when the models or individual parameters are declared in dependencies.

# If models share a parameter name or alias, each model validates that request parameter independently. Use distinct names or aliases for independent values. OpenAPI lists a shared parameter once, as it does for parameters shared with dependencies, so shared declarations should describe the same type and constraints.

# Each model's extra configuration applies to all query parameters, including those declared in other models or dependencies. With extra="forbid", any parameter outside that model is rejected. With extra="allow", those parameters are included as model extras.

# —————————— Optional Query Parameter Models ——————————
class DateRange(BaseModel):
    start: date
    end: date
    
@app.get("/items/")
async def read_items(
    limit: int = 10,
    date_range: Annotated[DateRange | None, Query()] = None,
): 
    return {"limit": limit, "date_range": date_range}

# If neither start nor end is sent, date_range is None. If either is sent, FastAPI validates the model and requires both fields.
# Using | None without a default still makes the parameter required.
# Extra parameters follow the model's extra configuration. Ignored extras do not make the model present.

