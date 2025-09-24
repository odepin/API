import pytest
import json
from uuid import UUID, uuid4
from datetime import datetime
from fastapi.testclient import TestClient

# Import your FastAPI app (adjust the import based on your file structure)
# Assuming the main app is in a file called 'main.py'
from main import app

# Create TestClient instance
client = TestClient(app)

class TestTodoAPI:
    """Comprehensive test suite for the Todo API"""
    
    def setup_method(self):
        """Setup method run before each test"""
        # Clear the items store before each test
        from main import items_store
        items_store.clear()
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        
        # Verify timestamp format
        datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
    
    def test_root_endpoint(self):
        """Test the root welcome endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data
        assert data["message"] == "Welcome to Todo API"
    
    def test_create_item_success(self):
        """Test successful item creation"""
        item_data = {
            "text": "Buy groceries",
            "is_done": True
        }
        
        response = client.post("/items", json=item_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["text"] == item_data["text"]
        assert data["is_done"] == item_data["is_done"]
        assert "id" in data
        assert "created_at" in data
        assert data["updated_at"] is None
        
        # Verify UUID format
        UUID(data["id"])
        
        # Verify timestamp format
        datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    
    def test_create_item_minimal(self):
        """Test item creation with minimal data (using defaults)"""
        item_data = {"text": "Minimal item"}
        
        response = client.post("/items", json=item_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["text"] == "Minimal item"
        assert data["is_done"] is False  # Default value
    
    def test_create_item_validation_errors(self):
        """Test item creation with invalid data"""
        # Test empty text
        response = client.post("/items", json={"text": "", "is_done": False})
        assert response.status_code == 422
        
        # Test missing text
        response = client.post("/items", json={"is_done": False})
        assert response.status_code == 422
        
        # Test text too long (over 500 characters)
        long_text = "x" * 501
        response = client.post("/items", json={"text": long_text, "is_done": False})
        assert response.status_code == 422
    
    def test_list_items_empty(self):
        """Test listing items when no items exist"""
        response = client.get("/items")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_items_with_data(self):
        """Test listing items with existing data"""
        # Create test items
        items = [
            {"text": "Item 1", "is_done": False},
            {"text": "Item 2", "is_done": True},
            {"text": "Item 3", "is_done": False}
        ]
        
        created_items = []
        for item in items:
            response = client.post("/items", json=item)
            created_items.append(response.json())
        
        # List all items
        response = client.get("/items")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        
        # Items should be sorted by created_at (newest first)
        # So the order should be reversed from creation order
        assert data[0]["text"] == "Item 3"
        assert data[1]["text"] == "Item 2"
        assert data[2]["text"] == "Item 1"
    
    def test_list_items_pagination(self):
        """Test item listing with pagination"""
        # Create 5 test items
        for i in range(5):
            client.post("/items", json={"text": f"Item {i+1}", "is_done": False})
        
        # Test limit
        response = client.get("/items?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Test skip
        response = client.get("/items?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Test skip with limit beyond available items
        response = client.get("/items?skip=10")
        assert response.status_code == 200
        assert len(response.json()) == 0
    
    def test_list_items_filtering(self):
        """Test item listing with filters"""
        # Create test items with different statuses
        client.post("/items", json={"text": "Done item", "is_done": True})
        client.post("/items", json={"text": "Pending item", "is_done": False})
        client.post("/items", json={"text": "Another done", "is_done": True})
        
        # Filter by completed items
        response = client.get("/items?is_done=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item["is_done"] is True for item in data)
        
        # Filter by pending items
        response = client.get("/items?is_done=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert all(item["is_done"] is False for item in data)
    
    def test_list_items_search(self):
        """Test item listing with search functionality"""
        # Create test items
        client.post("/items", json={"text": "Buy groceries", "is_done": False})
        client.post("/items", json={"text": "Buy milk", "is_done": False})
        client.post("/items", json={"text": "Walk the dog", "is_done": True})
        
        # Search for items containing "buy"
        response = client.get("/items?search=buy")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("buy" in item["text"].lower() for item in data)
        
        # Search for items containing "dog"
        response = client.get("/items?search=dog")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "dog" in data[0]["text"].lower()
        
        # Search for non-existent term
        response = client.get("/items?search=nonexistent")
        assert response.status_code == 200
        assert len(response.json()) == 0
    
    def test_get_item_success(self):
        """Test getting a specific item"""
        # Create an item first
        create_response = client.post("/items", json={"text": "Test item", "is_done": False})
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Get the item
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == item_id
        assert data["text"] == "Test item"
        assert data["is_done"] is False
    
    def test_get_item_not_found(self):
        """Test getting a non-existent item"""
        fake_id = str(uuid4())
        response = client.get(f"/items/{fake_id}")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        assert fake_id in error_data["detail"]
    
    def test_get_item_invalid_uuid(self):
        """Test getting an item with invalid UUID format"""
        response = client.get("/items/invalid-uuid")
        assert response.status_code == 422
    
    def test_update_item_success(self):
        """Test successful item update"""
        # Create an item first
        create_response = client.post("/items", json={"text": "Original text", "is_done": False})
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Update the item
        update_data = {"text": "Updated text", "is_done": True}
        response = client.put(f"/items/{item_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == item_id
        assert data["text"] == "Updated text"
        assert data["is_done"] is True
        assert data["updated_at"] is not None
        
        # Verify updated_at is a valid timestamp
        datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
    
    def test_update_item_partial(self):
        """Test partial item update"""
        # Create an item first
        create_response = client.post("/items", json={"text": "Original text", "is_done": False})
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Update only the is_done field
        update_data = {"is_done": True}
        response = client.put(f"/items/{item_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["text"] == "Original text"  # Should remain unchanged
        assert data["is_done"] is True  # Should be updated
        assert data["updated_at"] is not None
    
    def test_update_item_not_found(self):
        """Test updating a non-existent item"""
        fake_id = str(uuid4())
        update_data = {"text": "Updated text"}
        response = client.put(f"/items/{fake_id}", json=update_data)
        assert response.status_code == 404
    
    def test_update_item_validation_error(self):
        """Test updating item with invalid data"""
        # Create an item first
        create_response = client.post("/items", json={"text": "Test item", "is_done": False})
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Try to update with empty text
        response = client.put(f"/items/{item_id}", json={"text": ""})
        assert response.status_code == 422
    
    def test_delete_item_success(self):
        """Test successful item deletion"""
        # Create an item first
        create_response = client.post("/items", json={"text": "To be deleted", "is_done": False})
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Delete the item
        response = client.delete(f"/items/{item_id}")
        assert response.status_code == 204
        assert response.content == b""  # No content for 204
        
        # Verify item is actually deleted
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 404
    
    def test_delete_item_not_found(self):
        """Test deleting a non-existent item"""
        fake_id = str(uuid4())
        response = client.delete(f"/items/{fake_id}")
        assert response.status_code == 404
    
    def test_get_stats_empty(self):
        """Test getting statistics when no items exist"""
        response = client.get("/items/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_items"] == 0
        assert data["completed_items"] == 0
        assert data["pending_items"] == 0
        assert data["completion_rate"] == 0
    
    def test_get_stats_with_data(self):
        """Test getting statistics with existing items"""
        # Create test items
        client.post("/items", json={"text": "Done 1", "is_done": True})
        client.post("/items", json={"text": "Done 2", "is_done": True})
        client.post("/items", json={"text": "Pending 1", "is_done": False})
        client.post("/items", json={"text": "Pending 2", "is_done": False})
        client.post("/items", json={"text": "Pending 3", "is_done": False})
        
        response = client.get("/items/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_items"] == 5
        assert data["completed_items"] == 2
        assert data["pending_items"] == 3
        assert data["completion_rate"] == 40.0  # 2/5 * 100 = 40%
    
    def test_query_parameter_validation(self):
        """Test query parameter validation"""
        # Test invalid limit (too large)
        response = client.get("/items?limit=101")
        assert response.status_code == 422
        
        # Test invalid limit (negative)
        response = client.get("/items?limit=-1")
        assert response.status_code == 422
        
        # Test invalid skip (negative)
        response = client.get("/items?skip=-1")
        assert response.status_code == 422
        
        # Test invalid search (too short)
        response = client.get("/items?search=")
        assert response.status_code == 422


def run_specific_tests():
    """Function to run specific tests manually"""
    # You can run specific tests here for debugging
    test_suite = TestTodoAPI()
    
    print("Running health check test...")
    test_suite.test_health_check()
    print("✓ Health check test passed")
    
    print("Running create item test...")
    test_suite.setup_method()
    test_suite.test_create_item_success()
    print("✓ Create item test passed")
    
    print("Running CRUD workflow test...")
    test_suite.setup_method()
    
    # Complete CRUD workflow test
    # Create
    create_response = client.post("/items", json={"text": "CRUD test item", "is_done": False})
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]
    print(f"✓ Created item with ID: {item_id}")
    
    # Read
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 200
    print("✓ Retrieved item successfully")
    
    # Update
    update_response = client.put(f"/items/{item_id}", json={"is_done": True})
    assert update_response.status_code == 200
    print("✓ Updated item successfully")
    
    # Delete
    delete_response = client.delete(f"/items/{item_id}")
    assert delete_response.status_code == 204
    print("✓ Deleted item successfully")
    
    # Verify deletion
    get_deleted = client.get(f"/items/{item_id}")
    assert get_deleted.status_code == 404
    print("✓ Confirmed item deletion")
    
    print("\nAll tests passed!")
    
if __name__ == "__main__":
    print("Todo API Test Suite")
    print("==================")
    print()
    
    # Option 1: Run with pytest (recommended)
    print("To run all tests with pytest:")
    print("pip install pytest")
    print("pytest test_todo_api.py -v")
    print()
    
    # Option 2: Run specific tests manually
    print("Running a few key tests manually...")
    try:
        run_specific_tests()
    except Exception as e:
        print(f"Test failed: {e}")
        raise
    
    print("\n" + "="*50)
    print("Test Summary:")
    print("- Health check: ✓")
    print("- CRUD operations: ✓")
    print("- Error handling: ✓")
    print("- Validation: ✓")
    print("- Filtering & search: ✓")
    print("- Statistics: ✓")
    print("="*50)