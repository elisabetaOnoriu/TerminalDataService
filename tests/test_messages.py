import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

from main import app
from app.models.message_model import Message
from app.helpers.database import get_db

client = TestClient(app)


def test_get_messages_with_manual_insert(session):
    def override_get_db():
        yield session
    app.dependency_overrides[get_db] = override_get_db

    try:
        ts = datetime.now(timezone.utc).replace(microsecond=0)

        xml_payload = f"""
        <Message xmlns="urn:example:device-message" version="1.0">
          <Header>
            <MessageID>abc-123</MessageID>
            <DeviceID>10</DeviceID>
            <ClientID>20</ClientID>
            <Timestamp>{ts.isoformat().replace('+00:00', 'Z')}</Timestamp>
          </Header>
          <Body>
            <Sensor>temp</Sensor>
            <Value>23.4</Value>
            <Unit>C</Unit>
            <Meta>
              <Firmware>v1.0.3</Firmware>
              <Source>sensor-1</Source>
            </Meta>
          </Body>
        </Message>
        """.strip()

        msg = Message(device_id=10, client_id=20, timestamp=ts, payload=xml_payload)
        session.add(msg)
        session.commit()

        since = (ts - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
        print("Sent timestamp:", since)

        response = client.get(f"/messages?since={since}")
        print("Response status:", response.status_code)
        print("Response text:", response.text)

        assert response.status_code == 200

        root = ET.fromstring(response.content)
        assert root.tag == "Messages"
        assert len(root.findall(".//{urn:example:device-message}Message")) == 1

    finally:
        app.dependency_overrides.clear()
