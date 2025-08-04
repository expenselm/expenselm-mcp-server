from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import os
import httpx
from pydantic import TypeAdapter
from fastmcp import FastMCP
from datetime import date

_EXPENSELM_API_ENDPOINT="https://api.expenselm.ai"
_EXPENSELM_TIMEOUT=60.0 # seconds

class ExpenseImageType(str, Enum):
    Receipt = "Receipt"
    Invoice = "Invoice"
    Others = "Others"

class ExpenseType(str, Enum):
    Standard = "Standard"
    Subscription = "Subscription"

class ExpenseImage(BaseModel):
    """
    Represents an image of an expense.
    """

    image_type: ExpenseImageType = Field(
        ..., description="The type of the expense image"
    )
    image_file_name: str = Field(..., description="The file name the expense image")

class ExpenseItem(BaseModel):
    """
    Represents an expense item within an expense.
    """

    name: str = Field("", description="The name of the item")
    quantity: float = Field(0, description="The quantity of the item")
    unit_price: float = Field(0, description="The unit price of the item")
    subtotal: float = Field(0, description="The subtotal of the item")

class Expense(BaseModel):
    """
    Represents an expense. It's the output from GenAI data extraction.
    """

    shop_name: str = Field("", description="The name of the shop")
    shop_address: str = Field("", description="The address of the shop")
    date: str = Field("", description="The date of the expense in ISO 8601 format")
    expense_category: str = Field("Misc", description="The category of the expense")
    currency: str = Field("", description="The currency of the expense")
    total_amount: float = Field(0, description="The total amount of the expense")
    items: list[ExpenseItem] = Field([], description="The items of the expense")
    expense_type: ExpenseType = Field(
        ExpenseType.Standard, description="The type of the expense"
    )
    remark: str = Field("", description="The remark of the expense")

class ExpenseImageData(BaseModel):
    """
    Represents the image and the extracted data of an expense.
    """

    image: Optional[ExpenseImage] = Field(None, description="The expense image")
    expense: Optional[Expense] = Field(None, description="The extracted expense data")

class ExpenseRecord(ExpenseImageData):
    """
    Represents a record of an expense.
    """

    id: str = Field(..., description="Unique identifier for the expense record")

class ExpenseSearchRequest(BaseModel):
    skip: int = Field(0, description="Offset for pagination")
    limit: int = Field(10, description="Limit for pagination", le=100, gt=0)
    text_input: Optional[str] = Field(None, description="Text for semantic search", min_length=2)
    from_date: Optional[date] = Field(None, description="Start date for filtering (YYYY-MM-DD)")
    to_date: Optional[date] = Field(None, description="End date for filtering (YYYY-MM-DD)")

class MonthCurAmtStatItem(BaseModel):
    month: str
    currency: str
    total_amount: float

class CategoryCurAmtStatItem(BaseModel):
    category: str
    currency: str
    total_amount: float

class SubscriptionCurAmtStatItem(BaseModel):
    subscription: str
    currency: str
    total_amount: float

mcp = FastMCP(name="Expense Assistant")

def _get_api_key() -> str:
    """
    Get the API key.

    Returns:
        str: The API key.
    """
    key = os.getenv("EXPENSELM_API_KEY")
    if key is None:
        raise ValueError("EXPENSELM_API_KEY is not set")

    return key

def _get_headers() -> dict[str, str]:
    """
    Get the headers.

    Returns:
        dict[str, str]: The headers.
    """
    return {
        "EXPENSELM_API_KEY": _get_api_key()
    }

@mcp.tool
async def get_latest_expenses(
        skip: int = 0, 
        limit: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        text_input: Optional[str] = None
    ) -> list[ExpenseRecord]:
    """
    Get the latest expense records.

    Args:
        skip (int): The number of records to skip. Default is 0.
        limit (int): The maximum number of records to return. Default is 10.
        from_date (Optional[date]): The start date for filtering. Default is None. Format is YYYY-MM-DD.
        to_date (Optional[date]): The end date for filtering. Default is None. Format is YYYY-MM-DD.
        text_input (Optional[str]): The text for semantic search. Default is None.
    
    Returns:
        list[ExpenseRecord]: The latest expense records.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/expenses/"

    search_params: dict[str, str | int] = {
        "skip": skip,
        "limit": limit,
    }

    if from_date:
        search_params["from_date"] = from_date

    if to_date:
        search_params["to_date"] = to_date

    if text_input:
        search_params["text_input"] = text_input

    async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client: 
        r = await client.get(
                api_endpoint, 
                headers=_get_headers(),
                params=search_params
            )

        adapter = TypeAdapter(list[ExpenseRecord])
        expenses = adapter.validate_python(r.json())

    return expenses

@mcp.tool
async def get_expense_by_id(
        id: str
    ) -> ExpenseImageData:
    """
    Get an expense record by id.

    Args:
        id: The id of the expense.
    
    Returns:
        ExpenseImageData: The expense record.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/expenses/{id}"

    async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client: 
        r = await client.get(
                api_endpoint, 
                headers=_get_headers()
            )

        expense_image_data = ExpenseImageData.model_validate_json(r.json())

    return expense_image_data

