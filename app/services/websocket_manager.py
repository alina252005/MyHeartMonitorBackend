from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, patient_id: str, websocket: WebSocket):
        await websocket.accept()
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = []
        self.active_connections[patient_id].append(websocket)

        print("CONNECTED:", patient_id)

    def disconnect(self, patient_id: str, websocket: WebSocket):
        if patient_id in self.active_connections:
            self.active_connections[patient_id].remove(websocket)

    async def send_to_patient(self, patient_id: str, message: dict):
        print("SENDING TO:", patient_id)

        if patient_id in self.active_connections:
            for connection in self.active_connections[patient_id]:
                await connection.send_json(message)

manager = ConnectionManager()