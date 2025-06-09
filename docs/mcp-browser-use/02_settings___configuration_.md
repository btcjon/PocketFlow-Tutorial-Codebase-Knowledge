# Chapter 2: Settings & Configuration

In the [previous chapter](01_mcp_server__fastmcp__.md), we learned that the FastMCP server is like the central switchboard for our browser automation system. It listens for requests from an AI assistant and routes them to the right tools. But how does this switchboard know *how* to operate its tools? For example, should the browser open visibly or secretly (headless)? Where should it save files?

This is where **Settings & Configuration** comes in! Think of it like the dashboard of a car. Just as you use knobs and buttons on a car's dashboard to control things like the lights, climate, or choose between drive and reverse, our settings allow you to control how the entire `mcp-browser-use` application behaves. It’s the control panel for everything from which AI model to use to how the browser operates.

## Why Do We Need Settings?

Imagine you're building a house. You could nail every piece of wood directly, or you could use screws. Screws allow you to adjust things later, move walls if needed, or even dismantle parts and rebuild. Settings are like the "screws" of our application. They make the system flexible and adaptable without having to change the core "structure" (the code).

**Central Use Case:** You want to run a web research task, but you want to see the browser opening on your screen (not hidden). Also, you want to store all downloaded files in a specific folder. How do you tell the system that? By changing its settings!

## Key Concepts of Settings

Our settings are organized into different groups, just like a car's dashboard has climate controls, media controls, and driving controls. Each group handles a specific part of the system.

In `mcp-browser-use`, our settings are defined in a file called `src/mcp_server_browser_use/config.py`. Let's look at the main groups:

1.  **LLM Settings (`LLMSettings`)**:
    *   **What it controls**: Which Large Language Model (LLM) the system uses (e.g., Google's Gemini, OpenAI's GPT). Also, things like its "temperature" (how creative it should be) and API keys.
    *   **Analogy**: This is like choosing your car's engine type (gas, electric, hybrid) and how aggressively it should accelerate.

2.  **Browser Settings (`BrowserSettings`)**:
    *   **What it controls**: How the web browser behaves. For example, if it should be `headless` (run in the background, invisible) or `false` (open a visible window). Where to save user data, or even connect to an already open browser.
    *   **Analogy**: This controls your car's driving mode (sport, economy, comfortable), whether its lights are on, or if you use cruise control.

3.  **Agent Tool Settings (`AgentToolSettings`)**:
    *   **What it controls**: Specific behaviors of the AI agents that use the browser. For example, how many steps an agent can take, or if it should use "vision" (looking at screenshots of web pages).
    *   **Analogy**: These are advanced features on your car's dashboard, like lane-keeping assist or adaptive cruise control, which guide how the car performs certain driving tasks.

4.  **Research Tool Settings (`ResearchToolSettings`)**:
    *   **What it controls**: How the deep research agent operates. This includes where it saves its research reports and how many browsers it can use at once.
    *   **Analogy**: This is like setting your car's navigation: where to save recent destinations or how many alternative routes to consider for speed.

5.  **Path Settings (`PathSettings`)**:
    *   **What it controls**: Where various temporary or output files are stored, such as downloaded files.
    *   **Analogy**: This tells the car's navigation where your "Home" or "Work" addresses are saved.

## How to Configure Settings

The `mcp-browser-use` application uses a popular Python library called `Pydantic-Settings` to manage its configuration. This library is very smart because it can read settings from multiple places, in a specific order:

1.  **Hardcoded Defaults**: These are the default values already written in `src/mcp_server_browser_use/config.py`.
2.  **`.env` files**: You can create a file named `.env` in your project's root directory and put settings there. This is very common for local development.
3.  **Environment Variables**: You can set these directly in your operating system or command line before running the application.

**Let's solve our use case:** You want a visible browser and specific download folder.

We will use an `.env` file because it's easy to manage and good for keeping settings separate from your code.

1.  **Create a `.env` file**: In the root of your `mcp-browser-use` project folder (the same folder where `src` is), create a new file named `.env`.

2.  **Add your settings to `.env`**:
    ```dotenv
    # .env file
    MCP_BROWSER_HEADLESS=False
    MCP_PATHS_DOWNLOADS=/path/to/your/custom/downloads # On Windows, might be C:\Users\YourUser\Downloads
    ```
    *   `MCP_BROWSER_HEADLESS=False`: This tells the `BrowserSettings` group that the `headless` option should be `False`. This means the browser will open visibly.
        *   `MCP_BROWSER_` is the prefix for `BrowserSettings`.
        *   `HEADLESS` is the name of the setting within `BrowserSettings`.
    *   Change `/path/to/your/custom/downloads` to an actual folder on your computer where you want files to be saved. For example, on Linux/macOS, it could be `/tmp/my_browser_downloads`, and on Windows, `C:\my_browser_downloads`.

    **Explanation**: The `Pydantic-Settings` library automatically looks for environment variables that start with `MCP_BROWSER_` for `BrowserSettings`, `MCP_PATHS_` for `PathSettings`, and so on. The `_` separates the prefix from the actual setting name.

