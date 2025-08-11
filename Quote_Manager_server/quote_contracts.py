import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional, Dict



class FetchData(BaseModel):
    session_id: str
    bid_price: Optional[float] = Field(default=None)
    ask_price: Optional[float] = Field(default=None)
    timestamp: str
    broker: str
    symbol: str

class FetchDataResponse(BaseModel):
    data: List[FetchData]



class FetchQuoteRequest(BaseModel):
    broker: str
    symbol: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None 


class QuoteResponse(BaseModel):
    timestamp: int  # Use int if it's a Unix timestamp
    bid: float
    ask: float
    session_id: str

class BrokersSymbolsResponse(BaseModel):
    brokers: Dict[str, List[str]]

class FetchQuoteResponse(BaseModel):
    quotes: List[QuoteResponse]

class FetchBrokersResponse(BaseModel):
    brokers: List[str]

class ListSymbolsRequest(BaseModel):
    broker: str

class ListSymbolsResponse(BaseModel):
    symbols: List[str]

class ListDatesRequest(BaseModel):
    broker: str
    symbol: str

class ListDatesResponse(BaseModel):
    dates: List[str]

class ListSessionRequest(BaseModel):
    broker: str
    symbol: str
    date: str

class ListSessionResponse(BaseModel):
    sessions: List[str]

class IngestRequest(BaseModel):
    zip_path: str  # path to archive

class IngestResponse(BaseModel):
    status: str  # "success" or "failed"
    message: str