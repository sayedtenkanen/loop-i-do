# Loop Engineering Architecture - Plugins Manager

## Purpose
Integrate with external tools and services via Model Context Protocol (MCP).

## Key Interfaces

```python
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import yaml
import json
import importlib.util
from datetime import datetime

@dataclass
class PluginConfig:
    name: str
    description: str
    version: str
    author: str
    enabled: bool = True
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None

@dataclass
class MCPServer:
    name: str
    command: str
    args: List[str] = None
    env: Dict[str, str] = None
    timeout: int = 30

class PluginManager:
    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Dict] = {}
        self.mcp_servers: Dict[str, MCPServer] = {}
        self.plugin_instances: Dict[str, Any] = {}
        
    async def load_plugin(self, plugin_path: str):
        """Load a plugin from directory"""
        plugin_dir = Path(plugin_path)
        
        # Load plugin configuration
        config_file = plugin_dir / "plugin.yaml"
        if not config_file.exists():
            raise ValueError(f"Plugin config not found: {config_file}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        config = PluginConfig(
            name=config_data["name"],
            description=config_data.get("description", ""),
            version=config_data.get("version", "1.0"),
            author=config_data.get("author", ""),
            enabled=config_data.get("enabled", True),
            dependencies=config_data.get("dependencies", []),
            config_schema=config_data.get("config_schema")
        )
        
        # Load MCP server configuration
        mcp_config = config_data.get("mcp_server")
        if mcp_config:
            mcp_server = MCPServer(
                name=config_data["name"],
                command=mcp_config["command"],
                args=mcp_config.get("args", []),
                env=mcp_config.get("env", {}),
                timeout=mcp_config.get("timeout", 30)
            )
            self.mcp_servers[config.name] = mcp_server
        
        # Load Python module if exists
        module_file = plugin_dir / "plugin.py"
        if module_file.exists():
            spec = importlib.util.spec_from_file_location(
                config.name, module_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Initialize plugin class if exists
            if hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
                self.plugin_instances[config.name] = plugin_class()
        
        # Store plugin info
        self.plugins[config.name] = {
            "config": config,
            "path": plugin_dir,
            "loaded_at": datetime.now()
        }
        
        print(f"Loaded plugin: {config.name} v{config.version}")
    
    async def connect_to_service(self, service_config: Dict[str, Any]):
        """Establish connection to external service"""
        service_name = service_config.get("name")
        
        if service_name not in self.plugins:
            raise ValueError(f"Plugin {service_name} not loaded")
        
        # Initialize connection based on plugin type
        plugin_instance = self.plugin_instances.get(service_name)
        if plugin_instance and hasattr(plugin_instance, 'connect'):
            await plugin_instance.connect(service_config)
    
    async def execute_plugin_action(self, plugin_name: str, action: str, 
                                  params: Dict[str, Any]) -> Any:
        """Execute an action through a plugin"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        plugin_info = self.plugins[plugin_name]
        
        # Check if plugin is enabled
        if not plugin_info["config"].enabled:
            raise ValueError(f"Plugin {plugin_name} is disabled")
        
        # Execute action via MCP server
        if plugin_name in self.mcp_servers:
            return await self._execute_mcp_action(plugin_name, action, params)
        
        # Execute action via Python module
        plugin_instance = self.plugin_instances.get(plugin_name)
        if plugin_instance and hasattr(plugin_instance, action):
            method = getattr(plugin_instance, action)
            return await method(**params)
        
        raise ValueError(f"Action {action} not found in plugin {plugin_name}")
    
    async def _execute_mcp_action(self, plugin_name: str, action: str,
                                params: Dict[str, Any]) -> Any:
        """Execute action via MCP server"""
        mcp_server = self.mcp_servers.get(plugin_name)
        if not mcp_server:
            raise ValueError(f"MCP server not found for {plugin_name}")
        
        # This would integrate with actual MCP client
        # For now, return mock response
        return {
            "success": True,
            "action": action,
            "params": params,
            "timestamp": datetime.now().isoformat()
        }
    
    def has_plugin(self, plugin_name: str) -> bool:
        """Check if plugin is loaded and enabled"""
        return (plugin_name in self.plugins and 
                self.plugins[plugin_name]["config"].enabled)
    
    def list_plugins(self) -> List[Dict]:
        """List all loaded plugins"""
        return [
            {
                "name": name,
                "version": info["config"].version,
                "description": info["config"].description,
                "enabled": info["config"].enabled,
                "loaded_at": info["loaded_at"].isoformat()
            }
            for name, info in self.plugins.items()
        ]
    
    def get_plugin_config(self, plugin_name: str) -> Optional[Dict]:
        """Get plugin configuration"""
        plugin_info = self.plugins.get(plugin_name)
        if plugin_info:
            return {
                "name": plugin_info["config"].name,
                "description": plugin_info["config"].description,
                "version": plugin_info["config"].version,
                "author": plugin_info["config"].author,
                "config_schema": plugin_info["config"].config_schema
            }
        return None
    
    async def unload_plugin(self, plugin_name: str):
        """Unload a plugin"""
        if plugin_name in self.plugins:
            # Cleanup plugin instance
            plugin_instance = self.plugin_instances.get(plugin_name)
            if plugin_instance and hasattr(plugin_instance, 'cleanup'):
                await plugin_instance.cleanup()
            
            # Remove from registries
            del self.plugins[plugin_name]
            if plugin_name in self.mcp_servers:
                del self.mcp_servers[plugin_name]
            if plugin_name in self.plugin_instances:
                del self.plugin_instances[plugin_name]

# Example plugin implementations
class GitHubPlugin:
    """GitHub integration plugin"""
    
    def __init__(self):
        self.client = None
    
    async def connect(self, config: Dict[str, Any]):
        """Connect to GitHub API"""
        # Initialize GitHub client
        pass
    
    async def create_pr(self, worktree, title: str, body: str) -> Dict:
        """Create a pull request"""
        # Create PR logic
        return {
            "pr_number": 123,
            "url": "https://github.com/org/repo/pull/123",
            "status": "created"
        }
    
    async def update_ticket(self, ticket_id: str, status: str) -> Dict:
        """Update issue/ticket status"""
        # Update issue logic
        return {
            "ticket_id": ticket_id,
            "status": status,
            "updated": True
        }
    
    async def add_comment(self, issue_number: int, comment: str) -> Dict:
        """Add comment to issue"""
        # Add comment logic
        return {
            "issue_number": issue_number,
            "comment_added": True
        }

class LinearPlugin:
    """Linear integration plugin"""
    
    def __init__(self):
        self.client = None
    
    async def connect(self, config: Dict[str, Any]):
        """Connect to Linear API"""
        # Initialize Linear client
        pass
    
    async def update_ticket(self, ticket_id: str, status: str) -> Dict:
        """Update ticket status"""
        # Update ticket logic
        return {
            "ticket_id": ticket_id,
            "status": status,
            "updated": True
        }
    
    async def create_ticket(self, title: str, description: str) -> Dict:
        """Create a new ticket"""
        # Create ticket logic
        return {
            "ticket_id": "ENG-456",
            "title": title,
            "created": True
        }

class SlackPlugin:
    """Slack integration plugin"""
    
    def __init__(self):
        self.client = None
    
    async def connect(self, config: Dict[str, Any]):
        """Connect to Slack API"""
        # Initialize Slack client
        pass
    
    async def send_message(self, channel: str, message: str) -> Dict:
        """Send message to Slack channel"""
        # Send message logic
        return {
            "channel": channel,
            "message_sent": True,
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_notification(self, user: str, message: str) -> Dict:
        """Send direct notification"""
        # Send notification logic
        return {
            "user": user,
            "notification_sent": True
        }

# Plugin configuration example
PLUGIN_CONFIGS = {
    "github": {
        "name": "github",
        "description": "GitHub integration for PRs and issues",
        "version": "1.0.0",
        "author": "loop-engineering",
        "enabled": True,
        "mcp_server": {
            "command": "python",
            "args": ["-m", "mcp_server_github"],
            "env": {
                "GITHUB_TOKEN": "${GITHUB_TOKEN}"
            },
            "timeout": 30
        },
        "config_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string"},
                "branch": {"type": "string"}
            }
        }
    },
    "linear": {
        "name": "linear",
        "description": "Linear integration for project management",
        "version": "1.0.0",
        "author": "loop-engineering",
        "enabled": True,
        "mcp_server": {
            "command": "python",
            "args": ["-m", "mcp_server_linear"],
            "env": {
                "LINEAR_API_KEY": "${LINEAR_API_KEY}"
            }
        }
    },
    "slack": {
        "name": "slack",
        "description": "Slack integration for notifications",
        "version": "1.0.0",
        "author": "loop-engineering",
        "enabled": True,
        "mcp_server": {
            "command": "python",
            "args": ["-m", "mcp_server_slack"],
            "env": {
                "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}"
            }
        }
    }
}
```

