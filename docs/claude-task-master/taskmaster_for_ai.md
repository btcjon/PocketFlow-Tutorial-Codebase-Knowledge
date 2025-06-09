# Claude Task Master - AI-Driven Task Management System

## System Overview
**Purpose**: Task management system designed for AI-driven development with CLI interface, AI IDE integration via MCP, and unified AI model access.

**Core Architecture**: 6 interconnected modules with CLI → Data → MCP → Config → AI Services → Utilities flow.

## 1. CLI Commands (Commander.js)

### Technical Implementation
- **Entry Point**: `index.js` using Commander.js library
- **Command Structure**: `task-master <command> [options]`
- **Core Commands**: `init`, `list`, `next`, `add`, `update-task`

### Command Patterns
```javascript
program
  .command('init')
  .option('-n, --name <n>', 'Project name')
  .option('-y, --yes', 'Skip prompts')
  .action(async (cmdOptions) => {
    const init = await import('./scripts/init.js');
    await init.initializeProject(cmdOptions);
  });
```

### Use Cases & Decision Points
- **When**: Starting projects, managing tasks via terminal, automation scripts
- **Why**: Faster than GUI, scriptable, consistent interface
- **Integration**: Serves as primary human interface, calls core logic modules

## 2. Tasks Data Management

### Data Schema (JSON Blueprint)
```json
{
  "id": 1,
  "title": "Task name",
  "description": "Detailed description", 
  "status": "pending|in-progress|done|blocked",
  "dependencies": [2, 3],
  "priority": "high|medium|low",
  "details": "Implementation details",
  "testStrategy": "Testing approach",
  "subtasks": []
}
```

### Technical Operations
- **Storage**: `tasks.json` file with JSON structure
- **Validation**: Zod schema enforcement (`AiTaskDataSchema`)
- **CRUD Operations**: Add via `add-task.js`, update via `update-task-by-id.js`, list via `list-tasks.js`

### AI Integration Points
- **Task Generation**: AI creates `title`, `description`, `details`, `testStrategy` from prompts
- **Task Updates**: AI suggests modifications based on context
- **Dependency Management**: AI can set task relationships

### Decision Guidance
- **When**: Need structured task tracking with AI assistance
- **Why**: Consistent data model enables reliable operations, AI can understand/modify tasks
- **Integration**: Consumed by CLI commands, exposed via MCP tools

## 3. MCP (Model Control Protocol) Integration

### Technical Architecture
- **Server**: FastMCP (`mcp-server/src/index.js`)
- **Transport**: STDIO communication
- **Tool Registration**: Core functions exposed as callable AI tools

### Dual-Mode Function Pattern
```javascript
export async function initializeProject(options = {}) {
  if (options.source !== 'mcp') {
    displayBanner(); // CLI-only UI
  }
  
  const projectId = await setupProjectFiles(options.name); // Shared logic
  
  if (options.source === 'mcp') {
    return { success: true, projectId, message: "..." }; // Structured response
  } else {
    console.log(`Project initialized!`); // CLI output
  }
}
```

### Tool Definition Pattern
```javascript
server.addTool({
  name: 'initializeProject',
  description: 'Initializes new Task Master project',
  parameters: z.object({
    projectName: z.string(),
    projectRoot: z.string()
  }),
  execute: async (args) => executeTaskMasterCommand('init', args)
});
```

### Use Cases & Integration
- **When**: AI IDE integration, automated workflows, agent-driven task management
- **Why**: Enables AI to directly manipulate task system without human intervention
- **Workflow**: AI Agent → MCP Server → Core Logic → Structured Response → AI Agent

## 4. Utility Functions

### Core Utilities (`scripts/modules/utils.js`)

#### File Operations
- **`readJSON(filepath)`**: Safe JSON file reading with error handling
- **`writeJSON(filepath, data)`**: JSON writing with directory creation
- **Pattern**: `try/catch` with detailed error logging

#### Project Management
- **`findProjectRoot()`**: Locates project root by searching for `package.json`, `.git`, `tasks.json`
- **`resolveEnvVariable(key)`**: Multi-source env var resolution (MCP session → .env → system env)

#### Logging
- **`log(level, message)`**: Configurable logging with color support
- **Levels**: `debug`, `info`, `warn`, `error`

### Decision Points
- **When**: Need consistent file ops, project detection, environment config
- **Why**: DRY principle, centralized error handling, reliable cross-platform behavior
- **Integration**: Used by all modules for common operations

## System Integration Patterns

### CLI to Data Flow
```
User Command → Commander.js → Core Logic → readJSON/writeJSON → tasks.json
```

### MCP to Data Flow  
```
AI Agent → MCP Server → Tool Execute → Core Logic (source: 'mcp') → Structured Response
```

### Error Handling Strategy
- **Zod Validation**: Schema enforcement at data boundaries
- **Try/Catch**: File operations and external API calls
- **Logging**: Consistent error reporting via utility functions

## Implementation Guidance

### For AI Systems Consuming This
1. **Task Operations**: Use MCP tools for programmatic task management
2. **Data Access**: Tasks are JSON objects with strict schema
3. **Configuration**: Environment variables resolved via utility functions
4. **Error Handling**: Expect structured responses with success/error indicators

### When to Recommend This System
- **AI-driven development workflows**: Native MCP integration
- **Complex project task management**: Rich task schema with dependencies
- **Multi-modal access needs**: Both CLI and programmatic interfaces
- **Team environments**: Consistent task structure across tools

### Integration Considerations
- **Environment Setup**: Requires Node.js, proper env var configuration
- **File System**: Creates `tasks.json`, `.taskmasterconfig` in project root
- **AI Model Access**: Needs API keys for AI service unification
- **MCP Compatibility**: Works with Cursor, Claude, other MCP-enabled tools

## Key Technical Decisions
- **Commander.js**: Mature CLI framework with good option parsing
- **FastMCP**: Lightweight MCP server implementation
- **Zod**: Runtime schema validation for data integrity
- **JSON Storage**: Simple, human-readable, version-controllable
- **Dual-mode Functions**: Single codebase serves both CLI and MCP interfaces