Now, when you run the `mcp-browser-use` server or CLI (which we'll cover later), it will automatically load these settings from your `.env` file!

## How Settings Work Under the Hood

Let's peek at the file `src/mcp_server_browser_use/config.py` to understand how these settings are defined and loaded.

### Defining Setting Groups

Each group of settings is defined as a Python class that inherits from `BaseSettings`.

```python
# src/mcp_server_browser_use/config.py (simplified)

from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MCP_LLM_") # Important: This defines the prefix!

    provider: str = Field(default="google", env="PROVIDER") # MCP_LLM_PROVIDER
    model_name: str = Field(default="gemini-2.5-flash-preview-04-17", env="MODEL_NAME") # MCP_LLM_MODEL_NAME
    temperature: float = Field(default=0.0, env="TEMPERATURE") # MCP_LLM_TEMPERATURE
    api_key: Optional[SecretStr] = Field(default=None, env="API_KEY") # MCP_LLM_API_KEY
    # ... more LLM settings ...

class BrowserSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MCP_BROWSER_") # Its prefix is MCP_BROWSER_

    headless: bool = Field(default=False, env="HEADLESS") # MCP_BROWSER_HEADLESS
    disable_security: bool = Field(default=False, env="DISABLE_SECURITY") # MCP_BROWSER_DISABLE_SECURITY
    binary_path: Optional[str] = Field(default=None, env="BINARY_PATH") # MCP_BROWSER_BINARY_PATH
    # ... more browser settings ...

class PathSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MCP_PATHS_") # Its prefix is MCP_PATHS_

    downloads: str = Field(default="./tmp/downloads", env="DOWNLOADS") # MCP_PATHS_DOWNLOADS
    recordings: str = Field(default="./tmp/recordings", env="RECORDINGS") # MCP_PATHS_RECORDINGS
    # ... more path settings ...

# And so on for AgentToolSettings, ResearchToolSettings, ServerSettings...
```
**Explanation**:
*   `class LLMSettings(BaseSettings):`: This creates a new group for LLM-related settings.
*   `model_config = SettingsConfigDict(env_prefix="MCP_LLM_")`: This is the magic line! It tells `Pydantic-Settings` to look for environment variables that start with `MCP_LLM_` (e.g., `MCP_LLM_PROVIDER`, `MCP_LLM_MODEL_NAME`) when filling in the values for this group.
*   `provider: str = Field(default="google", env="PROVIDER")`: This defines a setting named `provider`. Its default value is `"google"`. It will look for an environment variable named `MCP_LLM_PROVIDER`.

### Global Application Settings

All these individual setting groups are then combined into one large `AppSettings` class, which holds all the configuration for the entire application.

```python
# src/mcp_server_browser_use/config.py (simplified)

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",            # Look for a .env file
        env_file_encoding="utf-8",
        extra="ignore",             # Ignore extra env vars not defined
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    agent_tool: AgentToolSettings = Field(default_factory=AgentToolSettings)
    research_tool: ResearchToolSettings = Field(default_factory=ResearchToolSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)

# Create a single global instance of our settings
settings = AppSettings()
```
**Explanation**:
*   `class AppSettings(BaseSettings):`: This is the main class that combines all the smaller setting groups.
*   `env_file=".env"`: This tells `Pydantic-Settings` to automatically load variables from a file named `.env` if it exists.
*   `llm: LLMSettings = Field(default_factory=LLMSettings)`: This line means that `AppSettings` has a property called `llm`, which is an instance of `LLMSettings`. This is how all the specific settings are nested.

### Loading Settings in the Server

When the FastMCP server starts (as seen in `src/mcp_server_browser_use/server.py`), it simply imports the `settings` object that was created in `config.py`.

```python
# src/mcp_server_browser_use/server.py (simplified)

from .config import settings # Import global AppSettings instance

# ... later in the code ...

def serve() -> FastMCP:
    # ...
    # When creating a custom browser, it uses settings.browser.headless
    agent_headless_override = settings.agent_tool.headless
    browser_headless = agent_headless_override if agent_headless_override is not None else settings.browser.headless

    # When configuring deep research, it uses settings.research_tool.save_dir
    if settings.research_tool.save_dir:
        # If save_dir is provided, construct the full save directory path for this specific task
        save_dir_for_this_task = str(Path(settings.research_tool.save_dir) / task_id)

    # When configuring LLMs, it uses settings.llm.* values
    research_llm = internal_llm_provider.get_llm_model(settings.get_llm_config(is_planner=True)) # Example

    # ... and so on ...
```
**Explanation**:
This code shows how different parts of the application (like setting up the browser or configuring the LLM) access the `settings` object to get the values they need. Since the `settings` object has already loaded all the configurations from the `.env` file (or environment variables), the changes you made are now applied!

## Recap & Next Steps

You've learned that **Settings & Configuration** is the control panel for `mcp-browser-use`. It uses a clever system to let you adjust how the server, browser, and AI agents behave without touching the core code. By creating a simple `.env` file, you can easily customize vital behaviors, like making the browser visible or changing download locations. This makes the application incredibly flexible for different uses.

In the next chapter, we'll dive into the [Browser Use Agent (Browser Automation Orchestrator)](03_browser_use_agent__browser_automation_orchestrator__.md), the component that actually orchestrates browser actions based on the tasks given by the FastMCP server and guided by these very settings!

[Next Chapter: Browser Use Agent (Browser Automation Orchestrator)](03_browser_use_agent__browser_automation_orchestrator__.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)