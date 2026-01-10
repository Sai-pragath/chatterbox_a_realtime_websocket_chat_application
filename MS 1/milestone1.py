from fastapi import FastAPI, WebSocket
import uvicorn


app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Chatterbox Milestone 1 - WebSocket Server Running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    # Step 1: Accept the WebSocket connection
    await websocket.accept()
    print("Client connected")

    # Step 2: Keep listening for messages
    while True:
        try:
            message = await websocket.receive_text()

            # Ignore typing spam — do NOT send server messages for them
            if message in ["typing", "notyping"]:
                await websocket.send_text(message)
                continue

            print(f"Received: {message}")

            # Send only REAL messages
            await websocket.send_text(message)

        except Exception as e:
            print("Client disconnected", e)
            break


if __name__ == "__main__":
    uvicorn.run("milestone1:app", host="localhost", port=8000, reload=True)