## Plugin Structure

```
plugins/
├── github/
│   ├── plugin.yaml
│   ├── plugin.py
│   ├── mcp_server.py
│   └── README.md
├── linear/
│   ├── plugin.yaml
│   ├── plugin.py
│   ├── mcp_server.py
│   └── README.md
└── slack/
    ├── plugin.yaml
    ├── plugin.py
    ├── mcp_server.py
    └── README.md
```

## Plugin YAML Format

```yaml
# plugins/github/plugin.yaml
name: github
description: "GitHub integration for PRs and issues"
version: 1.0.0
author: "loop-engineering"
enabled: true
dependencies:
  - "pygithub>=1.55"
config_schema:
  type: object
  properties:
    repo:
      type: string
      description: "GitHub repository (owner/repo)"
    branch:
      type: string
      description: "Base branch for PRs"
mcp_server:
  command: "python"
  args: ["-m", "mcp_server_github"]
  env:
    GITHUB_TOKEN: "${GITHUB_TOKEN}"
  timeout: 30
```

## Implementation Notes

1. **MCP Protocol**: Uses Model Context Protocol for standardized tool integration
2. **Plugin Discovery**: Automatic loading from plugins directory
3. **Configuration**: YAML-based configuration with schema validation
4. **Hot Reloading**: Plugins can be loaded/unloaded without restarting
5. **Security**: Environment variables for sensitive configuration

## Example Usage

```python
# Initialize plugin manager
plugin_manager = PluginManager("./plugins")

# Load plugins
await plugin_manager.load_plugin("./plugins/github")
await plugin_manager.load_plugin("./plugins/linear")

# Check if plugin is available
if plugin_manager.has_plugin("github"):
    # Execute plugin action
    result = await plugin_manager.execute_plugin_action(
        "github",
        "create_pr",
        {
            "worktree": worktree,
            "title": "Fix: resolve authentication issue",
            "body": "Automated fix generated by loop engineering"
        }
    )
    print(f"PR created: {result['url']}")

# List all plugins
plugins = plugin_manager.list_plugins()
for plugin in plugins:
    print(f"{plugin['name']} v{plugin['version']}: {plugin['description']}")
```
