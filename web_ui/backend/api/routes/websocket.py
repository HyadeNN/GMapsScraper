"""
WebSocket API routes for real-time communication.
Handles live progress updates, log streaming, and scraper control.
"""

import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from api.models.scraper import CurrentProgress, LogMessage, LogLevel
from utils.integration import ScraperIntegration

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = client_info or {}
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "WebSocket connection established",
            "timestamp": datetime.now().isoformat(),
            "client_id": id(websocket)
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_info:
            del self.connection_info[websocket]
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                print(f"Error sending personal message: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        # Create list copy to avoid modification during iteration
        connections = self.active_connections.copy()
        
        for connection in connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(json.dumps(message, default=str))
                else:
                    self.disconnect(connection)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                self.disconnect(connection)
    
    async def broadcast_progress(self, progress: CurrentProgress):
        """Broadcast progress update to all clients."""
        message = {
            "type": "progress_update",
            "data": progress.dict(),
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_log(self, log_entry: LogMessage):
        """Broadcast log message to all clients."""
        message = {
            "type": "log_message",
            "data": log_entry.dict(),
            "timestamp": log_entry.timestamp.isoformat()
        }
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


get_scraper_integration = None


async def setup_scraper_callbacks(integration: ScraperIntegration):
    """Set up callbacks for scraper events."""
    # Only add callbacks if they haven't been added yet
    if manager.broadcast_progress not in integration.progress_callbacks:
        integration.add_progress_callback(manager.broadcast_progress)
    
    if manager.broadcast_log not in integration.log_callbacks:
        integration.add_log_callback(manager.broadcast_log)


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time communication.
    """
    await manager.connect(websocket)
    
    try:
        # Set up scraper integration callbacks
        integration = get_scraper_integration()
        if integration:
            await setup_scraper_callbacks(integration)
        
        # Send initial status
        if integration:
            status = integration.get_status()
            await manager.send_personal_message({
                "type": "initial_status",
                "data": status,
                "timestamp": datetime.now().isoformat()
            }, websocket)
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_client_message(message, websocket, integration)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error", 
                    "message": f"Message handling error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def handle_client_message(message: Dict, websocket: WebSocket, integration: ScraperIntegration):
    """Handle incoming messages from WebSocket clients."""
    message_type = message.get("type")
    data = message.get("data", {})
    
    response = {
        "type": f"{message_type}_response",
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "message": "Unknown message type"
    }
    
    try:
        if message_type == "ping":
            # Ping/pong for connection health
            response.update({
                "type": "pong",
                "success": True,
                "message": "pong",
                "server_time": datetime.now().isoformat()
            })
        
        elif message_type == "get_status":
            # Get current scraper status
            if integration:
                status = integration.get_status()
                response.update({
                    "success": True,
                    "message": "Status retrieved",
                    "data": status
                })
            else:
                response["message"] = "Scraper integration not available"
        
        elif message_type == "start_scraping":
            # Start scraping operation
            if not integration:
                response["message"] = "Scraper integration not available"
            else:
                operation_id = data.get("operation_id")
                settings = data.get("settings", {})
                locations = data.get("locations", {})
                
                if not operation_id:
                    response["message"] = "Missing operation_id"
                elif not settings:
                    response["message"] = "Missing settings"
                elif not locations:
                    response["message"] = "Missing locations"
                else:
                    success = await integration.start_scraping(operation_id, settings, locations)
                    response.update({
                        "success": success,
                        "message": "Scraping started" if success else "Failed to start scraping",
                        "operation_id": operation_id
                    })
        
        elif message_type == "pause_scraping":
            # Pause scraping
            if integration:
                success = await integration.pause_scraping()
                response.update({
                    "success": success,
                    "message": "Scraping paused" if success else "Could not pause scraping"
                })
            else:
                response["message"] = "Scraper integration not available"
        
        elif message_type == "resume_scraping":
            # Resume scraping
            if integration:
                success = await integration.resume_scraping()
                response.update({
                    "success": success,
                    "message": "Scraping resumed" if success else "Could not resume scraping"
                })
            else:
                response["message"] = "Scraper integration not available"
        
        elif message_type == "stop_scraping":
            # Stop scraping
            if integration:
                success = await integration.stop_scraping()
                response.update({
                    "success": success,
                    "message": "Scraping stopped" if success else "Could not stop scraping"
                })
            else:
                response["message"] = "Scraper integration not available"
        
        elif message_type == "subscribe_logs":
            # Subscribe to log messages (client indicates they want logs)
            response.update({
                "success": True,
                "message": "Subscribed to log messages"
            })
        
        elif message_type == "get_connection_info":
            # Get connection information
            response.update({
                "success": True,
                "message": "Connection info retrieved",
                "data": {
                    "client_id": id(websocket),
                    "connected_clients": manager.get_connection_count(),
                    "connection_time": datetime.now().isoformat()
                }
            })
        
        else:
            response["message"] = f"Unknown message type: {message_type}"
    
    except Exception as e:
        response.update({
            "success": False,
            "message": f"Error handling {message_type}: {str(e)}"
        })
    
    # Send response back to client
    await manager.send_personal_message(response, websocket)


@router.get("/info")
async def websocket_info():
    """
    Get information about WebSocket connections and status.
    """
    return {
        "websocket_endpoint": "/api/ws/connect",
        "active_connections": manager.get_connection_count(),
        "supported_message_types": [
            "ping",
            "get_status", 
            "start_scraping",
            "pause_scraping",
            "resume_scraping",
            "stop_scraping",
            "subscribe_logs",
            "get_connection_info"
        ],
        "broadcast_message_types": [
            "progress_update",
            "log_message",
            "scraping_started",
            "scraping_completed",
            "scraping_paused",
            "scraping_error"
        ]
    }


@router.post("/broadcast")
async def broadcast_message(message: Dict[str, Any]):
    """
    Broadcast a message to all connected WebSocket clients.
    This endpoint is for testing/admin purposes.
    """
    try:
        message["timestamp"] = datetime.now().isoformat()
        message["source"] = "api_broadcast"
        
        await manager.broadcast(message)
        
        return {
            "success": True,
            "message": "Message broadcasted",
            "recipients": manager.get_connection_count(),
            "broadcasted_message": message
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Broadcast failed: {str(e)}"
        }


@router.post("/test-log")
async def send_test_log():
    """
    Send a test log message through WebSocket.
    This endpoint is for testing purposes.
    """
    try:
        test_log = LogMessage(
            level=LogLevel.INFO,
            message="This is a test log message from the API",
            location="Test/API"
        )
        
        await manager.broadcast_log(test_log)
        
        return {
            "success": True,
            "message": "Test log sent",
            "recipients": manager.get_connection_count(),
            "log_entry": test_log.dict()
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Test log failed: {str(e)}"
        }


@router.get("/health")
async def websocket_health():
    """
    WebSocket service health check.
    """
    return {
        "healthy": True,
        "active_connections": manager.get_connection_count(),
        "service": "websocket",
        "timestamp": datetime.now().isoformat()
    }