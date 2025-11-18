from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
import os
import httpx
from pydantic import TypeAdapter
from fastmcp import FastMCP
from datetime import date
import base64
import logging

_EXPENSELM_API_ENDPOINT="https://api.expenselm.ai"
_EXPENSELM_TIMEOUT=60.0 # seconds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ImageDownloadRequest(BaseModel):
    expense_id: str
    thumbnail: Optional[bool] = False

class ImageDownloadResponse(BaseModel):
    expense_id: str
    image_data: str  # base64 encoded image
    content_type: str
    filename: str
    is_thumbnail: bool
    size_bytes: int

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
        "EXPENSELM_API_KEY": _get_api_key(),
        "X_CLIENT_TYPE": "mcp"
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

    Also for searching expenses by the provided criterias.

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

@mcp.tool()
async def download_expense_receipt_image(
    expense_id: str,
    thumbnail: bool = False,
) -> dict[str, Any]:
    """
    Download an expense receipt image from the backend API.
    
    Args:
        expense_id: The ID of the expense to download the receipt image for
        thumbnail: Whether to download the thumbnail version (default: False)
    
    Returns:
        dict containing the image data (base64 encoded), content type, and metadata
    """
    try:
        # Construct the API endpoint URL
        url = f"{_EXPENSELM_API_ENDPOINT}/expenses/{expense_id}/receipt-image"
        
        # Prepare headers
        headers = _get_headers()
        
        # Prepare query parameters
        params = {}
        if thumbnail:
            params["thumbnail"] = "true"
        
        logger.info(f"Downloading receipt image for expense: {expense_id}, thumbnail: {thumbnail}")
        
        # Make the HTTP request
        async with httpx.AsyncClient(timeout=_EXPENSELM_TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params)
            
            # Handle HTTP errors
            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Receipt image not found for expense ID: {expense_id}",
                    "error_code": "IMAGE_NOT_FOUND"
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Not authorized to access this expense",
                    "error_code": "FORBIDDEN"
                }
            elif response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "error_code": "HTTP_ERROR"
                }
            
            # Get image content
            image_bytes = response.content
            content_type = response.headers.get("content-type", "application/octet-stream")
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Extract filename from content-disposition header if available
            filename = "receipt_image"
            content_disposition = response.headers.get("content-disposition")
            if content_disposition and "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip('"')
            
            # Determine file extension from content type
            if content_type.startswith("image/"):
                extension = content_type.split("/")[-1]
                if extension in ["jpeg", "jpg", "png", "gif", "webp"]:
                    filename = f"{filename}.{extension}"
            
            logger.info(f"Successfully downloaded image: {len(image_bytes)} bytes, content-type: {content_type}")
            
            return {
                "success": True,
                "expense_id": expense_id,
                "image_data": image_base64,
                "content_type": content_type,
                "filename": filename,
                "is_thumbnail": thumbnail,
                "size_bytes": len(image_bytes),
                "encoding": "base64"
            }
            
    except httpx.TimeoutException:
        logger.error(f"Timeout while downloading image for expense: {expense_id}")
        return {
            "success": False,
            "error": "Request timeout while downloading image",
            "error_code": "TIMEOUT"
        }
    except httpx.RequestError as e:
        logger.error(f"Request error while downloading image for expense: {expense_id}: {e}")
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "error_code": "REQUEST_ERROR"
        }
    except Exception as e:
        logger.error(f"Unexpected error while downloading image for expense: {expense_id}: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNEXPECTED_ERROR"
        }

@mcp.tool()
async def save_expense_receipt_image(
    expense_id: str,
    save_path: str,
    thumbnail: bool = False
) -> dict[str, Any]:
    """
    Download and save an expense receipt image to a local file.
    
    Args:
        expense_id: The ID of the expense to download the receipt image for
        save_path: Local file path where the image should be saved
        thumbnail: Whether to download the thumbnail version (default: False)
    
    Returns:
        dict containing success status and file information
    """
    try:
        # First download the image
        download_result = await download_expense_receipt_image(
            expense_id=expense_id,
            thumbnail=thumbnail
        ) # type: ignore
        
        if not download_result.get("success"):
            return download_result
        
        # Decode base64 image data
        image_data = download_result["image_data"]
        image_bytes = base64.b64decode(image_data)
        
        # Save to file
        with open(save_path, "wb") as f:
            f.write(image_bytes)
        
        logger.info(f"Successfully saved image to: {save_path}")
        
        return {
            "success": True,
            "expense_id": expense_id,
            "file_path": save_path,
            "content_type": download_result["content_type"],
            "is_thumbnail": thumbnail,
            "size_bytes": len(image_bytes)
        }
        
    except IOError as e:
        logger.error(f"Failed to save image to {save_path}: {e}")
        return {
            "success": False,
            "error": f"Failed to save file: {str(e)}",
            "error_code": "FILE_SAVE_ERROR"
        }
    except Exception as e:
        logger.error(f"Unexpected error while saving image: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "UNEXPECTED_ERROR"
        }
    
@mcp.tool
async def get_expense_count_by_period(
        from_date: str,
        to_date: str
    ) -> int:
    """
    Get expense count for the provided period.

    Example usage: 
    When user want to perform analytics for a period, first use this method to
    get the count of total expenses first. Then can use the get_latest_expenses
    tool to fetch the expenses by page to get all records.

    Args:
        from_date (required): The start date for filtering. Format is YYYY-MM-DD.
        to_date (required): The end date for filtering. Format is YYYY-MM-DD.
    
    Returns:
        int: The count of expense reocrds for the period.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/stats/expense-count-by-period"

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
        
        r.raise_for_status()

        # The response is a raw integer, so we read the text and cast it to int.
        # Using r.text instead of r.json()
        expense_count = int(r.text)

    return expense_count

@mcp.tool
async def get_subscription_expense_count_by_period(
        from_date: str,
        to_date: str
    ) -> int:
    """
    Get subscription based expense count for the provided period.

    Example usage: 
    When user want to perform analytics of subscription based 
    expenses for a period, first use this method to
    get the count of total subscription based expenses first. 
    Then can use the get_latest_subscription_expenses
    tool to fetch the expenses by page to get all records.

    Args:
        from_date (required): The start date for filtering. Format is YYYY-MM-DD.
        to_date (required): The end date for filtering. Format is YYYY-MM-DD.
    
    Returns:
        int: The count of subscription based expense reocrds for the period.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/stats/subscription-expense-count-by-period"

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
        
        r.raise_for_status()

        # The response is a raw integer, so we read the text and cast it to int.
        # Using r.text instead of r.json()
        expense_count = int(r.text)

    return expense_count

def main():
    """Main entry point for the ExpenseLM MCP service."""
    try:
        logger.info("Starting ExpenseLM MCP service")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error starting ExpenseLM MCP service: {str(e)}")
        raise

if __name__ == "__main__":
    main()
