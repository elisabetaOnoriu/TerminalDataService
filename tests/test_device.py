from app.models.device_model import Device
from app.models.Status import Status

def test_add_new_device(session):
    device = Device(
        client_id=1,
        status=Status.CONNECTED,
        location="Test Lab",
        payload='{"test": true}'
    )

    session.add(device)
    session.commit()
    session.refresh(device)

    assert device.device_id is not None
    assert device.client_id == 1
    assert device.status == Status.CONNECTED
