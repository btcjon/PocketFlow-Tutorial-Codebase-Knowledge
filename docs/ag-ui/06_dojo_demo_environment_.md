# Chapter 6: Dojo Demo Environment

Welcome to the final chapter of our AG-UI tutorial! In [Chapter 5: Event Encoding and Transport](05_event_encoding_and_transport_.md), we explored how AG-UI events are packaged and sent across the network. Now, it's time to see all these concepts come alive in a practical, interactive setting: the **Dojo Demo Environment**.

## What is the Dojo? Your Interactive AG-UI Playground

Imagine you've learned all about a new type of engine. You've studied its parts, how they communicate, and how fuel is delivered. Wouldn't it be great to visit an exhibition hall where you can see different vehicles using this engine, watch them run, and even peek under the hood?

That's exactly what the **Dojo Demo Environment** is for AG-UI!

The "Dojo" is an interactive web application designed specifically to showcase various AG-UI features and integrations. Think of it as an **exhibition hall** where each "booth" is a specific **demo**. Each demo highlights a particular capability of AG-UI, such as:
*   Building an AI chatbot that can use frontend tools (agentic chat).
*   Creating interactions where humans and AI collaborate on tasks (human-in-the-loop).
*   Implementing agents that can update shared information with the UI.

The Dojo helps you:
*   **See AG-UI in action**: Witness firsthand how different features work.
*   **Understand the code**: Explore the source code for each demo to see how it's implemented.
*   **Get inspiration**: Find examples and patterns you can use in your own AG-UI projects.

It's built using modern web technologies like Next.js (a React framework), making it a responsive and user-friendly web application.

## A Quick Tour of the Dojo

When you open the Dojo in your web browser, you'll typically see a layout like this:

```mermaid
graph TD
    DojoUI[Dojo Demo Environment UI] --> Sidebar[Sidebar (Left)]
    DojoUI --> MainContent[Main Content Area (Right)]

    Sidebar --> DemoList[Demo List (Select a Demo)]
    Sidebar --> ViewTabs[View Tabs (Preview, Code, Docs)]

    MainContent --> PreviewTab[Preview Tab (Interactive Demo)]
    MainContent --> CodeTab[Code Tab (View Source Code)]
    MainContent --> DocsTab[Docs Tab (Read Demo Information)]

    CodeTab --> FileTreeNav[File Tree Navigator]
    CodeTab --> FileTree[File List]
    CodeTab --> CodeEditor[Code Viewer]
```

Let's break down the main parts:

1.  **Sidebar (on the left)**: This is your control panel.
    *   **Demo List**: You'll find a list of available demos, like "Agentic Chat" or "Human in the Loop." Clicking on a demo loads it into the main content area. (This is handled by `DemoList` in `dojo/src/components/sidebar/sidebar.tsx`).
    *   **View Tabs**: Above or within the demo list area, you'll usually find tabs to switch between different views for the selected demo:
        *   👁️ **Preview**: See the demo live and interact with it.
        *   💻 **Code**: Look at the source code of the demo.
        *   📖 **Docs**: Read a description and explanation (often a README file) for the demo.

2.  **Main Content Area (on the right)**: This is where the action happens.
    *   **Preview Tab**: This is where the selected demo runs. You can chat with the agent, click buttons, and see AG-UI features working in real-time. For instance, in an agentic chat demo, you'd see the chat interface and the AI's responses.
    *   **Code Tab**: When you select this tab, the main area transforms into a code exploration view.
        *   **File Tree**: You'll see a list of files that make up the demo (e.g., `page.tsx` for the UI, `agent.py` for the agent logic). (Handled by `FileTree` in `dojo/src/components/file-tree/file-tree.tsx`).
        *   **Code Editor**: Clicking a file in the tree opens its content in a read-only code editor with syntax highlighting, so you can study how it works. (Handled by `CodeEditor` in `dojo/src/components/code-editor/code-editor.tsx`).
    *   **Docs Tab**: This view displays the `README.mdx` or `README.md` file associated with the demo, providing explanations, setup instructions, or highlights of what the demo showcases.

