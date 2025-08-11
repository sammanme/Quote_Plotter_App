from fastapi import APIRouter, Depends, HTTPException, Query
from quote_db import QuoteDatabase
from quote_service import QuoteService
from quote_contracts import (    
    FetchQuoteRequest, FetchQuoteResponse,
    ListSymbolsRequest, ListSymbolsResponse,
    ListDatesRequest, ListDatesResponse,
    ListSessionRequest, ListSessionResponse,
    IngestRequest, IngestResponse,    
    FetchBrokersResponse,
    FetchData, FetchDataResponse,
    BrokersSymbolsResponse
)

router = APIRouter()

def get_db():
    db = QuoteDatabase("quotes.db")
    try:
        yield db
    finally:
        db.conn.close()

def get_service(db: QuoteDatabase = Depends(get_db)):
    return QuoteService(db=db)

@router.post("/ingest", response_model=IngestResponse)
def ingest_quotes(request: IngestRequest, service: QuoteService = Depends(get_service)):
    return service.ingest_archive(request)

@router.get("/api/data", response_model=FetchDataResponse)
async def get_data(
    broker_a: str = Query(...),
    symbol_a: str = Query(...),
    broker_b: str = Query(...),
    symbol_b: str = Query(...),
    time_range_hours: str = Query('all', description="Time range: 'all' or hours (1, 6, 24)"),
    limit: int = Query(1000, description="Maximum number of records"),
    service: QuoteService = Depends(get_service)
):
    data = service.get_data(broker_a, symbol_a, broker_b, symbol_b, limit, time_range_hours)
    return {"data": data}

@router.get("/brokers", response_model=FetchBrokersResponse)
def get_all_brokers(service: QuoteService = Depends(get_service)):
    return service.get_all_brokers()

@router.post("/symbols", response_model=ListSymbolsResponse)
def get_symbols(request: ListSymbolsRequest, service: QuoteService = Depends(get_service)):
    return service.get_symbols(request)

@router.post("/dates", response_model=ListDatesResponse)
def get_dates(request: ListDatesRequest, service: QuoteService = Depends(get_service)):
    return service.get_dates(request)

@router.post("/sessions", response_model=ListSessionResponse)
def get_sessions(request: ListSessionRequest, service: QuoteService = Depends(get_service)):
    return service.get_sessions(request)

@router.post("/quotes", response_model=FetchQuoteResponse)
def get_quotes(request: FetchQuoteRequest, service: QuoteService = Depends(get_service)):
    return service.get_quotes(request)

@router.get("/brokers&symbols", response_model=BrokersSymbolsResponse)
def get_brokers_and_symbols(service: QuoteService = Depends(get_service)):
    return service.get_brokers_and_symbols()
