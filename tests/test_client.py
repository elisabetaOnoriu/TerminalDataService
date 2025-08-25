from app.models.client_model import Client
from fastapi.testclient import TestClient
from main import app

"""Persist a new Client and ensure it receives a primary key.

    Args:
        session: SQLAlchemy session fixture bound to the test database.
    """
def test_add_new_client(session):
    client1=Client(
        name= "John doe"
    )
    session.add(client1)
    session.commit()
    session.refresh(client1)

    assert client1.client_id is not None
    print(client1.name)

client = TestClient(app)

"""Create a client and a device via API, then assign the device to the client.

 Flow:
     1) POST /client/clients -> create client, capture client_id
     2) POST /devices/devices/ -> create device, capture device_id
     3) PUT /client/client/devices -> assign device to client
     4) Verify response payload mirrors created resources

 Args:
     client: FastAPI TestClient fixture with DB dependency overridden.
 """

def test_assign_device_to_client(client):

    response_client = client.post("/client/clients", json={"name": "TestClient"})
    assert response_client.status_code == 200
    client_id = response_client.json()["client_id"]

    response_device = client.post("/devices/devices/", json={
        "client_id": 1,
        "name": "DeviceToAssign",
        "status": "disconnected",
        "location": "Lab",
        "payload": "test"
    })
    assert response_device.status_code == 200
    device_id = response_device.json()["device_id"]

    assign_response = client.put("/client/client/devices", params={
        "client_id": client_id,
        "device_id": device_id
    })
    assert assign_response.status_code == 201

    data = assign_response.json()
    assert data["client_id"] == client_id
    assert data["device_id"] == device_id
    assert data["name"] == "DeviceToAssign"
    assert data["status"] == "disconnected"
    assert data["location"] == "Lab"
    assert data["payload"] == "test"
