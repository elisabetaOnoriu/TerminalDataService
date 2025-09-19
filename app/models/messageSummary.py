from dataclasses import dataclass
from datetime import datetime
from xml.etree import ElementTree as ET

NS = {"x": "urn:example:device-message"}

@dataclass
class MessageSummary:
    """Parsed data from an SQS message (id, device, client, sensor, value, unit, timestamp)."""
    message_id: str
    device_id: str
    client_id: str
    sensor: str
    value: str
    unit: str
    timestamp:str

    @classmethod
    def from_body(cls, body: dict) -> "MessageSummary":
        """Build a response from xml {'xml':..., 'parsed':...}"""
        xml = body.get("xml", "")
        parsed = body.get("parsed")
        if parsed is None:
            parsed = ET.fromstring(xml)

        ts_str = parsed.findtext("x:Header/x:Timestamp", namespaces=NS)

        ts_eu = None

        if ts_str:

            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            ts_eu = dt.strftime("%d.%m.%Y %H:%M:%S")

        return cls(
            message_id=parsed.findtext("x:Header/x:MessageID", namespaces=NS),
            device_id=parsed.findtext("x:Header/x:DeviceID", namespaces=NS),
            client_id=parsed.findtext("x:Header/x:ClientID", namespaces=NS),
            sensor=parsed.findtext("x:Body/x:Sensor", namespaces=NS),
            value=parsed.findtext("x:Body/x:Value", namespaces=NS),
            unit=parsed.findtext("x:Body/x:Unit", namespaces=NS),
            timestamp=ts_eu or "",
        )

    def as_dict(self):
        return {
            "message_id": self.message_id,
            "device_id": self.device_id,
            "client_id": self.client_id,
            "sensor": self.sensor,
            "value": self.value,
            "unit": self.unit,
            "timestamp":self.timestamp,
        }
