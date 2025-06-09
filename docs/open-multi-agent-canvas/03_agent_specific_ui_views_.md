# Chapter 3: Agent-Specific UI Views

Welcome to Chapter 3! In [Chapter 2: Frontend Agent Orchestration](02_frontend_agent_orchestration_.md), we learned how our application manages multiple AI agents and determines which one is "active." We saw how the `Canvas.tsx` component acts like a stage manager, knowing who's supposed to be in the spotlight.

But what exactly does the audience (the user) *see* when an agent is active? If the Travel Agent is planning a trip, we probably want to see a map, not a blank screen. If the Research Agent has found information, we'd expect to see a report. This is where **Agent-Specific UI Views** come into play.

**What Problem Do They Solve?**

Imagine you're in a high-tech control room. There isn't just one giant screen showing everything. Instead, you have:
*   A screen for navigation (like a GPS).
*   A screen for system diagnostics (showing charts and logs).
*   A screen for communication status.

Each screen is specialized to display specific information in the clearest way possible. Agent-Specific UI Views are just like these specialized dashboards. Each AI agent in our application might have unique information to show or require unique ways for the user to interact with it.

For example:
*   Our **Travel Agent** needs to display flight itineraries and places on a map.
*   Our **AI Research Agent** needs to present its findings as a structured document or report.
*   Our **MCP Agent** (Master Control Program Agent) needs to show logs of its operations and responses from backend services.

Agent-Specific UI Views provide these dedicated "dashboards" for each agent, ensuring the user gets the right information in the right format.

**Our Goal for This Chapter:**

We want to understand what these specialized UI views are, see examples of how they're built for different agents in `open-multi-agent-canvas`, and learn how they get displayed when their respective agent is active.

## What are Agent-Specific UI Views?

Agent-Specific UI Views are distinct **React components** responsible for rendering the unique outputs and interactive elements for each specialized agent.

Think of them as the "face" of each agent within the main application area. When the Travel Agent is active, its view (e.g., a map) is shown. When the Research Agent is active, its view (e.g., a report) takes center stage.

These views are not just static displays; they can be interactive and update dynamically as the agent works or as the user interacts with the chat.

## Examples of Agent UI Views in Our Project

Let's look at a few examples from `open-multi-agent-canvas` to make this concrete. These UI components are typically found in the `frontend/src/components/agents/` directory.

### 1. The Travel Agent's View: Showing a Map

The Travel Agent's main job is to help with travel plans, which often involve locations. So, its specific UI view is a map!

This is primarily handled by `frontend/src/components/agents/travel.tsx`, which uses the `MapComponent` from `frontend/src/components/map-container.tsx`.

```typescript
// frontend/src/components/agents/travel.tsx (Simplified)
import Map from "@/components/map"; // Our custom map component

export const TravelAgent = () => {
  // This component's job is to render the Map.
  // The Map component itself will handle showing trip data.
  return <Map />;
};
```
**Explanation:**
*   The `TravelAgent` component is very straightforward: it renders another component called `<Map />`.
*   The actual map display, including markers for places and trip details, is managed within the `<Map />` component (which internally uses `MapComponent` from `map-container.tsx`).
*   The data for the map (like points of interest) often comes from actions defined within `MapComponent` itself, such as the `add_trips` action we saw in [Chapter 1: CopilotKit AI Interaction Core](01_copilotkit_ai_interaction_core_.md). When that action successfully adds trips, the `MapComponent` updates its state, and the map display changes.

So, when the Travel Agent is active and has trip data, the user sees an interactive map in the main canvas area.

### 2. The AI Research Agent's View: Displaying Reports

The AI Research Agent gathers information and presents it. Its specific UI view is designed to show this research in a readable format, like a report, along with any sources or logs.

This is handled by `frontend/src/components/agents/researcher.tsx`.

