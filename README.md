# 🤖 Studio 5000 AI-Powered PLC Programming Assistant

This revolutionary MCP (Model Context Protocol) server transforms PLC programming by providing AI-powered code generation, L5X project creation, real .ACD file generation, and seamless Studio 5000 integration. Convert natural language specifications directly into working ladder logic and complete Studio 5000 projects!

## ⚡ **TL;DR - For Impatient Teammates**
```bash
# 1. Get Python 3.12 (NOT 3.11!) from python.org
python --version  # Must show 3.12.x

# 2. Clone and install
git clone <repository-url>
cd Studio5000_MCP_Server
pip install -r requirements.txt

# 3. Install SDK (CRITICAL for .ACD files!)
pip install "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\logix_designer_sdk-*-py3-none-any.whl"

# 4. Test it works
python src/mcp_server/studio5000_mcp_server.py --test
```
**That's it!** ✅ Skip to [Claude Desktop setup](#configuration-for-claude-desktop) if tests pass.

## 🚀 **Quick Start for Teammates**

**Ready to use this tool? Follow these steps:**

### **Prerequisites** ⚠️ CRITICAL
- **Python 3.12** (NOT 3.11 or earlier - the SDK will not work!)
- **Studio 5000 Logix Designer v36 or later** installed on your machine
- **Windows Operating System** (Studio 5000 SDK is Windows-only)

### **Installation Steps**

1. **Verify Python 3.12**:
   ```bash
   python --version
   # Must show Python 3.12.x - if not, install Python 3.12 from python.org
   ```

2. **Clone and Install**:
   ```bash
   git clone <repository-url>
   cd Studio5000_MCP_Server
   pip install -r requirements.txt
   ```

3. **Install Studio 5000 SDK** (for .ACD files):
   ```bash
   pip install "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\logix_designer_sdk-*-py3-none-any.whl"
   ```

4. **Test the Installation**:
   ```bash
   python src/mcp_server/studio5000_mcp_server.py --test
   ```
   ✅ Should show: Documentation indexed, SDK available, tests passing

5. **Ready to Use!** - The server will auto-detect your Studio 5000 installation paths

