from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_opportunities_are_sorted():
    response = client.get("/api/opportunities", params={"horizon": "short"})
    assert response.status_code == 200
    scores = [item["score"] for item in response.json()]
    assert scores == sorted(scores, reverse=True)


def test_unknown_stock_returns_404():
    response = client.get("/api/stocks/999999/opportunity")
    assert response.status_code == 404

