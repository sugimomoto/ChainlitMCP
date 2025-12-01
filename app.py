import os
import json
from dotenv import load_dotenv
import chainlit as cl
from anthropic import Anthropic
from mcp import ClientSession

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Model configuration
MODEL_NAME = "claude-sonnet-4-20250514"


@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession):
    """Called when an MCP connection is established"""
    # List available tools from the MCP server
    result = await session.list_tools()
    
    # Process tool metadata
    tools = [{
        "name": t.name,
        "description": t.description,
        "input_schema": t.inputSchema,
    } for t in result.tools]
    
    # Store tools for later use
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)
    
    # Notify user about connected tools
    tool_names = [t["name"] for t in tools]
    await cl.Message(
        content=f"✅ MCP接続 '{connection.name}' が確立されました。\n利用可能なツール: {', '.join(tool_names)}"
    ).send()


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """Called when an MCP connection is terminated"""
    # Remove tools from session
    mcp_tools = cl.user_session.get("mcp_tools", {})
    if name in mcp_tools:
        del mcp_tools[name]
        cl.user_session.set("mcp_tools", mcp_tools)


@cl.step(type="tool")
async def call_tool(tool_use):
    """Execute a tool via MCP"""
    tool_name = tool_use.name
    tool_input = tool_use.input
    
    current_step = cl.context.current_step
    current_step.name = tool_name
    
    # Identify which MCP connection provides this tool
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_name = None
    
    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == tool_name for tool in tools):
            mcp_name = connection_name
            break
    
    if not mcp_name:
        error_msg = json.dumps({"error": f"Tool {tool_name} not found in any MCP connection"})
        current_step.output = error_msg
        return error_msg
    
    # Get the MCP session
    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)
    
    if not mcp_session:
        error_msg = json.dumps({"error": f"MCP {mcp_name} session not found"})
        current_step.output = error_msg
        return error_msg
    
    try:
        # Call the tool
        result = await mcp_session.call_tool(tool_name, tool_input)
        current_step.output = result
        return result
    except Exception as e:
        error_msg = json.dumps({"error": str(e)})
        current_step.output = error_msg
        return error_msg


def flatten_tools(mcp_tools):
    """Flatten tools from all MCP connections"""
    return [tool for tools in mcp_tools.values() for tool in tools]


async def call_claude(messages, tools):
    """Call Claude with streaming and tool support"""
    msg = cl.Message(content="")
    
    # Build request parameters
    request_params = {
        "model": MODEL_NAME,
        "max_tokens": 4096,
        "messages": messages,
    }
    
    # Only add tools if they exist
    if tools:
        request_params["tools"] = tools
    
    # Stream the response using synchronous with statement
    with client.messages.stream(**request_params) as stream:
        for text in stream.text_stream:
            await msg.stream_token(text)
    
    await msg.send()
    response = stream.get_final_message()
    
    return response


@cl.on_chat_start
async def start():
    """Initialize chat session"""
    cl.user_session.set("message_history", [])
    cl.user_session.set("mcp_tools", {})
    await cl.Message(
        content="こんにちは!Claude AIアシスタントです。\n\nMCPツールを使用するには、右上のメニューからMCP接続を追加してください。\n\n何かお手伝いできることはありますか?"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages with tool calling support"""
    # Get message history
    message_history = cl.user_session.get("message_history", [])
    
    # Add user message to history
    message_history.append({
        "role": "user",
        "content": message.content
    })
    
    # Get available MCP tools
    mcp_tools = cl.user_session.get("mcp_tools", {})
    tools = flatten_tools(mcp_tools)
    
    # Call Claude
    response = await call_claude(message_history, tools)
    
    # Handle tool use loop
    while response.stop_reason == "tool_use":
        # Find the tool use block
        tool_use = next(
            (block for block in response.content if block.type == "tool_use"),
            None
        )
        
        if not tool_use:
            break
        
        # Execute the tool
        tool_result = await call_tool(tool_use)
        
        # Add assistant response and tool result to history
        message_history.extend([
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result),
                    }
                ],
            },
        ])
        
        # Continue conversation with tool result
        response = await call_claude(message_history, tools)
    
    # Extract final text response
    final_response = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )
    
    # Update message history with final response
    if final_response:
        message_history.append({
            "role": "assistant",
            "content": final_response
        })
    
    # Save updated history
    cl.user_session.set("message_history", message_history)