**Having Issues?** See the [Troubleshooting](#troubleshooting) section below.

## 🚀 AI-Powered Features

### **🧠 Natural Language to PLC Code**
- **AI Code Generation**: Convert plain English to working ladder logic
  - *"Start the motor when the start button is pressed and stop it when the stop button is pressed"* → Complete ladder logic with proper start/stop interlocking
- **Smart Pattern Recognition**: Automatically detects start/stop, timer, counter, and basic I/O patterns
- **Intelligent Tag Creation**: Automatically generates appropriate I/O tags with descriptive names
- **Instruction Validation**: Validates generated code against official Studio 5000 documentation database

### **📁 L5X Project Generation**
- **Complete Project Creation**: Generate full Studio 5000 L5X project files with programs, routines, and tags
- **Multiple Controller Support**: Support for various Allen-Bradley controllers (1756-L83E, 1756-L85E, etc.)
- **Ready-to-Import**: Projects can be directly imported into Studio 5000 Logix Designer
- **Structured Output**: Properly formatted XML with correct Studio 5000 schema

### **🏭 Real .ACD Project Creation**
- **Official Studio 5000 SDK Integration**: Creates genuine .ACD files using Rockwell's official SDK
- **Direct Studio 5000 Compatibility**: .ACD files open directly in Studio 5000 without conversion
- **Two Creation Modes**: 
  - **Empty Projects**: Clean templates ready for manual development
  - **🎉 Complete Projects**: Full projects with MainProgram, MainTask, and AI-generated ladder logic
- **Advanced SDK Integration**: Uses partial import functionality to create complete project structures
- **Version Control**: Supports different Studio 5000 major revisions (v36 default)

### **📚 Documentation Access**
- **Comprehensive Instruction Database**: Searches through official Studio 5000 documentation
- **Smart Search**: Find PLC instructions by name, description, category, or functionality
- **Detailed Information**: Get comprehensive details about instruction syntax, parameters, and usage
- **Category Browsing**: Browse instructions by functional categories (Alarm, Math, Motion, Timer, etc.)
- **Language Support**: Information about which programming languages support each instruction (Ladder, ST, FBD)
- **Real-time Validation**: Instant validation using official Rockwell documentation

## 📋 Detailed Installation Guide

### Prerequisites - READ THIS FIRST! ⚠️

**🚨 CRITICAL REQUIREMENT: Python 3.12 ONLY**
- This project **REQUIRES Python 3.12** - earlier versions will fail
- Studio 5000 SDK is **incompatible** with Python 3.11 and earlier
- **Verify your Python version FIRST** before proceeding

**System Requirements:**
- **Python 3.12.x** (Download from [python.org](https://www.python.org/downloads/))
- **Studio 5000 Logix Designer v36 or later** installed
- **Windows Operating System** (Studio 5000 SDK is Windows-only)
- **Administrator privileges** may be required for initial setup

### Step-by-Step Setup

#### Step 1: Install Python 3.12
1. **Download**: Go to [python.org](https://www.python.org/downloads/) and download Python 3.12
2. **Install**: During installation, **CHECK "Add Python to PATH"** ✅
3. **Verify**: Open Command Prompt and run:
   ```bash
   python --version
   # Must show: Python 3.12.x (if not, restart command prompt)
   ```

#### Step 2: Get the Project
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Studio5000_MCP_Server
   ```

#### Step 3: Install Dependencies (CRITICAL!)
1. **Install all required packages**:
   ```bash
   pip install -r requirements.txt
   ```
   **This installs**: BeautifulSoup, XML processing, vector databases, and AI components
   
   **If you get errors**, try:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

#### Step 3.5: Install Studio 5000 SDK (CRITICAL for .ACD files!) 🚨
**⚠️ TEAMMATES MUST DO THIS STEP** - Skip only if you don't need .ACD file creation

1. **Find the SDK wheel file** in your Studio 5000 installation:
   ```bash
   # Look for this file (version may vary):
   dir "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\logix_designer_sdk-*-py3-none-any.whl"
   ```

2. **Install the SDK wheel file**:
   ```bash
   # Replace with your actual file path and version:
   pip install "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\logix_designer_sdk-2.0.1-py3-none-any.whl"
   ```

3. **Alternative - if you can't find the wheel file**:
   ```bash
   # Navigate to the SDK directory and install from there:
   cd "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python"
   pip install logix_designer_sdk-*-py3-none-any.whl
   ```

**Without this step**: Documentation and L5X generation will work, but .ACD file creation will fail!

#### Step 4: Test Your Installation ✅
1. **Run the test command**:
   ```bash
   python src/mcp_server/studio5000_mcp_server.py --test
   ```

2. **You should see**:
   - ✅ "Documentation indexed successfully" (500+ instructions found)
   - ✅ "SDK Available: True" (if you installed the SDK wheel file correctly)
   - ✅ "SDK Available: False" (OK if you skipped SDK installation - L5X generation still works)
   - ✅ Sample search results and code generation tests

3. **If SDK Available shows False** but you installed the wheel file:
   - Check the wheel file path was correct
   - Try: `python -c "import logix_designer_sdk; print('SDK OK')"`

4. **If tests fail completely**, check the [Troubleshooting](#troubleshooting) section

🎉 **You're Ready to Use the Tool!** 🎉

The server will automatically detect your Studio 5000 installation paths. Skip to the [Configuration for Claude Desktop](#configuration-for-claude-desktop) section to start using it!

---

#### Step 5: Configure Environment Variables (Advanced Users Only)
**⚠️ SKIP THIS STEP** - Only needed if Studio 5000 is installed in non-standard locations

   **Option A: Set via Windows Environment Variables**
   - Open System Properties → Environment Variables
   - Add these User or System variables:
     ```
     STUDIO5000_DOC_PATH=C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000
     STUDIO5000_SDK_PATH=C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python
     PYTHON312_PATH=C:\Users\YourUsername\AppData\Local\Programs\Python\Python312\python.exe
     ```

   **Option B: Create `.env` file** (in project root):
   
   ```bash
   STUDIO5000_DOC_PATH=C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000
   STUDIO5000_SDK_PATH=C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python
   PYTHON312_PATH=C:\Users\YourUsername\AppData\Local\Programs\Python\Python312\python.exe
   ```

4. **Find Your Studio 5000 Paths**:
   
   **Documentation Path**: Look for this file in your Studio 5000 installation:
   ```
   <Studio5000_Install>\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000\17691.htm
   ```
   Common locations:
   - `C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000`
   - `C:\Program Files\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000`

   **SDK Path**: Look for the SDK Python folder:
   ```
   C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python
   ```

5. **Test the Server**:
   ```bash
   # Test with environment variables (recommended)
   python src/mcp_server/studio5000_mcp_server.py --test
   
   # Or test with explicit path
   python src/mcp_server/studio5000_mcp_server.py --doc-root "C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000" --test
   ```

   **Successful output should show**:
   - Documentation indexing (hundreds of instructions found)
   - Sample search results
   - AI code generation test
   - SDK availability status

## Configuration for Claude Desktop

To use this MCP server with Claude Desktop, add the following to your Claude configuration:

### Windows Configuration

Add to your Claude Desktop configuration file (typically found in `%APPDATA%\Claude\config.json`):

**Option A: Using Environment Variables (Recommended)**
```json
{
  "mcpServers": {
    "studio5000-ai-assistant": {
      "command": "python",
      "args": [
        "C:\\Users\\YourUsername\\Studio5000_MCP_Server\\src\\mcp_server\\studio5000_mcp_server.py"
      ],
      "cwd": "C:\\Users\\YourUsername\\Studio5000_MCP_Server",
      "env": {
        "STUDIO5000_DOC_PATH": "C:\\Program Files (x86)\\Rockwell Software\\Studio 5000\\Logix Designer\\ENU\\v36\\Bin\\Help\\ENU\\rs5000",
        "STUDIO5000_SDK_PATH": "C:\\Users\\Public\\Documents\\Studio 5000\\Logix Designer SDK\\python"
      }
    }
  }
}
```

**Option B: Using Command Line Arguments**
```json
{
  "mcpServers": {
    "studio5000-ai-assistant": {
      "command": "python",
      "args": [
        "C:\\Users\\YourUsername\\Studio5000_MCP_Server\\src\\mcp_server\\studio5000_mcp_server.py",
        "--doc-root",
        "C:\\Program Files (x86)\\Rockwell Software\\Studio 5000\\Logix Designer\\ENU\\v36\\Bin\\Help\\ENU\\rs5000"
      ],
      "cwd": "C:\\Users\\YourUsername\\Studio5000_MCP_Server"
    }
  }
}
```

**Important Notes:**
- Replace `YourUsername` with your actual Windows username
- Adjust the Studio 5000 paths to match your installation
- Use **Python 3.12** - specify full path if needed: `"command": "C:\\Users\\YourUsername\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"`

### Alternative: Using Cursor IDE

If you're using Cursor IDE, the MCP server is available by default when working in this project workspace. The server will automatically use environment variables if set, or you can configure it manually in Cursor's MCP settings.

## 🛠️ Available AI Tools

Once configured, these powerful tools will be available in your AI conversations:

### 🧠 **AI Code Generation Tools**

#### 1. Generate Ladder Logic
**Tool**: `generate_ladder_logic`
**Parameters**: 
- `specification` (string): Natural language description of desired PLC behavior

**Capabilities**:
- **Pattern Recognition**: Automatically detects start/stop, timer, counter, and basic I/O patterns
- **Smart Tag Generation**: Creates appropriate tag names and data types
- **Instruction Validation**: Uses Studio 5000 documentation database for validation

**Example**: *"Create logic to start a motor with a start button and stop it with a stop button"*

#### 2. Create L5X Project  
**Tool**: `create_l5x_project`
**Parameters**:
- `project_spec` (object): Project specification including:
  - `name` (string): Project name
  - `controller_type` (string): Controller model (e.g., "1756-L83E")
  - `specification` (string): Natural language description of logic
  - `save_path` (optional string): File path to save L5X file

**Output**: Complete Studio 5000 L5X project file ready for import

#### 3. Create Real .ACD Project - Empty Template
**Tool**: `create_acd_project`  
**Parameters**:
- `project_spec` (object): ACD project specification including:
  - `name` (string): Project name
  - `controller_type` (string): Controller model
  - `major_revision` (integer): Studio 5000 version (default 36)
  - `save_path` (string): File path for .ACD file

**Output**: Empty .ACD file using official Studio 5000 SDK - ready for manual development

#### 4. Create Complete .ACD Project - WITH MainProgram! 🎉
**Tool**: `create_complete_acd_project`  
**Parameters**:
- `project_spec` (object): Complete ACD project specification including:
  - `name` (string): Project name
  - `controller_type` (string): Controller model
  - `major_revision` (integer): Studio 5000 version (default 36)
  - `save_path` (string): File path for .ACD file
  - `ladder_logic` (string): Optional ladder logic in L5X rung format

**Output**: Complete .ACD file with MainProgram, MainTask, and ladder logic - opens directly in Studio 5000!

**🎯 This solves the original limitation!** You can now create ACD files that are immediately ready to use.


#### 5. Validate Ladder Logic
**Tool**: `validate_ladder_logic`
**Parameters**:
- `logic_spec` (object): Contains:
  - `ladder_logic` (string): Ladder logic code to validate
  - `instructions_used` (array): List of PLC instructions used

**Output**: Comprehensive validation report with errors, warnings, and suggestions

### 📚 **Documentation Tools**

#### 6. Search Instructions
**Tool**: `search_instructions`
**Parameters**: 
- `query` (string): Search term (instruction name, description, functionality)
- `category` (optional string): Filter by instruction category

**Features**: Searches through official Studio 5000 documentation database

#### 7. Get Instruction Details
**Tool**: `get_instruction`
**Parameters**:
- `name` (string): Exact instruction name (e.g., "TON", "MOV", "ADD", "PID")

**Output**: Complete instruction information including syntax, parameters, examples, and supported languages

#### 8. List Categories  
**Tool**: `list_categories`
**Parameters**: None (dummy parameter required)

**Output**: All available instruction categories (Alarm, Math, Motion, Timer, etc.)

#### 9. List Instructions by Category
**Tool**: `list_instructions_by_category`
**Parameters**:
- `category` (string): Category name

**Output**: All instructions within the specified category

#### 10. Get Instruction Syntax
**Tool**: `get_instruction_syntax`
**Parameters**:
- `name` (string): Instruction name

**Output**: Detailed syntax and parameter information for the instruction

## 🎯 **Three Powerful Approaches for PLC Project Creation**

Your MCP server supports **THREE different approaches** for PLC project creation, each optimized for different use cases:

### **🥇 Approach 1: Complete .ACD Generation (NEWEST & MOST POWERFUL!)**
🎉 **Generates**: Complete .ACD projects with MainProgram, MainTask, and AI-generated ladder logic  
🎉 **Output**: Ready-to-use .ACD file that opens directly in Studio 5000  
🎉 **Best for**: Automated development with immediate usability  
🎉 **Zero Manual Steps**: Everything is ready to go!  

**Usage**: *"Create a complete ACD project with conveyor control logic"*  
**Tool**: `create_complete_acd_project`

### **🥈 Approach 2: L5X Generation (Great for Import Workflows)**  
✅ **Generates**: Complete projects with MainProgram, MainTask, and ladder logic  
✅ **Output**: L5X file ready to import into Studio 5000  
✅ **Best for**: Import into existing projects or version control  
✅ **AI Integration**: Full AI-generated ladder logic included  

**Usage**: *"Create a complete L5X project for a conveyor system with start/stop logic"*  
**Tool**: `create_l5x_project`

### **🥉 Approach 3: Empty .ACD Templates (For Manual Development)**  
🛠️ **Generates**: Empty .ACD project file (clean template)  
🛠️ **Output**: Blank project that opens directly in Studio 5000  
🛠️ **Best for**: Starting point for completely manual development  
🛠️ **Manual Steps**: Create MainProgram and MainTask yourself  

**Usage**: *"Create an empty .ACD template for manual development"*  
**Tool**: `create_acd_project`

### **🎯 Problem SOLVED!**

**Previous Limitation**: ❌ Could only create empty .ACD files  
**NEW Capability**: ✅ **Complete .ACD files with MainProgram + MainTask + Ladder Logic!**

The enhanced SDK implementation uses Rockwell's `partial_import_from_xml_file()` method to:
1. Create an empty .ACD project
2. Generate L5X XML with MainProgram, MainTask, and your ladder logic
3. Import the complete structure into the .ACD file
4. Result: **Fully functional .ACD project ready for Studio 5000!**

## 💡 Usage Examples

Once the MCP server is configured, you can ask questions and generate code like:

### **🧠 AI Code Generation Examples**
- *"Create ladder logic to start a motor when a start button is pressed and stop it when a stop button is pressed"*
- *"Generate a conveyor control system with start, stop, and emergency stop"*
- *"Create a 5-second delay timer for a solenoid valve"*
- *"Build ladder logic for a pump control with auto/manual modes and run hours counter"*
- *"Design a three-station assembly line with interlocking and safety circuits"*

### **📁 Project Creation Examples** 
- *"Create a complete .ACD project with conveyor control logic and safety interlocks"* → **Complete .ACD with MainProgram + logic**
- *"Generate a motor control .ACD project for a 1756-L83E controller"* → **Ready-to-use .ACD file**
- *"Create a complete Studio 5000 L5X project for motor control with start/stop functionality"* → **L5X for import**
- *"Build a complete L5X project for a 3-station assembly line with safety interlocks"* → **Complex L5X projects**
- *"Create an empty .ACD template for manual development"* → **Clean template files**

### **📚 Documentation Examples**
- *"What timer instructions are available in Studio 5000?"*
- *"Show me the complete syntax and parameters for the PID instruction"*
- *"What are all the Motion Control instructions available?"*
- *"How do I use the GSV (Get System Value) instruction in ladder logic?"*
- *"What's the difference between TON, TOF, and RTO timer instructions?"*

### **🔍 Validation Examples**
- *"Validate this ladder logic: XIC(START)XIO(STOP)OTE(MOTOR)"*
- *"Check if my TON timer instruction usage is correct with these parameters"*
- *"Verify that my counter logic follows Studio 5000 best practices"*

### **🏭 Real-World Applications**
- *"Generate ladder logic for a car wash system with 5 sequential steps"*
- *"Create a complete project for a packaging line with conveyor controls and product counting"*
- *"Build a temperature control system with PID loop and alarm handling"*

The AI will automatically use the MCP server tools to provide accurate, up-to-date information based on your actual Studio 5000 documentation and generate working PLC code.

## Troubleshooting

### ❗ Critical Issues

#### 1. **Python Version Mismatch**
**Problem**: MCP server starts but SDK features don't work or you get import errors.

**Solution**:
```bash
# Check your Python version
python --version
# Must show 3.12.x

# If not 3.12, install Python 3.12 and use full path in Claude config:
"command": "C:\\Users\\YourUsername\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
```

**Why**: Studio 5000 SDK requires Python 3.12 specifically. Earlier versions will cause SDK import failures.

#### 2. **Documentation Path Not Found**
**Problem**: "Main index file not found" or "No instructions found"

**Solution - Find Your Documentation Path**:
1. **Open File Explorer** and search for: `17691.htm`
2. **Look in these common locations**:
   ```
   C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000\17691.htm
   C:\Program Files\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000\17691.htm
   C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v37\Bin\Help\ENU\rs5000\17691.htm
   ```
3. **Set the correct path** (everything except the filename):
   ```bash
   # Via environment variable
   set STUDIO5000_DOC_PATH=C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000
   
   # Or via command line
   python src/mcp_server/studio5000_mcp_server.py --doc-root "C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000" --test
   ```

#### 3. **SDK Not Available**
**Problem**: "Studio 5000 SDK not available" or "SDK import failed"

**Most Common Cause**: **You didn't install the SDK wheel file!** ⚠️

**Solution**:
1. **🚨 CRITICAL: Install the SDK wheel file first**:
   ```bash
   # Find and install the wheel file (most teammates miss this step!)
   pip install "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\logix_designer_sdk-*-py3-none-any.whl"
   ```

2. **Check SDK Installation**:
   - Look for: `C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\`
   - If missing, reinstall Studio 5000 with SDK components

3. **Verify SDK Works**:
   ```bash
   # Test if SDK is now available
   python -c "import logix_designer_sdk; print('SDK OK')"
   ```

4. **If still failing, set SDK Path**:
   ```bash
   set STUDIO5000_SDK_PATH=C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python
   ```

### ⚠️ Common Setup Issues

#### 4. **Server Fails to Start**
**Symptoms**: Server crashes immediately or shows JSON-RPC errors.

**Solutions**:
- **Check Python path in Claude config** - use full path to Python 3.12
- **Verify working directory** - `"cwd"` should point to project root
- **Check file permissions** - ensure read access to all project files
- **Test in isolation**:
  ```bash
  python src/mcp_server/studio5000_mcp_server.py --test
  ```

#### 5. **Environment Variables Not Working**
**Problem**: Server still uses hardcoded paths despite setting environment variables.

**Solutions**:
1. **Restart Command Prompt/IDE** after setting environment variables
2. **Check variable names** (case sensitive):
   - `STUDIO5000_DOC_PATH`
   - `STUDIO5000_SDK_PATH` 
   - `PYTHON312_PATH`
3. **Test environment variables**:
   ```bash
   echo %STUDIO5000_DOC_PATH%
   echo %STUDIO5000_SDK_PATH%
   ```

#### 6. **Claude Desktop Configuration Issues**
**Problem**: MCP server not appearing in Claude Desktop.

**Solutions**:
1. **Check config.json syntax** - use JSON validator
2. **Restart Claude Desktop** completely after config changes
3. **Use absolute paths** - no relative paths in Claude config
4. **Check Claude logs** in `%APPDATA%\Claude\logs\`

### 🔧 Advanced Troubleshooting

#### 7. **Multiple Python Versions**
If you have multiple Python versions installed:
```bash
# Use specific Python 3.12 executable
C:\Users\YourUsername\AppData\Local\Programs\Python\Python312\python.exe src/mcp_server/studio5000_mcp_server.py --test

# Or create virtual environment with Python 3.12
py -3.12 -m venv studio5000_env
studio5000_env\Scripts\activate
pip install -r requirements.txt
```

#### 8. **Corporate/Network Restrictions**
**Problem**: Cannot access documentation files due to permissions.

**Solutions**:
- **Run as Administrator** when testing
- **Check antivirus exclusions** for Python and Studio 5000 directories  
- **Verify network drive access** if Studio 5000 is on network share

#### 9. **Studio 5000 Version Compatibility**
**Problem**: Different Studio 5000 version than v36.

**Solutions**:
- **Update documentation path** to match your version (v37, v38, etc.)
- **Update major_revision parameter** in .ACD project creation
- **Check SDK version compatibility**

### 🧪 Testing Commands

Verify your setup with these commands:
```bash
# Test 1: Python version
python --version

# Test 2: Basic server test
python src/mcp_server/studio5000_mcp_server.py --test

# Test 3: Documentation path
dir "C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000\17691.htm"

# Test 4: SDK availability (after installing wheel file)
python -c "import logix_designer_sdk; print('SDK Available')"

# Test 5: Environment variables
echo %STUDIO5000_DOC_PATH%
echo %STUDIO5000_SDK_PATH%
```

### 📞 Getting Help

If you're still having issues:
1. **Run the test command** and capture the full output
2. **Check your Python version** and Studio 5000 installation paths  
3. **Verify all file paths exist** before reporting issues
4. **Include your exact configuration** when asking for help

### Testing the Server

For testing instructions, see **Step 4** in the [installation guide](#step-by-step-setup) above.

## Technical Details

### Architecture
The MCP server consists of four main components:

1. **Documentation Parser** (`studio5000_mcp_server.py`):
   - Parses HTML documentation files using BeautifulSoup
   - Builds an in-memory index of all instructions
   - Extracts instruction names, categories, descriptions, syntax, and parameters
   - Provides fast search and retrieval capabilities

2. **AI Code Assistant** (`ai_assistant/code_assistant.py`):
   - Natural language parsing with pattern recognition
   - Ladder logic generation for start/stop, timer, counter patterns
   - Smart tag creation with appropriate data types
   - Code validation using documentation database

3. **L5X Generator** (`code_generator/l5x_generator.py`):
   - XML-based L5X project file generation
   - Complete project structure with programs, routines, and tags
   - Studio 5000 schema compliance
   - Pretty-printed XML output

4. **Studio 5000 SDK Interface** (`sdk_interface/studio5000_sdk.py`):
   - Real .ACD project creation using official Rockwell SDK
   - Python 3.12 requirement for SDK compatibility
   - Empty project template generation
   - Direct Studio 5000 integration

### MCP Protocol
- Follows the Model Context Protocol specification for AI integration
- JSON-RPC 2.0 communication via stdin/stdout
- Tool-based architecture with 9 available tools
- Async support for all operations

## 📁 Project Structure

```
Studio5000_MCP_Server/
├── src/                                # Main source code
│   ├── mcp_server/
│   │   └── studio5000_mcp_server.py    # Main MCP server with AI features
│   ├── code_generator/
│   │   ├── l5x_generator.py            # L5X project file generation
│   │   └── templates/                  # L5X XML templates
│   ├── ai_assistant/
│   │   └── code_assistant.py           # AI-powered natural language processing
│   └── sdk_interface/
│       └── studio5000_sdk.py           # Real Studio 5000 SDK integration
├── tests/                              # Test suite and examples
├── examples/                           # Example generated projects
├── docs/                              # Additional documentation
├── requirements.txt                    # Python dependencies (Python 3.12 required)
├── mcp_config.json                    # Sample MCP configuration for Claude
├── studio5000_mcp_server.py           # Legacy server entry point (deprecated)
└── README.md                          # This comprehensive documentation
```

### Key Files
- **Main Server**: `src/mcp_server/studio5000_mcp_server.py` (use this one)
- **AI Assistant**: `src/ai_assistant/code_assistant.py` (natural language to ladder logic)
- **L5X Generator**: `src/code_generator/l5x_generator.py` (creates importable L5X files)
- **SDK Interface**: `src/sdk_interface/studio5000_sdk.py` (creates real .ACD files)
- **Configuration**: Environment variables or command line arguments

## Contributing


### Current Capabilities
- ✅ Official Studio 5000 documentation parsing (HTML)
- ✅ AI-powered natural language to ladder logic conversion
- ✅ L5X project file generation 
- ✅ Real .ACD file creation via Studio 5000 SDK
- ✅ Pattern recognition (start/stop, timer, counter, basic I/O)
- ✅ Instruction validation against official documentation
- ✅ Environment variable configuration support

### Future Enhancement Opportunities

#### **High Priority (Completed! ✅):**
- ✅ **Complete SDK Integration**: COMPLETED! Full program/task creation now implemented
- ✅ **Routine Import/Export**: COMPLETED! Using SDK's partial import functionality 
- ✅ **Program Structure Creation**: COMPLETED! Automatically creates MainProgram and MainTask
- **Tag Management**: Implement SDK tag creation and management operations (TODO)
- **Advanced Project Operations**: Build, upgrade, and deployment automation (TODO)

#### **Medium Priority (Feature Expansion):**
- **Additional Language Support**: Structured Text (ST) and Function Block Diagram (FBD) generation
- **Enhanced Pattern Recognition**: More complex industrial automation patterns  
- ✅ **SDK Documentation Improvement**: COMPLETED! Parser now finds 63 LogixProject methods + 39 examples = 102+ operations (was 22)
- **Advanced Validation**: Static analysis and best practices checking

#### **Lower Priority (Extended Integration):**
- **Multiple Studio 5000 Versions**: Dynamic version detection and compatibility
- **Integration Extensions**: Support for FactoryTalk View, RSLinx, and other Rockwell tools
- **Cloud Deployment**: Web-based interface for team collaboration
- **Caching System**: Improved performance for large documentation sets

#### **🎉 The Big Opportunity: ACHIEVED!**
The SDK implementation now provides complete project creation capabilities:
- ✅ Create programs and tasks programmatically (**COMPLETED!**)
- ✅ Import/export individual routines (**COMPLETED!**)
- 🔄 Add tags, UDTs, and Add-On Instructions (Next priority)
- 🔄 Perform complete project operations (Next priority)

**You CAN now ask**: *"Create a .ACD project with conveyor control logic"* and get a complete, ready-to-use project file! **This works today!**

### Development Setup
1. Fork the repository
2. Install Python 3.12 and dependencies
3. Set up environment variables for your Studio 5000 installation
4. Run tests to verify functionality
5. Submit pull requests with clear documentation

## License and Legal

**Important Legal Information**:
- This project is provided as-is for educational and development purposes
- **Studio 5000**, **Logix Designer**, **ControlLogix**, and **Allen-Bradley** are trademarks of **Rockwell Automation, Inc.**
- This software is not affiliated with, endorsed, or supported by Rockwell Automation
- Users must have valid Studio 5000 licenses to use the SDK features
- Generated code and projects should be validated by qualified personnel before use in production environments

**Disclaimer**: This tool assists with PLC programming but does not replace proper engineering practices, safety analysis, or compliance verification required for industrial automation systems.