@mcp.tool
async def get_latest_subscription_expenses(
        skip: int = 0, 
        limit: int = 10,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        text_input: Optional[str] = None
    ) -> list[ExpenseRecord]:
    """
    Get the latest expense records related to regular subscriptions.

    Args:
        skip (int): The number of records to skip. Default is 0.
        limit (int): The maximum number of records to return. Default is 10.
        from_date (Optional[date]): The start date for filtering. Default is None. Format is YYYY-MM-DD.
        to_date (Optional[date]): The end date for filtering. Default is None. Format is YYYY-MM-DD.
        text_input (Optional[str]): The text for semantic search. Default is None.
    
    Returns:
        list[ExpenseRecord]: The latest subscription expense records.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/subscriptions/"

    search_params: dict[str, str | int] = {
        "skip": skip,
        "limit": limit,
    }

    if from_date:
        search_params["from_date"] = from_date

    if to_date:
        search_params["to_date"] = to_date

    if text_input:
        search_params["text_input"] = text_input

    async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client: 
        r = await client.get(
                api_endpoint, 
                headers=_get_headers(),
                params=search_params
            )

        adapter = TypeAdapter(list[ExpenseRecord])
        expenses = adapter.validate_python(r.json())

    return expenses

@mcp.tool
async def get_expense_summary_by_month_by_currency(
        from_date: str,
        to_date: str
    ) -> list[MonthCurAmtStatItem]:
    """
    Get expense summary by month and currency for the provided period.

    Args:
        from_date (required): The start date for filtering. Format is YYYY-MM-DD.
        to_date (required): The end date for filtering. Format is YYYY-MM-DD.
    
    Returns:
        list[MonthCurAmtStatItem]: The expense summary by month and currency. For month, the format is YYYY-MM.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/stats/summary-by-month-by-currency"

    search_params: dict[str, str] = {
        "from_date": from_date,
        "to_date": to_date,
    }

    async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client: 
        r = await client.get(
                api_endpoint, 
                headers=_get_headers(),
                params=search_params
            )

        adapter = TypeAdapter(list[MonthCurAmtStatItem])
        expense_stats = adapter.validate_python(r.json())

    return expense_stats

@mcp.tool
async def get_expense_summary_by_category_by_currency(
        from_date: str,
        to_date: str
    ) -> list[CategoryCurAmtStatItem]:
    """
    Get expense summary by category and currency for the provided period.

    Args:
        from_date (required): The start date for filtering. Format is YYYY-MM-DD.
        to_date (required): The end date for filtering. Format is YYYY-MM-DD.
    
    Returns:
        list[CategoryCurAmtStatItem]: The expense summary by category and currency.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/stats/summary-by-category-by-currency"

    search_params: dict[str, str] = {
        "from_date": from_date,
        "to_date": to_date,
    }

    async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client: 
        r = await client.get(
                api_endpoint, 
                headers=_get_headers(),
                params=search_params
            )

        adapter = TypeAdapter(list[CategoryCurAmtStatItem])
        expense_stats = adapter.validate_python(r.json())

    return expense_stats

@mcp.tool
async def get_expense_summary_by_subscription_by_currency(
        from_date: str,
        to_date: str
    ) -> list[SubscriptionCurAmtStatItem]:
    """
    Get expense summary by subscription and currency for the provided period.

    Args:
        from_date (required): The start date for filtering. Format is YYYY-MM-DD.
        to_date (required): The end date for filtering. Format is YYYY-MM-DD.
    
    Returns:
        list[SubscriptionCurAmtStatItem]: The expense summary by subscription and currency.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/stats/summary-by-subscription-by-currency"

    search_params: dict[str, str] = {
        "from_date": from_date,
        "to_date": to_date,
    }

    async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client: 
        r = await client.get(
                api_endpoint, 
                headers=_get_headers(),
                params=search_params
            )

        adapter = TypeAdapter(list[SubscriptionCurAmtStatItem])
        expense_stats = adapter.validate_python(r.json())

    return expense_stats

if __name__ == "__main__":
    mcp.run()
