#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { spawn } from "child_process";
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import os from "os";

// Get the directory of this script
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the Python main.py script (relative to the package)
const PYTHON_SCRIPT_PATH = path.resolve(__dirname, "..", "..", "main.py");

interface TutorialResult {
  success: boolean;
  message: string;
  outputPath?: string;
  error?: string;
}

/**
 * Execute the Python tutorial generation script
 */
async function executePythonScript(
  source: string,
  sourceType: "repo" | "dir",
  outputDir?: string,
  language?: string,
  llmProvider?: string
): Promise<TutorialResult> {
  return new Promise((resolve) => {
    const args = [
      PYTHON_SCRIPT_PATH,
      sourceType === "repo" ? "--repo" : "--dir",
      source
    ];

    // Add optional parameters
    if (outputDir) {
      args.push("--output", outputDir);
    }
    if (language && language.toLowerCase() !== "english") {
      args.push("--language", language);
    }
    if (llmProvider) {
      args.push("--llm-provider", llmProvider);
    }

    // Set up environment
    const env = {
      ...process.env,
      PYTHONPATH: path.resolve(__dirname, "..", ".."),
      LLM_PROVIDER: llmProvider || process.env.LLM_PROVIDER || "openrouter"
    };

    console.error(`Executing: python ${args.join(" ")}`);
    
    const pythonProcess = spawn("python", args, {
      env,
      cwd: path.resolve(__dirname, "..", ".."),
      stdio: ["pipe", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    pythonProcess.stdout.on("data", (data) => {
      stdout += data.toString();
      console.error(`Python stdout: ${data.toString()}`);
    });

    pythonProcess.stderr.on("data", (data) => {
      stderr += data.toString();
      console.error(`Python stderr: ${data.toString()}`);
    });

    pythonProcess.on("close", (code) => {
      if (code === 0) {
        // Try to extract the output path from the logs
        const outputMatch = stdout.match(/Tutorial moved to docs folder: ([^\\n]+)/);
        const outputPath = outputMatch ? outputMatch[1] : undefined;
        
        resolve({
          success: true,
          message: `Tutorial generated successfully!${outputPath ? ` Saved to: ${outputPath}` : ""}`,
          outputPath
        });
      } else {
        resolve({
          success: false,
          message: `Tutorial generation failed with exit code ${code}`,
          error: stderr || stdout
        });
      }
    });

    pythonProcess.on("error", (error) => {
      resolve({
        success: false,
        message: `Failed to execute Python script: ${error.message}`,
        error: error.message
      });
    });
  });
}

/**
 * List generated tutorials in a directory
 */
async function listGeneratedTutorials(directory: string): Promise<string[]> {
  try {
    const resolvedDir = path.resolve(directory);
    const entries = await fs.readdir(resolvedDir, { withFileTypes: true });
    
    const tutorials: string[] = [];
    
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith("_tutorial.md")) {
        tutorials.push(path.join(resolvedDir, entry.name));
      } else if (entry.isDirectory()) {
        // Check if directory contains tutorial files
        try {
          const subEntries = await fs.readdir(path.join(resolvedDir, entry.name));
          const hasTutorial = subEntries.some(file => file.endsWith("_tutorial.md"));
          if (hasTutorial) {
            const tutorialFiles = subEntries
              .filter(file => file.endsWith("_tutorial.md"))
              .map(file => path.join(resolvedDir, entry.name, file));
            tutorials.push(...tutorialFiles);
          }
        } catch {
          // Ignore errors reading subdirectories
        }
      }
    }
    
    return tutorials;
  } catch (error) {
    console.error(`Error listing tutorials: ${error}`);
    return [];
  }
}

/**
 * Get tutorial content
 */
async function getTutorialContent(tutorialPath: string): Promise<string> {
  try {
    const resolvedPath = path.resolve(tutorialPath);
    const content = await fs.readFile(resolvedPath, "utf-8");
    return content;
  } catch (error) {
    throw new Error(`Failed to read tutorial: ${error}`);
  }
}

// Create the MCP server
const server = new McpServer({
  name: "tutorial-codebase-knowledge",
  version: "1.0.0"
});

// Add the generate_tutorial tool
server.tool(
  "generate_tutorial",
  {
    source: z.string().describe("GitHub repository URL (e.g. https://github.com/user/repo) or local directory path"),
    source_type: z.enum(["repo", "dir"]).optional().describe("Either 'repo' for GitHub URL or 'dir' for local directory (auto-detected if not specified)"),
    output_dir: z.string().optional().describe("Where to save the tutorial (default: ./mydocs for local dirs, ~/Dropbox/tutorial-docs for repos)"),
    language: z.string().optional().describe("Language for the tutorial (default: English)"),
    llm_provider: z.enum(["gemini", "openai", "anthropic", "openrouter"]).optional().describe("LLM provider to use (default: openrouter)")
  },
  async (params) => {
    const { source, source_type, output_dir, language, llm_provider } = params;
    
    // Auto-detect source type if not provided
    let detectedSourceType = source_type;
    if (!detectedSourceType) {
      if (source.startsWith("http://") || source.startsWith("https://") || source.startsWith("git@")) {
        detectedSourceType = "repo";
      } else {
        detectedSourceType = "dir";
      }
    }
    
    console.error(`Generating tutorial for ${source} (type: ${detectedSourceType})`);
    
    const result = await executePythonScript(
      source,
      detectedSourceType,
      output_dir,
      language || "english",
      llm_provider || "openrouter"
    );
    
    if (result.success) {
      return {
        content: [
          {
            type: "text" as const,
            text: result.message
          }
        ]
      };
    } else {
      return {
        content: [
          {
            type: "text" as const,
            text: `❌ ${result.message}${result.error ? `\\n\\nError details:\\n${result.error}` : ""}`
          }
        ]
      };
    }
  }
);

// Add the list_generated_tutorials tool
server.tool(
  "list_generated_tutorials",
  {
    directory: z.string().optional().describe("Directory to search for tutorials (default: ./mydocs)")
  },
  async (params) => {
    const directory = params.directory || "./mydocs";
    
    console.error(`Listing tutorials in: ${directory}`);
    
    const tutorials = await listGeneratedTutorials(directory);
    
    if (tutorials.length === 0) {
      return {
        content: [
          {
            type: "text" as const,
            text: `No tutorials found in ${path.resolve(directory)}`
          }
        ]
      };
    }
    
    const tutorialList = tutorials
      .map((tutorial, index) => `${index + 1}. ${path.basename(tutorial)} (${tutorial})`)
      .join("\\n");
    
    return {
      content: [
        {
          type: "text" as const,
          text: `Found ${tutorials.length} tutorial(s) in ${path.resolve(directory)}:\\n\\n${tutorialList}`
        }
      ]
    };
  }
);

// Add the get_tutorial_content tool
server.tool(
  "get_tutorial_content",
  {
    tutorial_path: z.string().describe("Path to the tutorial file")
  },
  async (params) => {
    const { tutorial_path } = params;
    
    console.error(`Reading tutorial: ${tutorial_path}`);
    
    try {
      const content = await getTutorialContent(tutorial_path);
      
      return {
        content: [
          {
            type: "text" as const,
            text: content
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text" as const,
            text: `❌ ${error instanceof Error ? error.message : String(error)}`
          }
        ]
      };
    }
  }
);

// Start the server
async function main() {
  console.error("Starting Tutorial Codebase Knowledge MCP Server...");
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error("MCP Server connected and ready!");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});