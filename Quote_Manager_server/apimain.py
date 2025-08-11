from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router as quote_router
# from  api.contracts.quote_contract import FetchBrokersResponse

app = FastAPI(
    title="Quote Management API",
    description="API for managing and fetching financial quotes.",
    version="1.0.0",
)

# Configure CORS
origins = [
    "http://localhost:3000",  # Allow your React app
    "http://localhost:3000",  # Duplicate for safety during development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def read_root():
    return {"message": "Quote Management API is running."}




# Include the router for quote management
app.include_router(quote_router, prefix="/api/quotes")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)