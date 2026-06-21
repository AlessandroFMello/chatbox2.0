from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import conversation_service
from app.services.ai_service import AIServiceError, stream_response

router = APIRouter()


@router.websocket("/ws/conversations/{conversation_id}")
async def ws_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            if not text.strip():
                continue

            conversation = await conversation_service.get_conversation(conversation_id)
            if not conversation:
                await websocket.send_json({"type": "error", "message": "Conversation not found"})
                await websocket.close()
                return

            full_content = ""
            async for chunk in stream_response(conversation.user_name, conversation.messages):
                full_content += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})

            if full_content:
                await conversation_service.persist_ai_message(conversation_id, full_content)
            await websocket.send_json({"type": "end"})

    except AIServiceError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
    except WebSocketDisconnect:
        pass
