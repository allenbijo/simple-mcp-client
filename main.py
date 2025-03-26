import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# from anthropic import Anthropic
from openai import OpenAI

from dotenv import load_dotenv
import json

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # self.anthropic = Anthropic()
        self.openai = OpenAI()
        
        self.messages = []

    async def connect_to_server(self):
        """
        Connect to all MCP servers
        """
        with open('mcp_config.json') as f:
            mcp_servers = json.load(f)['mcpServers']

        server='sysinfo'
        
        server_params = StdioServerParameters(
            command=mcp_servers[server]['command'],
            args=mcp_servers[server]['args'],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        
        # available_tools = [{ 
        #     "name": tool.name,
        #     "description": tool.description,
        #     "input_schema": tool.inputSchema
        # } for tool in response.tools]
        
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def claude_process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                if hasattr(content, 'text') and content.text:
                    messages.append({
                      "role": "assistant",
                      "content": content.text
                    })
                messages.append({
                    "role": "user", 
                    "content": result.content
                })

                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                )

                final_text.append(response.content[0].text)

        return "\n".join(final_text)

    async def gpt_process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        
        def mcp_to_tool(tool):
            return {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                }
            }
            
        client = self.openai
            
        self.messages.append(
            {
                "role": "user",
                "content": query
            }
        )

        response = await self.session.list_tools()
        available_tools = [mcp_to_tool(tool) for tool in response.tools]

        # Process response and handle tool calls
        final_text = []
        
        while True:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=self.messages,
                tools=available_tools,
                tool_choice="auto"
            )

            response = completion.choices[0]
            
            if response.finish_reason == 'tool_calls':
                tool_call = completion.choices[0].message.tool_calls[0]
                function_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                result = await self.session.call_tool(function_name, args)
                final_text.append(f"[Calling tool {function_name} with args {args}]")
                
                self.messages.append(response.message)
                self.messages.append({                               # append result message
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            elif response.finish_reason == 'stop':
                self.messages.append(response.message)
                final_text.append(response.message.content)
                break

        return "\n".join(final_text)
    
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.gpt_process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())