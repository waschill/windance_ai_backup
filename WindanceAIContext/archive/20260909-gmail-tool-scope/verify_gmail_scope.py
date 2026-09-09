import os,sys,yaml
os.environ['HERMES_HOME']='/Users/herald/.hermes/profiles/herald'
sys.path.insert(0,'/Users/herald/.hermes/hermes-agent')
from tools.mcp_tool_discovery import discover_mcp_tools
from tools.mcp_tool_lifecycle import shutdown_mcp_servers
from model_tools import get_tool_definitions
from pathlib import Path
try:
 names=discover_mcp_tools(allowed_mcp_names=['windance-gmail'])
 print('Discovered:',names)
 c=yaml.safe_load(Path(os.environ['HERMES_HOME'],'config.yaml').read_text())
 selected=c['platform_toolsets']['telegram']
 for label,sets in [('current',selected),('with_bridge',selected+['windance-gmail'])]:
  defs=get_tool_definitions(enabled_toolsets=sets,quiet_mode=True,skip_tool_search_assembly=True)
  gmail=[d['function']['name'] for d in defs if 'gmail' in d['function']['name']]
  print(label,'gmail tools:',gmail)
finally:shutdown_mcp_servers()
