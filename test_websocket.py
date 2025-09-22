import asyncio
import websockets
import json

async def test_websocket():
    try:
        # Connect to the WebSocket
        ws = await websockets.connect('ws://localhost:8000/ws/chat')
        print("Connected to WebSocket")
        
        # Send a test query
        query = {
            'type': 'query', 
            'question': 'What is this document about?', 
            'chat_history': []
        }
        await ws.send(json.dumps(query))
        print("Sent query:", query['question'])
        
        # Receive responses
        responses = []
        try:
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                response_data = json.loads(response)
                responses.append(response_data)
                print(f"Received: {response_data}")
                
                # Stop if we get a complete or error response
                if response_data.get('type') in ['complete', 'error']:
                    break
        except asyncio.TimeoutError:
            print("Timeout waiting for response")
        
        await ws.close()
        print("WebSocket connection closed")
        return responses
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    responses = asyncio.run(test_websocket())
    print(f"\nTotal responses received: {len(responses)}")