The overall structure and switching between these views are managed by components like `dojo/src/components/layout/main-layout.tsx` and `dojo/src/components/sidebar/sidebar.tsx`.

## What Makes a Demo Tick?

Each demo in the Dojo is a mini-application designed to showcase AG-UI. Here are the key ingredients:

### 1. Demo Configuration

Each demo is defined in a configuration file, typically `dojo/src/config.ts`. This file tells the Dojo what demos are available and where to find their information.

Here's a simplified example of how a demo might be configured:
```typescript
// Simplified from dojo/src/config.ts
function createDemoConfig({ id, name, description, tags }) {
  // ... (logic to find files for this demo, often from a generated files.json)
  return {
    id,          // Unique identifier, e.g., "agentic_chat"
    name,        // Display name, e.g., "Agentic Chat"
    description, // Short description
    path: `/feature/${id}`, // URL path to the demo
    tags,        // Keywords like "Chat", "Tools"
    files: [],   // List of source files (details gathered by a script)
  };
}

const config = [
  createDemoConfig({
    id: "agentic_chat",
    name: "Agentic Chat",
    description: "Chat with your Copilot and call frontend tools",
    tags: ["Chat", "Tools", "Streaming"],
  }),
  // ... other demos
];
```
This configuration helps the Dojo list the demos and load their respective pages and files.

### 2. The Demo Page (UI Implementation)

For each demo, there's a specific page component (e.g., `dojo/src/app/feature/agentic_chat/page.tsx`) that implements the user interface and integrates AG-UI client-side logic. This is where you'll see AG-UI components (often from libraries like `@copilotkit/react-core` and `@copilotkit/react-ui` which use AG-UI principles) in action.

For example, the "Agentic Chat" demo page might look like this:
```tsx
// Simplified from dojo/src/app/feature/agentic_chat/page.tsx
import React from "react";
import { CopilotKit } from "@copilotkit/react-core"; // Uses AG-UI
import { CopilotChat } from "@copilotkit/react-ui";  // UI for chat

const AgenticChatDemoPage: React.FC = () => {
  return (
    // CopilotKit sets up the AG-UI environment
    <CopilotKit runtimeUrl="/api/copilotkit" agent="agenticChatAgent">
      {/* CopilotChat provides the chat interface */}
      <CopilotChat labels={{ initial: "Hi, I'm an agent. Want to chat?" }} />
    </CopilotKit>
  );
};

export default AgenticChatDemoPage;
```
This page uses `CopilotKit` to connect to an agent backend. The `CopilotChat` component handles displaying messages, which are exchanged using the [AG-UI Events](01_ag_ui_events_.md) we learned about.

### 3. The Agent Logic

Each demo interacts with an AI agent. The agent's logic might be defined in:
*   A Python file (e.g., `agent.py`) if it's a Python-based agent running on a server.
*   A TypeScript file (e.g., `custom-agent.ts` as seen in [Chapter 2: Agent (Abstract Representation)](02_agent__abstract_representation__.md)) if it's a client-side or Node.js agent.
*   Sometimes, the agent logic is part of a backend API route (e.g., in `dojo/src/app/api/...`).

These agents are implementations that generate the [AG-UI Events](01_ag_ui_events_.md), process [Message and State Types](03_message_and_state_types_.md), and communicate using the [Event Encoding and Transport](05_event_encoding_and_transport_.md) mechanisms.

### 4. README Files

Each demo usually comes with a `README.mdx` (or `.md`) file. This file is displayed in the "Docs" tab and provides:
*   An overview of the demo.
*   What AG-UI features it highlights.
*   Sometimes, notes on how to understand its code.

## Behind the Scenes: Gathering Demo Content

To display the source code and READMEs in the Dojo's "Code" and "Docs" tabs, a build script is used. This script, often found at `dojo/scripts/generate-content-json.js`, runs before you start the Dojo.