```typescript
// frontend/src/components/agents/researcher.tsx (Simplified)
import { AvailableAgents } from "@/lib/available-agents";
import { useCoAgent } from "@copilotkit/react-core"; // To get agent state
import ReactMarkdown from "react-markdown"; // To show formatted reports
// ... other imports ...

// Defines the structure of the Research Agent's data
export type ResearchAgentState = {
  report: string; // The main research report text
  resources: Array<{ url: string; title: string }>; // List of sources
  // ... other fields like logs ...
};

export const AIResearchAgent: FC = () => {
  // Get the current state of the research agent
  const { state: researchAgentState } = useCoAgent<ResearchAgentState>({
    name: AvailableAgents.RESEARCH_AGENT,
    // ... initial state for the agent ...
  });

  // If the agent is working, show a loading skeleton (simplified)
  // if (isResearchInProgress.current) return <ResearchPaperSkeleton />;

  // If there's no report data yet, render nothing for this view
  if (!researchAgentState.report) {
    return null;
  }

  // Otherwise, display the report and resources
  return (
    <div className="research-report-view">
      <h2>Research Findings</h2>
      <ReactMarkdown>{researchAgentState.report}</ReactMarkdown>
      {/* UI to list researchAgentState.resources would go here */}
    </div>
  );
};
```
**Explanation:**
*   The `AIResearchAgent` component uses the `useCoAgent` hook to access its state, which includes the `report` text and `resources`.
*   It uses the `ReactMarkdown` library to display the `report` content, allowing for rich text formatting.
*   Crucially, if `researchAgentState.report` is empty (meaning no research has been completed or presented yet), this component returns `null`. This means it won't take up space on the screen.
*   When the Research Agent produces a report, this view will automatically update to display it.

### 3. The MCP Agent's View: Showing Logs and Responses

The MCP (Master Control Program) Agent interacts with backend services. Its view is designed to show the status of these operations, any logs generated, and the final responses.

This is handled by `frontend/src/components/agents/mcp-agent.tsx`.

```typescript
// frontend/src/components/agents/mcp-agent.tsx (Simplified)
import { AvailableAgents } from "@/lib/available-agents";
import { useCoAgent } from "@copilotkit/react-core";
import ReactMarkdown from "react-markdown"; // For formatted responses
// ... other imports ...

export type MCPAgentState = {
  response: string; // The final response from the MCP
  logs: Array<{ message: string; done: boolean }>; // Logs of operations
};

export const MCPAgent: FC = () => {
  const { state: mcpAgentState } = useCoAgent<MCPAgentState>({
    name: AvailableAgents.MCP_AGENT,
    // ... initial state ...
  });

  // If processing, show logs (simplified)
  // if (isProcessing.current) return <MCPLoadingView logs={mcpAgentState.logs} />;

  // If there's no response, render nothing for this view
  if (!mcpAgentState.response) {
    return null;
  }

  // Display the final response
  return (
    <div className="mcp-agent-view">
      <h3>MCP Agent Response:</h3>
      <ReactMarkdown>{mcpAgentState.response}</ReactMarkdown>
      {/* Optionally, display logs here too */}
    </div>
  );
};
```
**Explanation:**
*   Similar to the Research Agent, the `MCPAgent` component fetches its state (like `response` and `logs`) using `useCoAgent`.
*   It can display ongoing logs while processing and then the final `response` (perhaps formatted with `ReactMarkdown`).
*   It also returns `null` if there's no significant data (like a `response`) to display, ensuring it only appears when relevant.

## How These Views Are Displayed: The Stage and the Performers

In [Chapter 2: Frontend Agent Orchestration](02_frontend_agent_orchestration_.md), we saw that `frontend/src/components/canvas.tsx` is our main "stage." How does it decide to show, for example, the `<Agents.TravelAgent />` view?

It's quite clever! The `Canvas.tsx` component doesn't actually have a big `if/else` block to pick which agent UI to render. Instead, it includes *all* potential agent UI components. Each agent-specific UI component then decides for itself whether it should be visible or not.

Here's a simplified look at the relevant part of `frontend/src/components/canvas.tsx`:

