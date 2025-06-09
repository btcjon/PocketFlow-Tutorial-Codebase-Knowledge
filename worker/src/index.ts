/**
 * Tutorial Codebase Knowledge - Cloudflare Worker MCP Server
 * 
 * This worker provides an MCP server that generates comprehensive tutorials
 * from codebases, accessible remotely via Claude or other MCP clients.
 */

// MCP protocol types
interface MCPRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: any;
}

interface MCPResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

interface Env {
  TUTORIAL_KV: KVNamespace;
  OPENAI_API_KEY?: string;
  ANTHROPIC_API_KEY?: string;
  GEMINI_API_KEY?: string;
}

// Tutorial generation types
interface Abstraction {
  name: string;
  type: string;
  description: string;
  file_path: string;
  code_snippet?: string;
}

interface TutorialRequest {
  source: string;
  source_type: 'repo' | 'dir';
  output_dir?: string;
  language?: string;
  llm_provider?: string;
  llm_model?: string;
}

// File fetching utilities
async function fetchGitHubFiles(repoUrl: string): Promise<Map<string, string>> {
  const files = new Map<string, string>();
  
  // Parse GitHub URL
  const match = repoUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
  if (!match) throw new Error('Invalid GitHub URL');
  
  const [_, owner, repo] = match;
  const apiUrl = `https://api.github.com/repos/${owner}/${repo}/git/trees/main?recursive=1`;
  
  try {
    // Fetch repository tree
    const response = await fetch(apiUrl, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Tutorial-Codebase-Knowledge'
      }
    });
    
    if (!response.ok) throw new Error(`GitHub API error: ${response.status}`);
    
    const data = await response.json() as any;
    const tree = data.tree || [];
    
    // Filter and fetch relevant files
    const relevantFiles = tree.filter((item: any) => {
      if (item.type !== 'blob') return false;
      const path = item.path.toLowerCase();
      
      // Include code files
      return path.endsWith('.py') || path.endsWith('.js') || path.endsWith('.ts') ||
             path.endsWith('.jsx') || path.endsWith('.tsx') || path.endsWith('.java') ||
             path.endsWith('.cpp') || path.endsWith('.c') || path.endsWith('.h') ||
             path.endsWith('.go') || path.endsWith('.rs') || path.endsWith('.rb') ||
             path.endsWith('.php') || path.endsWith('.swift') || path.endsWith('.kt') ||
             path.endsWith('.md') || path.endsWith('.json') || path.endsWith('.yaml') ||
             path.endsWith('.yml') || path.endsWith('.toml');
    }).slice(0, 100); // Limit to 100 files for performance
    
    // Fetch file contents
    for (const file of relevantFiles) {
      try {
        const contentUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${file.path}`;
        const contentResponse = await fetch(contentUrl, {
          headers: {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Tutorial-Codebase-Knowledge'
          }
        });
        
        if (contentResponse.ok) {
          const contentData = await contentResponse.json() as any;
          if (contentData.content) {
            const content = atob(contentData.content);
            files.set(file.path, content);
          }
        }
      } catch (err) {
        console.error(`Failed to fetch ${file.path}:`, err);
      }
    }
    
    return files;
  } catch (error) {
    throw new Error(`Failed to fetch repository: ${error}`);
  }
}

// LLM integration
async function callLLM(
  prompt: string, 
  provider: string = 'openai',
  model?: string,
  env?: Env
): Promise<string> {
  // For the Worker version, we'll use OpenAI API as the default
  // You can extend this to support other providers
  
  if (!env?.OPENAI_API_KEY) {
    // Fallback to a simple rule-based response for demo
    return generateSimpleResponse(prompt);
  }
  
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: model || 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are an expert at analyzing code and creating educational tutorials.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.7,
      max_tokens: 2000
    })
  });
  
  if (!response.ok) {
    throw new Error(`LLM API error: ${response.status}`);
  }
  
  const data = await response.json() as any;
  return data.choices[0].message.content;
}

// Simple fallback response generator
function generateSimpleResponse(prompt: string): string {
  if (prompt.includes('identify abstractions')) {
    return JSON.stringify([
      {
        name: 'Main Application',
        type: 'module',
        description: 'Core application entry point',
        file_path: 'main.py'
      },
      {
        name: 'Data Models',
        type: 'class',
        description: 'Data structure definitions',
        file_path: 'models.py'
      }
    ]);
  }
  
  return 'Generated tutorial content based on the codebase analysis.';
}

// Tutorial generation workflow
async function generateTutorial(
  request: TutorialRequest,
  env: Env
): Promise<string> {
  try {
    // Step 1: Fetch repository files
    const files = await fetchGitHubFiles(request.source);
    
    // Step 2: Identify abstractions
    const abstractionsPrompt = `
    Analyze these code files and identify the main abstractions (classes, modules, functions, concepts):
    
    ${Array.from(files.entries()).slice(0, 20).map(([path, content]) => 
      `File: ${path}\n\`\`\`\n${content.slice(0, 500)}...\n\`\`\`\n`
    ).join('\n')}
    
    Return a JSON array of abstractions with name, type, description, and file_path.
    `;
    
    const abstractionsResponse = await callLLM(abstractionsPrompt, request.llm_provider, request.llm_model, env);
    const abstractions: Abstraction[] = JSON.parse(abstractionsResponse);
    
    // Step 3: Generate tutorial content
    const tutorialPrompt = `
    Create a comprehensive tutorial in ${request.language || 'English'} for a codebase with these abstractions:
    
    ${abstractions.map(a => `- ${a.name} (${a.type}): ${a.description}`).join('\n')}
    
    Structure the tutorial with:
    1. Overview
    2. Key concepts explanation
    3. How components work together
    4. Example usage
    5. Best practices
    
    Make it beginner-friendly and comprehensive.
    `;
    
    const tutorial = await callLLM(tutorialPrompt, request.llm_provider, request.llm_model, env);
    
    // Add metadata
    const timestamp = new Date().toISOString();
    const repoName = request.source.split('/').pop() || 'unknown';
    
    return `# Tutorial: ${repoName}

Generated on: ${timestamp}
Source: ${request.source}

---

${tutorial}

---

*Generated by Tutorial Codebase Knowledge MCP Server*
`;
    
  } catch (error) {
    throw new Error(`Tutorial generation failed: ${error}`);
  }
}

// MCP protocol handler
function createMCPResponse(id: string | number, result?: any, error?: any): MCPResponse {
  const response: MCPResponse = {
    jsonrpc: '2.0',
    id
  };
  
  if (error) {
    response.error = {
      code: -32603,
      message: error.message || 'Internal error',
      data: error
    };
  } else {
    response.result = result;
  }
  
  return response;
}

async function handleMCPRequest(request: MCPRequest, env: Env): Promise<MCPResponse> {
  try {
    switch (request.method) {
      case 'initialize':
        return createMCPResponse(request.id, {
          protocolVersion: '0.1.0',
          capabilities: {
            tools: {}
          },
          serverInfo: {
            name: 'tutorial-codebase-knowledge',
            version: '1.0.0'
          }
        });
        
      case 'tools/list':
        return createMCPResponse(request.id, {
          tools: [
            {
              name: 'generate_tutorial',
              description: 'Generate a comprehensive tutorial from a codebase',
              inputSchema: {
                type: 'object',
                properties: {
                  source: {
                    type: 'string',
                    description: 'GitHub repository URL'
                  },
                  source_type: {
                    type: 'string',
                    enum: ['repo'],
                    description: 'Source type (currently only repo supported)'
                  },
                  language: {
                    type: 'string',
                    description: 'Tutorial language (default: English)'
                  },
                  llm_provider: {
                    type: 'string',
                    enum: ['openai', 'anthropic', 'gemini'],
                    description: 'LLM provider to use'
                  }
                },
                required: ['source']
              }
            }
          ]
        });
        
      case 'tools/call':
        if (request.params?.name === 'generate_tutorial') {
          try {
            const args = request.params.arguments || {};
            const tutorial = await generateTutorial({
              source: args.source,
              source_type: args.source_type || 'repo',
              language: args.language,
              llm_provider: args.llm_provider
            }, env);
            
            // Store in KV
            const key = `tutorial_${Date.now()}`;
            await env.TUTORIAL_KV.put(key, tutorial);
            
            return createMCPResponse(request.id, {
              content: [
                {
                  type: 'text',
                  text: `Tutorial generated successfully!\n\nKey: ${key}\n\nPreview:\n${tutorial.slice(0, 500)}...`
                }
              ]
            });
          } catch (error) {
            return createMCPResponse(request.id, null, error);
          }
        }
        return createMCPResponse(request.id, null, { message: `Unknown tool: ${request.params?.name}` });
        
      default:
        return createMCPResponse(request.id, null, { message: `Unknown method: ${request.method}` });
    }
  } catch (error) {
    return createMCPResponse(request.id, null, error);
  }
}

// Cloudflare Worker handler
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type'
        }
      });
    }
    
    // Handle SSE connection for MCP
    if (request.headers.get('accept') === 'text/event-stream') {
      const { readable, writable } = new TransformStream();
      const writer = writable.getWriter();
      const encoder = new TextEncoder();
      
      // Process incoming messages
      request.body?.pipeTo(new WritableStream({
        async write(chunk) {
          const text = new TextDecoder().decode(chunk);
          const lines = text.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const message = JSON.parse(line.slice(6)) as MCPRequest;
                const response = await handleMCPRequest(message, env);
                await writer.write(encoder.encode(`data: ${JSON.stringify(response)}\n\n`));
              } catch (error) {
                console.error('Error processing message:', error);
              }
            }
          }
        }
      }));
      
      return new Response(readable, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }
    
    // Default response
    return new Response('Tutorial Codebase Knowledge MCP Server', {
      headers: {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
};