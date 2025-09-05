# Studio 5000 Logix Designer Documentation MCP Server

This MCP (Model Context Protocol) server provides seamless access to Studio 5000/Logix Designer instruction documentation within AI conversations. It enables you to search for and retrieve detailed information about PLC instructions, programming syntax, parameters, and best practices directly while coding.

## Features

- **Search Instructions**: Find PLC instructions by name, description, or category
- **Detailed Information**: Get comprehensive details about instruction syntax, parameters, and usage
- **Category Browsing**: Browse instructions by functional categories (Alarm, Math, Motion, etc.)
- **Language Support**: Information about which programming languages support each instruction (Ladder, Function Block, Structured Text)
- **Real-time Access**: Instant access to documentation without leaving your development environment

## Installation

### Prerequisites

- Python 3.8 or higher
- Studio 5000 Logix Designer installed (for documentation access)

### Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test the Server**:
   ```bash
   python studio5000_mcp_server.py --doc-root "C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000" --test
   ```

   This should show that the server successfully indexed your Studio 5000 documentation.

## Configuration for Claude Desktop

To use this MCP server with Claude Desktop, add the following to your Claude configuration:

### Windows Configuration

Add to your Claude Desktop configuration file (typically found in `%APPDATA%\Claude\config.json`):

```json
{
  "mcpServers": {
    "studio5000-docs": {
      "command": "python",
      "args": [
        "C:\\Users\\kontr\\Studio5000_MCP_Server\\studio5000_mcp_server.py",
        "--doc-root",
        "C:\\Program Files (x86)\\Rockwell Software\\Studio 5000\\Logix Designer\\ENU\\v36\\Bin\\Help\\ENU\\rs5000"
      ],
      "cwd": "C:\\Users\\kontr\\Studio5000_MCP_Server"
    }
  }
}
```

### Alternative: Using Cursor IDE

If you're using Cursor IDE, you can configure the MCP server in your workspace settings:

1. Open Cursor settings (Ctrl+,)
2. Navigate to the MCP section
3. Add a new MCP server with the following details:
   - **Name**: Studio 5000 Documentation
   - **Command**: `python C:\Users\kontr\Studio5000_MCP_Server\studio5000_mcp_server.py --doc-root "C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000"`

## Available Tools

Once configured, the following tools will be available in your AI conversations:

### 1. Search Instructions
**Tool**: `search_instructions`
**Parameters**: 
- `query` (string): Search term (instruction name, description, etc.)
- `category` (optional string): Filter by instruction category

**Example**: Search for timer-related instructions

### 2. Get Instruction Details
**Tool**: `get_instruction`
**Parameters**:
- `name` (string): Exact instruction name (e.g., "TON", "MOV", "ADD")

**Example**: Get complete details about the ADD instruction

### 3. List Categories
**Tool**: `list_categories`
**Parameters**: None

**Example**: See all available instruction categories

### 4. List Instructions by Category
**Tool**: `list_instructions_by_category`
**Parameters**:
- `category` (string): Category name

**Example**: List all Motion instructions

### 5. Get Instruction Syntax
**Tool**: `get_instruction_syntax`
**Parameters**:
- `name` (string): Instruction name

**Example**: Get syntax and parameters for a specific instruction

## Usage Examples

Once the MCP server is configured, you can ask questions like:

- "What instructions are available for timer operations?"
- "Show me the syntax for the MOV instruction"
- "What are all the Motion instructions available?"
- "How do I use the ADD instruction in ladder logic?"
- "What parameters does the PID instruction require?"

The AI will automatically use the MCP server tools to provide accurate, up-to-date information from your Studio 5000 documentation.

## Troubleshooting

### Common Issues

1. **Server fails to start**: 
   - Ensure Python and dependencies are installed
   - Check that the documentation path exists
   - Verify file permissions

2. **No instructions found**:
   - Confirm the `--doc-root` path points to the correct Studio 5000 documentation folder
   - Check that the 17691.htm file exists in the documentation directory

3. **Permission errors**:
   - Run the command prompt as administrator if needed
   - Ensure read access to the Studio 5000 documentation folder

### Testing the Server

Run the test mode to verify everything is working:

```bash
python studio5000_mcp_server.py --doc-root "C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000" --test
```

This will:
- Index all available instructions
- Show sample search results
- Display instruction categories
- Confirm the server is functioning properly

## Technical Details

The MCP server:
- Parses HTML documentation files using BeautifulSoup
- Builds an in-memory index of all instructions
- Extracts instruction names, categories, descriptions, syntax, and parameters
- Provides fast search and retrieval capabilities
- Follows the Model Context Protocol specification for AI integration

## File Structure

```
C:\Users\kontr\Studio5000_MCP_Server\
├── studio5000_mcp_server.py    # Main MCP server implementation
├── requirements.txt            # Python dependencies
├── mcp_config.json            # Sample MCP configuration
└── README.md                  # This documentation
```

## Contributing

This MCP server can be extended to support:
- Additional documentation formats
- Enhanced search capabilities
- Caching for improved performance
- Support for multiple Studio 5000 versions
- Integration with other Rockwell software documentation

## License

This project is provided as-is for educational and development purposes. Studio 5000 and Logix Designer are trademarks of Rockwell Automation.
