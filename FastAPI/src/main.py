from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4, UUID

from fastapi import FastAPI, HTTPException, Query, Path, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models with validation and documentation
class ItemBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="The todo item text")
    is_done: bool = Field(default=False, description="Whether the item is completed")

class ItemCreate(ItemBase):
    """Model for creating new items"""
    pass

class ItemUpdate(BaseModel):
    """Model for updating existing items"""
    text: Optional[str] = Field(None, min_length=1, max_length=500, description="The todo item text")
    is_done: Optional[bool] = Field(None, description="Whether the item is completed")

class ItemResponse(ItemBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "Buy groceries",
                "is_done": False,
                "created_at": "2023-12-01T10:00:00",
                "updated_at": None
            }
        }
    }

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str

class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str
    status_code: int
    timestamp: datetime

# In-memory storage (use database in production)
items_store: dict[UUID, ItemResponse] = {}

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler"""
    # Startup
    logger.info("Todo API is starting up...")
    logger.info("Initializing application resources...")
    
    # You can add startup logic here:
    # - Database connections
    # - Cache initialization  
    # - External service connections
    # - Background tasks setup
    
    yield
    
    # Shutdown
    logger.info("Todo API is shutting down...")
    logger.info("Cleaning up application resources...")
    
    # You can add cleanup logic here:
    # - Close database connections
    # - Clear caches
    # - Save state to persistent storage
    # - Cancel background tasks

# Initialize FastAPI app with metadata and lifespan
app = FastAPI(
    title="Todo API",
    description="A simple and efficient Todo API built with FastAPI",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@todoapi.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (use database in production)
items_store: dict[UUID, ItemResponse] = {}

# Dependency to get item by ID
async def get_item_by_id(
    item_id: UUID = Path(..., description="The unique identifier of the item")
) -> ItemResponse:
    """Dependency to retrieve an item by ID"""
    if item_id not in items_store:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    return items_store[item_id]

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_response = ErrorResponse(
        detail=exc.detail,
        status_code=exc.status_code,
        timestamp=datetime.now(timezone.utc)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_response)
    )

# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the current health status of the API"
)
async def health_check():
    """Health check endpoint for monitoring"""
    logger.info("Health check requested")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0"
    )

# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="Welcome endpoint",
    description="Returns a welcome message"
)
async def root():
    """Root endpoint with welcome message"""
    return {"message": "Welcome to Todo API", "docs": "/docs", "health": "/health"}

# Create item endpoint
@app.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Items"],
    summary="Create a new todo item",
    description="Create a new todo item with the provided text and completion status"
)
async def create_item(item: ItemCreate):
    """Create a new todo item"""
    item_id = uuid4()
    now = datetime.now(timezone.utc)
    
    new_item = ItemResponse(
        id=item_id,
        text=item.text,
        is_done=item.is_done,
        created_at=now,
        updated_at=None
    )
    
    items_store[item_id] = new_item
    logger.info(f"Created new item: {item_id}")
    
    return new_item

# List items endpoint with pagination and filtering
@app.get(
    "/items",
    response_model=List[ItemResponse],
    tags=["Items"],
    summary="List todo items",
    description="Retrieve a list of todo items with optional pagination and filtering"
)
async def list_items(
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    is_done: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, min_length=1, description="Search in item text")
):
    """List todo items with pagination and optional filtering"""
    logger.info(f"Listing items: limit={limit}, skip={skip}, is_done={is_done}, search={search}")
    
    # Get all items and convert to list
    all_items = list(items_store.values())
    
    # Apply filters
    filtered_items = all_items
    
    if is_done is not None:
        filtered_items = [item for item in filtered_items if item.is_done == is_done]
    
    if search:
        search_lower = search.lower()
        filtered_items = [
            item for item in filtered_items 
            if search_lower in item.text.lower()
        ]
    
    # Sort by created_at (newest first)
    filtered_items.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    paginated_items = filtered_items[skip:skip + limit]
    
    return paginated_items

# Get items statistics
@app.get(
    "/items/stats",
    tags=["Items"],
    summary="Get todo items statistics",
    description="Get statistics about todo items (total, completed, pending)"
)
async def get_items_stats():
    """Get statistics about todo items"""
    total_items = len(items_store)
    completed_items = sum(1 for item in items_store.values() if item.is_done)
    pending_items = total_items - completed_items
    
    logger.info("Retrieved items statistics")
    
    return {
        "total_items": total_items,
        "completed_items": completed_items,
        "pending_items": pending_items,
        "completion_rate": round(completed_items / total_items * 100, 2) if total_items > 0 else 0
    }

# Get single item endpoint
@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    tags=["Items"],
    summary="Get a specific todo item",
    description="Retrieve a specific todo item by its unique identifier"
)
async def get_item(item: ItemResponse = Depends(get_item_by_id)):
    """Get a specific todo item by ID"""
    logger.info(f"Retrieved item: {item.id}")
    return item

# Update item endpoint
@app.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    tags=["Items"],
    summary="Update a todo item",
    description="Update an existing todo item's text or completion status"
)
async def update_item(
    item_update: ItemUpdate,
    item: ItemResponse = Depends(get_item_by_id)
):
    """Update an existing todo item"""
    # Update only provided fields
    update_data = item_update.model_dump(exclude_unset=True)

    if update_data:
        for field, value in update_data.items():
            setattr(item, field, value)
        item.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated item: {item.id}")
    
    return item

# Delete item endpoint
@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Items"],
    summary="Delete a todo item",
    description="Delete a specific todo item by its unique identifier"
)
async def delete_item(item: ItemResponse = Depends(get_item_by_id)):
    """Delete a todo item"""
    del items_store[item.id]
    logger.info(f"Deleted item: {item.id}")
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )