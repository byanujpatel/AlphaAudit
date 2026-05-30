import asyncio
import json
import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from config import config
from mcp_client import mcp_client
from graph import app_graph, GraphState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alphaaudit.main")

app = FastAPI(
    title="AlphaAudit: Autonomous Pre-Earnings Alternative Data Engine",
    description="Stateful cyclic multi-agent graph intelligence engine utilizing Bright Data and Gemini."
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    On startup, connect to the Bright Data MCP server.
    """
    logger.info("Starting up AlphaAudit backend server...")
    # Initialize the MCP connection
    await mcp_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Disconnect from the MCP server on shutdown.
    """
    logger.info("Shutting down AlphaAudit backend server...")
    await mcp_client.disconnect()

@app.get("/api/health")
async def health_check():
    """
    Standard health check endpoint that reports configuration validation.
    """
    valid, missing = config.validate()
    return {
        "status": "healthy" if valid else "degraded",
        "mcp_connected": mcp_client.is_connected,
        "mcp_fallback_active": mcp_client.use_fallback,
        "mcp_is_sse": getattr(mcp_client, "is_sse", False),
        "config_valid": valid,
        "missing_keys": missing
    }

@app.get("/api/analyze")
async def analyze_company(target: str = Query(..., description="Stock ticker or company domain to analyze")):
    """
    Core execution endpoint. Streams live LangGraph node transitions, 
    infrastructure self-healing logs, and the final synthesized outcomes 
    to the frontend using Server-Sent Events (SSE).
    """
    async def sse_event_generator():
        # Initialize graph state
        initial_state = GraphState(
            target=target,
            status_stream=[],
            retry_count={},
            errors=[]
        )

        logger.info(f"Triggering pre-earnings analysis for: {target}")
        
        # Keep track of which log events we've already streamed to avoid duplicates
        sent_log_count = 0

        yield f"data: {json.dumps({'type': 'init', 'message': f'Initializing AlphaAudit analysis for {target}...'})}\n\n"
        await asyncio.sleep(0.5)

        try:
            # Execute the stateful graph using async streaming
            # LangGraph astream streams updates as each node completes execution
            async for event in app_graph.astream(initial_state.dict(), stream_mode="values"):
                # Extract logs from state
                status_stream = event.get("status_stream", [])
                
                # Yield any new logs that have been added
                while sent_log_count < len(status_stream):
                    new_event = status_stream[sent_log_count]
                    yield f"data: {json.dumps({'type': 'log', 'node': new_event['node'], 'message': new_event['message']})}\n\n"
                    sent_log_count += 1
                    await asyncio.sleep(0.1) # Smooth streaming effect
                
                # Check if final outcome was generated in this step
                if event.get("final_outcome"):
                    final_outcome = event["final_outcome"]
                    # Convert Pydantic model to dictionary for JSON serialization
                    final_dict = final_outcome.dict() if hasattr(final_outcome, "dict") else final_outcome
                    yield f"data: {json.dumps({'type': 'outcome', 'data': final_dict})}\n\n"
                    break

            yield f"data: {json.dumps({'type': 'complete', 'message': 'Analysis complete!'})}\n\n"

        except Exception as e:
            logger.error(f"Graph execution failed: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Critical engine error: {str(e)}'})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
