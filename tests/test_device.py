from app.models.device_model import Device
from app.enum.status import Status
"""Persist a new Device and verify it receives identifiers and expected values.

    Args:
        session: SQLAlchemy session fixture bound to the test database.
    """
def test_add_new_device(session):
    device = Device(
        client_id=1,
        status=Status.CONNECTED,
        name="John Doe",
        location="Test Lab",
        payload='{"test": true}'
    )

    session.add(device)
    session.commit()
    session.refresh(device)

    assert device.device_id is not None
    assert device.client_id == 1
    assert device.status == Status.CONNECTED
