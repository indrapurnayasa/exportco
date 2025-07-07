import pytest
from fastapi.testclient import TestClient

def test_get_country_demand(client: TestClient):
    """Test getting country demand data for all countries"""
    response = client.get("/api/v1/export/country-demand")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    
    # If data exists, verify structure
    if data["data"]:
        country_data = data["data"][0]
        assert "countryId" in country_data
        assert "countryName" in country_data
        assert "growthPercentage" in country_data
        assert "currentTotalTransaction" in country_data
        assert "products" in country_data
        assert isinstance(country_data["products"], list)
        
        # Check products structure
        if country_data["products"]:
            product = country_data["products"][0]
            assert "id" in product
            assert "name" in product
            assert "growth" in product

def test_get_country_demand_no_data(client: TestClient):
    """Test getting country demand data when no data is available"""
    # This test would need to be run in an environment with no data
    # For now, we just test that the endpoint doesn't crash
    response = client.get("/api/v1/export/country-demand")
    # Should return either 200 with empty data or 404
    assert response.status_code in [200, 404] 