**What the script does:**
1.  It looks at the demo configurations (like the one in `dojo/src/config.ts`).
2.  For each demo, it finds the specified source files (e.g., `agent.py`, `page.tsx`, `README.mdx`) from their locations in the project.
3.  It reads the content of these files.
4.  It bundles all this information (file names, paths, content, language for syntax highlighting) into a single JSON file, usually `src/files.json`.

```javascript
// Conceptual snippet from dojo/scripts/generate-content-json.js
// (Actual script is more complex)

// Configuration of files needed for each demo
const demoFileConfigs = {
  agentic_chat: ["agent.py", "page.tsx", "README.mdx"],
  // ... other demos
};

let allDemosContent = {};

for (const demoId in demoFileConfigs) {
  allDemosContent[demoId] = { files: [] };
  for (const fileName of demoFileConfigs[demoId]) {
    // const content = fs.readFileSync(path.join(demoDir, demoId, fileName), "utf8");
    // allDemosContent[demoId].files.push({ name: fileName, content: content, ... });
    // (Simplified: actual file reading and path logic is more detailed)
  }
}
// fs.writeFileSync("src/files.json", JSON.stringify(allDemosContent));
```
When you browse the "Code" or "Docs" tab in the Dojo, the UI reads from this pre-generated `files.json` to display the content. This makes loading the code and documentation very fast.

## Example: Exploring the "Agentic Chat" Demo

Let's say you want to understand how a basic agentic chat works with AG-UI:

1.  **Select the Demo**: In the Dojo's sidebar, click on "Agentic Chat."
2.  **Try it (Preview Tab)**:
    *   The main content area will load the chat interface.
    *   You can type messages and interact with the AI agent.
    *   Observe how the agent responds, perhaps using tools if the demo supports it. This interaction is powered by the [AG-UI Events](01_ag_ui_events_.md) flowing between the UI and the agent.
3.  **Examine the Code (Code Tab)**:
    *   Switch to the "Code" tab.
    *   In the file tree, you might find files like:
        *   `page.tsx`: Click to see the React component for the chat UI. Notice how it uses `CopilotKit` and `CopilotChat`.
        *   `agent.py` or a similar file for agent logic (or an API route file): Click to see how the agent is defined, how it handles user messages, and how it emits events.
        *   `style.css`: See any custom styling for this demo.
4.  **Read the Docs (Docs Tab)**:
    *   Switch to the "Docs" tab.
    *   Read the `README.mdx` for the "Agentic Chat" demo. It will likely explain the purpose of the demo and highlight key aspects of its implementation.

By going through these steps, you can connect the theoretical AG-UI concepts (Events, Agents, Messages, State, Transport) to concrete, working examples.

## Conclusion: Your Launchpad for AG-UI Mastery

The Dojo Demo Environment is more than just a collection of examples; it's an interactive learning tool. It provides a hands-on way to:
*   **Reinforce your understanding** of AG-UI concepts covered in this tutorial.
*   **Discover practical implementations** of various features.
*   **Bootstrap your own projects** by adapting code from the demos.

We've covered a lot in this tutorial series, from the fundamental [AG-UI Events](01_ag_ui_events_.md) that enable communication, the [Agent (Abstract Representation)](02_agent__abstract_representation__.md) that powers the AI, the [Message and State Types](03_message_and_state_types_.md) that structure the data, the client-side [Event Stream Processing Pipeline](04_event_stream_processing_pipeline__client_side__.md) that brings it all together in the UI, and the [Event Encoding and Transport](05_event_encoding_and_transport_.md) methods that carry these events.

The Dojo is the perfect place to see all these pieces working in harmony. We encourage you to spend time exploring the different demos, peeking at their code, and experimenting. This hands-on experience will be invaluable as you start building your own amazing applications with AG-UI.

Happy coding, and we're excited to see what you build!

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)