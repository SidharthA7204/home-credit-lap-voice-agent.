from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_rest_flow_disqualifies_agricultural():
    sid = client.post("/api/sessions", json={"customer_name": "Rahul Sharma"}).json()["session_id"]
    for u in ["Yes speaking", "Sure", "It's agricultural land", "Yes"]:
        r = client.post(f"/api/sessions/{sid}/turn", json={"utterance": u}).json()
    assert r["ended"] and r["outcome"] == "disqualified"


def test_retell_websocket_protocol():
    with client.websocket_connect("/llm-websocket/test-call") as ws:
        assert ws.receive_json()["response_type"] == "config"
        ws.send_json({"interaction_type": "call_details", "call": {"retell_llm_dynamic_variables": {
            "customer_name": "Rahul Sharma", "agent_gender": "female", "language_to_speak": "English"}}})
        first = ws.receive_json()
        assert first["response_id"] == 0 and "Rahul Sharma" in first["content"]
        ws.send_json({"interaction_type": "ping_pong", "timestamp": 1})
        assert ws.receive_json()["response_type"] == "ping_pong"
        ws.send_json({"interaction_type": "response_required", "response_id": 1,
                      "transcript": [{"role": "user", "content": "Yes speaking"}]})
        assert "convenient" in ws.receive_json()["content"]
