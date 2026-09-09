import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    tid=json.loads(Path(__file__).with_name('live-task.json').read_text())['id']
    params=StdioServerParameters(command='/Users/herald/services/google-workspace-mcp/.venv/bin/python',args=['/Users/herald/services/herald-staff-mcp/herald_staff_mcp.py'])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            names=[t.name for t in (await session.list_tools()).tools]
            assert 'get_staff_task' in names and 'add_staff_task_note' in names
            response=await session.call_tool('get_staff_task',{'task_id':tid})
            assert not response.isError
            text='\n'.join(getattr(c,'text','') for c in response.content)
            assert tid in text and 'Business watch is excluded' in text
            print(json.dumps({'mcp_protocol':'PASS','tool_count':len(names),'same_task_and_note':True}))
asyncio.run(main())
