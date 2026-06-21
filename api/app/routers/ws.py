from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws/conversations/{conversation_id}")
async def ws_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()