```typescript
// frontend/src/components/canvas.tsx (Simplified Rendering Logic)
// ... other imports ...
import * as Agents from "@/components/agents"; // Imports all agent UIs
// ...

export default function Canvas() {
  // ... logic to determine if ANY agent is currently active for the banner ...
  // const { status: travelAgentRunning, ... } = useCoAgent(...);
  // const currentlyRunningAgent = getCurrentlyRunningAgent(...);

  return (
    // ... overall layout ...
    <div className="main-display-area"> {/* This is where agent views appear */}
      <Agents.TravelAgent />      {/* The Travel Agent's UI view */}
      <Agents.AIResearchAgent />  {/* The Research Agent's UI view */}
      <Agents.MCPAgent />         {/* The MCP Agent's UI view */}

      {/* If no agent is actively displaying content, show a default message */}
      {/* This condition checks if any agent considers itself "running" for the banner purpose */}
      {!currentlyRunningAgent?.status && <DefaultView />}
    </div>
    // ...
  );
}
```
**Explanation:**
*   `<Agents.TravelAgent />`, `<Agents.AIResearchAgent />`, and `<Agents.MCPAgent />` are all rendered.
*   However, as we saw in their individual component definitions, each of these components (like `AIResearchAgent` or `MCPAgent`) will return `null` (nothing) if they don't have relevant data to display (e.g., no report, no response) or if their specific agent isn't the one that should be currently showing its UI.
*   The `MapComponent` (used by `TravelAgent`) also has logic to render `null` or a skeleton if it's not ready (e.g., `if (!pointsFrom.length) return null;`).
*   So, only the agent view that *should* be visible will actually render content. If no agent-specific view renders content, and no agent is marked as `currentlyRunningAgent` (for the top banner), the `<DefaultView />` is shown.

This approach keeps the `Canvas.tsx` clean and delegates the responsibility of "should I be visible?" to the individual agent UI components themselves. They typically base this decision on their own state, which is updated by agent actions or through `useCoAgent`.

Let's visualize this:

```mermaid
graph TD
    A[Canvas Component] -->|Renders all agent views| B(Agent Views Area)
    B --> BTA{TravelAgent View}
    B --> BRA{ResearchAgent View}
    B --> BMA{MCPAgent View}
    B --> BDV{Default View}

    subgraph Agent Logic
        BTA -- Map data exists? --> RTA[Shows Map]
        BTA -- No map data? --> NTA[Shows Nothing (null)]

        BRA -- Report exists? --> RRA[Shows Report]
        BRA -- No report? --> NRA[Shows Nothing (null)]

        BMA -- Response exists? --> RMA[Shows MCP Response]
        BMA -- No response? --> NMA[Shows Nothing (null)]
    end

    subgraph Display Logic
        BDV -- No other agent view is active AND no agent is 'running'? --> SDV[Shows Default Message]
    end

    style RTA fill:#ccffcc
    style RRA fill:#ccffcc
    style RMA fill:#ccffcc
    style SDV fill:#e6e6e6
```
The `Canvas` sets the stage, and each agent component decides if it's their cue to perform. If no one takes the stage, the `DefaultView` might appear.

## Connecting Views to Data

These Agent-Specific UI Views don't just appear out of nowhere; they need data to display! This data primarily comes from two sources we've touched upon:

1.  **Agent Actions (`useCopilotAction`):** As seen in [Chapter 1: CopilotKit AI Interaction Core](01_copilotkit_ai_interaction_core_.md), actions can update the application's state. For example, the `add_trips` action in `map-container.tsx` directly updates the state (`pointsFrom`, `center`) that the `MapComponent` uses to render the map.
2.  **Agent State (`useCoAgent`):** As discussed in [Chapter 2: Frontend Agent Orchestration](02_frontend_agent_orchestration_.md) and seen in the agent UI examples above, components use `useCoAgent` to get the latest state for their agent (e.g., `researchAgentState.report` or `mcpAgentState.response`). When this state changes (because the backend agent logic updated it), the UI component re-renders with the new data.

So, there's a flow: User interacts -> AI processes -> Agent performs actions/updates state -> Agent-Specific UI View reflects these changes.

## Conclusion

You've now seen how `open-multi-agent-canvas` provides **Agent-Specific UI Views** – dedicated React components that give each AI agent its own specialized "dashboard" within the application. You've learned:

*   These views are crucial for presenting information clearly and providing agent-specific interactivity.
*   Examples include the map for the Travel Agent, the report display for the Research Agent, and log/response views for the MCP Agent.
*   These views are standard React components, located in `frontend/src/components/agents/`.
*   The `Canvas.tsx` component renders all potential agent views, but each view intelligently decides whether to display itself based on its current state and data.
*   Data for these views comes from agent actions or the shared agent state managed by CopilotKit.

These views are the visual front-ends for our specialized agents. One of the most interesting agents is the MCP Agent, which can interact with backend services. How does it do that? And how do we integrate these services?

That's what we'll explore in the next chapter: [MCP Agent & Service Integration](04_mcp_agent___service_integration_.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)