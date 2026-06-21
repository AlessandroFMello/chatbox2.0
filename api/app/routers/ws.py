from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ai_service import AIServiceError, stream_response

router = APIRouter()


@router.websocket("/ws/conversations/{conversation_id}")
async def ws_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.receive_json()

            full_content = ""
            async for chunk in stream_response("", []):
                full_content += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})

            await websocket.send_json({"type": "end"})

    except AIServiceError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
    except WebSocketDisconnect:
        pass
