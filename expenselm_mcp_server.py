import random
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import os
import json
import httpx
from pydantic import TypeAdapter
from fastmcp import FastMCP

_EXPENSELM_API_ENDPOINT="https://api.expenselm.ai"

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

expenses = """
[
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-8a928697-96ef-476c-8fdc-9344ec36fa44.jpg"
    },
    "expense": {
      "shop_name": "Taste",
      "shop_address": "Shop No. 401, Level 4 and Entrance Lobby on Level 3, Plaza Hollywood",
      "date": "2025-07-30",
      "expense_category": "Groceries",
      "currency": "HKD",
      "total_amount": 132.6,
      "items": [
        {
          "name": "雞柳",
          "quantity": 1,
          "unit_price": 55.9,
          "subtotal": 55.9
        },
        {
          "name": "特大裝鮮橙",
          "quantity": 6,
          "unit_price": 9,
          "subtotal": 54
        },
        {
          "name": "Buy 3 Save $3.1",
          "quantity": 1,
          "unit_price": -6.2,
          "subtotal": -6.2
        },
        {
          "name": "特大艾菲蘋果",
          "quantity": 3,
          "unit_price": 14.9,
          "subtotal": 44.7
        },
        {
          "name": "Buy 3 Save $15.8",
          "quantity": 1,
          "unit_price": -15.8,
          "subtotal": -15.8
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "GfqzcOI2mL0MxocIuxGX"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-558e310b-0039-4b97-983e-ea8b73db2c38.jpg"
    },
    "expense": {
      "shop_name": "WM Cafe & Bar (Diamond Hill)",
      "shop_address": "鑽石山龍蟠街3號荷里活廣場2樓283-284號舖",
      "date": "2025-07-30",
      "expense_category": "Food",
      "currency": "HKD",
      "total_amount": 102,
      "items": [
        {
          "name": "M. 香煎三文魚扒配",
          "quantity": 1,
          "unit_price": 98,
          "subtotal": 98
        },
        {
          "name": "凍即磨咖啡",
          "quantity": 1,
          "unit_price": 4,
          "subtotal": 4
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "B16rjvWp9xoGMgd8h2ZA"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-a0a77d14-fe1c-4323-b295-aa9023c76cf6.jpg"
    },
    "expense": {
      "shop_name": "時代冰室",
      "shop_address": "",
      "date": "2025-07-29",
      "expense_category": "Food",
      "currency": "HKD",
      "total_amount": 62,
      "items": [
        {
          "name": "D213-煙嫩鴨胸焓",
          "quantity": 1,
          "unit_price": 51,
          "subtotal": 51
        },
        {
          "name": "炸薯餅",
          "quantity": 1,
          "unit_price": 8,
          "subtotal": 8
        },
        {
          "name": "A022-凍即磨咖啡",
          "quantity": 1,
          "unit_price": 3,
          "subtotal": 3
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "qRYPHwfBiasGcKiU22Ey"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-47d37366-317a-4b5d-a45d-24f98d6c5e13.jpg"
    },
    "expense": {
      "shop_name": "WM Cafe & Bar (Diamond Hill)",
      "shop_address": "鑽石山龍蟠街3號荷里活廣場2樓283-284號舖",
      "date": "2025-07-28",
      "expense_category": "Food",
      "currency": "HKD",
      "total_amount": 102,
      "items": [
        {
          "name": "M. 香煎三文魚扒配 檸檬牛油醬伴時令 蔬菜 (餐)是日餐湯 (餐)沙律",
          "quantity": 1,
          "unit_price": 98,
          "subtotal": 98
        },
        {
          "name": "凍即磨咖啡 少冰 走甜",
          "quantity": 1,
          "unit_price": 4,
          "subtotal": 4
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "lStWNuMgbUT0I9HqCs8r"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-f03fbbef-9a46-4c62-9fba-7637380fdfe6.jpg"
    },
    "expense": {
      "shop_name": "iEAT",
      "shop_address": "鑽石山荷里活廣場2樓270號鋪 Shop: 036 荷里活L2-270(新)",
      "date": "2025-07-28",
      "expense_category": "Groceries",
      "currency": "HKD",
      "total_amount": 42,
      "items": [
        {
          "name": "紐西蘭艾菲蘋果 #35",
          "quantity": 3,
          "unit_price": 8.66,
          "subtotal": 26
        },
        {
          "name": "有機菜椒 250g",
          "quantity": 1,
          "unit_price": 10,
          "subtotal": 8
        },
        {
          "name": "有機番薯葉250g",
          "quantity": 1,
          "unit_price": 10,
          "subtotal": 8
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "bGaAqCoHiljqZqJYWfro"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-e67c25cf-e3e3-4e43-9226-e7dd8a8056d0.png"
    },
    "expense": {
      "shop_name": "OpenAI",
      "shop_address": "548 Market Street PMB 97273 San Francisco, California 94104-5401 United States",
      "date": "2025-07-26",
      "expense_category": "SOFTWARE",
      "currency": "USD",
      "total_amount": 21,
      "items": [
        {
          "name": "ChatGPT Plus Subscription",
          "quantity": 1,
          "unit_price": 20,
          "subtotal": 20
        }
      ],
      "expense_type": "Subscription",
      "remark": ""
    },
    "id": "nLjiCSXuT10wU5Cx2iE0"
  },
  {
    "image": {
      "image_type": "Invoice",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-b3461193-e9bd-4af2-8666-65ab5402f7f8.png"
    },
    "expense": {
      "shop_name": "CLP",
      "shop_address": "",
      "date": "2025-07-26",
      "expense_category": "Utilities",
      "currency": "HKD",
      "total_amount": 1170,
      "items": [
        {
          "name": "Energy Charge",
          "quantity": 896,
          "unit_price": 0.9871763392857144,
          "subtotal": 884.51
        },
        {
          "name": "Fuel Cost Adjustment",
          "quantity": 896,
          "unit_price": 0.4350334821428571,
          "subtotal": 389.79
        }
      ],
      "expense_type": "Subscription",
      "remark": ""
    },
    "id": "Qs2yizlizZcjwq6lPPF5"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-55f72216-36bf-40ec-9a5f-457f2718fb00.jpg"
    },
    "expense": {
      "shop_name": "WM Cafe & Bar (Diamond Hill)",
      "shop_address": "鑽石山龍蟠街3號荷里活廣場2樓283-284號舖",
      "date": "2025-07-24",
      "expense_category": "Food",
      "currency": "HKD",
      "total_amount": 82,
      "items": [
        {
          "name": "B. 香煎西冷牛扒伴",
          "quantity": 1,
          "unit_price": 78,
          "subtotal": 78
        },
        {
          "name": "凍即磨咖啡",
          "quantity": 1,
          "unit_price": 4,
          "subtotal": 4
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "QgWBGeizxrh67bmT74I1"
  },
  {
    "image": {
      "image_type": "Receipt",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-95597b63-bc3c-489f-9b50-e5ec39c6c727.jpg"
    },
    "expense": {
      "shop_name": "Taste",
      "shop_address": "Plaza Hollywood, Shop No. 401, Level 4 and Entrance Lobby on Level 3, Plaza Hollywood",
      "date": "2025-07-24",
      "expense_category": "Groceries",
      "currency": "HKD",
      "total_amount": 108.8,
      "items": [
        {
          "name": "珠江橋牌豆豉鯪魚",
          "quantity": 2,
          "unit_price": 28,
          "subtotal": 56
        },
        {
          "name": "特大裝鮮橙",
          "quantity": 3,
          "unit_price": 9,
          "subtotal": 23.9
        },
        {
          "name": "特大艾菲蘋果",
          "quantity": 3,
          "unit_price": 14.9,
          "subtotal": 28.9
        }
      ],
      "expense_type": "Standard",
      "remark": ""
    },
    "id": "Iqyzj9E3tZ7i7YxxhNqm"
  },
  {
    "image": {
      "image_type": "Invoice",
      "image_file_name": "TodlOrf0IjOd0yV95oEFobDAToD2-c7aac873-4de9-4fb6-9e1a-98681213067b.png"
    },
    "expense": {
      "shop_name": "中華電信股份有限公司",
      "shop_address": "台北市金山南路二段52號",
      "date": "2025-07-22",
      "expense_category": "Telecommunication",
      "currency": "TWD",
      "total_amount": 599,
      "items": [
        {
          "name": "5G 599型月租費",
          "quantity": 1,
          "unit_price": 599,
          "subtotal": 599
        }
      ],
      "expense_type": "Subscription",
      "remark": ""
    },
    "id": "KnNQS1jBRtUkVAGtcR6L"
  }
]
"""

adapter = TypeAdapter(list[ExpenseRecord])
samples_expenses = adapter.validate_python(json.loads(expenses))

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

@mcp.tool
def get_latest_expenses(limit: int) -> list[ExpenseRecord]:
    """
    Get the latest expense records.

    Args:
        limit (int): The maximum number of records to return.
    
    Returns:
        list[ExpenseRecord]: The latest expense records.
    """
    api_endpoint = f"{_EXPENSELM_API_ENDPOINT}/expenses/"

    with httpx.Client() as client: 
        headers = {
            "EXPENSELM_API_KEY": _get_api_key(),
        }
        r = client.get(api_endpoint, headers=headers, params={"limit": limit})

        adapter = TypeAdapter(list[ExpenseRecord])
        expenses = adapter.validate_python(r.json())

    return expenses

# @mcp.tool
# def get_api_key() -> str:
#     key = os.getenv("EXPENSELM_API_KEY", "123")
#     return key

if __name__ == "__main__":
    mcp.run()
