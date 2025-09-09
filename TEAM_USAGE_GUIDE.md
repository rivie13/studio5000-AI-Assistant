# 🛠️ Studio 5000 MCP Server - Team Usage Guide

## 📋 **Quick Start for New Team Members**

### What This Tool Does
Our Studio 5000 MCP Server transforms PLC programming by allowing you to:
- 🧠 Convert natural language requests into working ladder logic
- 📁 Generate complete L5X routine files for import into Studio 5000
- 🔍 Search official Studio 5000 documentation instantly
- ✅ Validate ladder logic using real Studio 5000 compilation
- 🏗️ Create complete .ACD project files using official Rockwell SDK

---

## 🏭 **Real-World Team Workflow** 
*Based on actual industrial practice*

### **Step 1: Set Up Your Project Folder Structure** 📁

Create a dedicated folder for each project following this proven structure:

```
📁 PROJECT_NAME_Real/
├── 📄 PROJECT_NAME.ACD                    # Your main Studio 5000 project
├── 📄 PROJECT_NAME_Tags.CSV               # Exported tags from Studio 5000
├── 📄 R010_ROUTINE_NAME_RLL.L5X          # Individual routine exports
├── 📄 R020_ANOTHER_ROUTINE_RLL.L5X       # More routine exports  
├── 📁 fix_scripts/                       # Your custom Python fix scripts
├── 📄 project_documentation.pdf          # Technical specs, drawings
├── 📄 camera_signal_solutions.md         # Your analysis notes
└── 📄 *.backup files                     # Automatic backups
```

**Real Example Structure** (from MCM_06_Real):
- `MTN6_MCM06_090825.ACD` - Main project file
- `MTN6_MCM06_090825_Tags.CSV` - Tag database export
- `R035_PACKAGE_UPDATES_Routine_RLL.L5X` - Individual routine
- `fix_camera_signal.py` - Custom fix script
- `Amazon NonCon and Intralox S7000 Sorter Functional Document_R5.pdf` - Project docs

---

## 🔄 **The Complete Team Workflow**

### **Phase 1: Project Setup and Export** 📤

#### **1.1 Export Your ACD File**

# Place your main .ACD file in the project folder
📁 Project_Folder/
└── 📄 YourProject.ACD
You can just drag and drop your .ACD file into the project folder.

#### **1.2 Export Individual Routines**
In Studio 5000:
1. **Right-click** on each routine you're working on
2. **Export** → **L5X File**
3. **Save** to your project folder with naming convention:
   - `R010_ROUTINE_NAME_RLL.L5X`
   - `R020_ANOTHER_ROUTINE_RLL.L5X`

#### **1.3 Export Tag Database**
1. **Go to** Logic → Tags
2. **File** → **Export**
3. **Save as** `ProjectName_Tags.CSV` in project folder

---

### **Phase 1.5 Routine Indexing**
Ask the AI to index the exported L5X files:
It should create a vector database of the exported L5X files. Allowing for semantic search of the exported L5X files.


This is especially useful for large projects with many routines where the routines themselves are also large and complex.

### **Phase 2: AI-Powered Development** 🤖

#### **2.1 Create Analysis Documentation**
Document your findings in markdown files:

```markdown
# Problem Analysis
- Current issue with camera signal connection
- Need to map Signal_From_Camera to actual I/O
- Available spare inputs: Local:5:I.DATA.10-15
```

#### **2.2 Use MCP Tools with Natural Language**

**Example AI Requests:**
- *"Fix the camera signal connection in my sorter routine"*
- *"Create ladder logic for conveyor jam detection using upstream/downstream photoeyes"*
- *"Add a 5-second delay timer before activating the divert"*
- *"Generate error handling logic for VFD communication loss"*

**The AI will:**
✅ Generate working ladder logic  
✅ Create proper tag structures  
✅ Validate against Studio 5000 documentation  
✅ Provide complete L5X files ready for import  

---

### **Phase 3: Automated Fix Scripts** 🔧

Create Python scripts for common fixes (like your examples):
This is optional, but sometimes the AI will generate code that is not correct and you will need to fix it. The AI can generate these scripts for you. It can use sdk and regular docs documentation to help it fix the code.

Examples:

#### **3.1 Camera Signal Fix Script** 
```python
# fix_camera_signal.py
def fix_camera_connection(l5x_file, spare_input="Local:5:I.DATA.10"):
    """Connect Signal_From_Camera to actual I/O"""
    # Replace XIC(Signal_From_Camera) with XIC(Local:5:I.DATA.10)
    # Add backup creation
    # Validate changes
```

#### **3.2 Missing Tags Fix Script**
```python  
# fix_missing_tags.py
def add_missing_tags(l5x_file, csv_tags_file):
    """Add controller tags from CSV to L5X routine"""
    # Read tags from CSV export
    # Generate proper XML tag definitions
    # Insert into L5X Tags section
```

#### **3.3 Array Syntax Fix Script**
```python
# fix_udpe_array_syntax.py  
def fix_array_references(l5x_file):
    """Fix UDPE array syntax issues"""
    # Correct array indexing
    # Fix dimension references
    # Validate syntax
```

---

### **Phase 4: Import and Test** 🔄

#### **4.1 Import Updated Routines**
1. **Open** Studio 5000 with your main .ACD file
2. **Go to** File → Import
3. **Select** your updated L5X routine files

#### **4.2 Validation Process**
1. **Compile** the project in Studio 5000 (happens automatically when you import the L5X files)
    - if there are errors, you will need to fix them you can copy and paste the error messages to the AI to fix them.
2. **Check** for errors in the Error List
3. **If errors exist:**
   - Use the validate feature in studio 5000 to get more detailed error messages
   - Copy error messages
   - Feed back to AI: *"Fix these Studio 5000 errors: [paste errors]"*
   - Get corrected L5X files  
   - Re-import and test again

#### **4.3 Verify Logic**
- **Cross-reference** logic with I/O
- **Test** individual rungs if possible
- **Verify** tag addresses match physical hardware

---

### **Phase 5: Vector Database Integration** 🗄️ 
*(New Feature - Gives AI Access to Real Devices)*

#### **5.1 Create Tag Vector Database**
Ask the AI to create a vector database of the tag database. This is especially useful for large projects with many tags.

#### **5.2 Benefits of Vector Database:**
- ✅ AI knows your **actual device names** (NCS1_1_VFD1, Local:5:I.DATA.10)
- ✅ Understands your **existing tag structure** 
- ✅ Generates logic that **matches your hardware**
- ✅ Reduces import errors by using **real tag references**

---

## 🛠️ **Daily Usage Examples**

### **Common AI Requests:**

#### **Motor Control:**
*"Create start/stop logic for conveyor motor with VFD NCS1_1_VFD1"*

#### **Sensor Integration:** 
*"Add photoeye logic for package detection using available spare input Local:5:I.DATA.12"*

#### **Timer Logic:**
*"Create a 30-second timeout for divert operation with alarm"*  

#### **Error Handling:**
*"Add fault detection for encoder communication loss with automatic retry"*

#### **Array Operations:**
*"Fix the UDPE array indexing errors in my package tracking routine"*

#### **Documentation Search:**
*"What are the parameters for the PID instruction?"*
*"Show me all Motion Control instructions available"*

---

## ⚡ **Quick Reference Commands**

### **Project Creation:**
```
Ask AI: "Create complete L5X project for [description]"
Result: Full Studio 5000 project ready for import
```

### **Logic Generation:**
```  
Ask AI: "Generate ladder logic for [description]"
Result: Working ladder logic with proper tags
```

### **Routine Fixes:**
```
Ask AI: "Fix this routine: [paste L5X content or error messages]" 
Result: Corrected L5X file ready for import
```

### **Documentation:**
```
Ask AI: "How do I use [instruction name]?"
Result: Complete syntax and examples
```

### **Validation:**
```
Ask AI: "Validate this logic: [paste ladder logic]"
Result: Error checking and suggestions
```

---

## 🚨 **Common Issues & Solutions**

### **Import Errors**
**Problem:** "Tag not found" errors after import  
**Solution:** Use fix_missing_tags.py (you can generate this script) script or ask AI: *"Add missing tags from my CSV file to this routine"*

### **Array Syntax Issues**
**Problem:** UDPE[1,Index] syntax errors  
**Solution:** Use fix_udpe_array_syntax.py or ask AI: *"Fix array syntax in my routine"*

### **I/O Connection Issues**
**Problem:** Memory tags not connected to physical I/O  
**Solution:** Ask AI: *"Connect [tag_name] to available spare input [input_address]"*

### **Compilation Errors**
**Problem:** Logic doesn't compile in Studio 5000  
**Solution:** Copy error messages and ask AI: *"Fix these Studio 5000 compilation errors: [paste errors]"*

---

## 📝 **Best Practices for Teams**

### **File Organization:**
- ✅ **Always** create backups before making changes  
- ✅ **Use** consistent naming conventions (R010_, R020_)
- ✅ **Keep** project documentation in the same folder
- ✅ **Export** tags regularly as projects evolve

### **AI Interaction:**
- ✅ **Be specific** in requests (*"conveyor with jam detection"* vs *"conveyor logic"*)
- ✅ **Include context** (*"using VFD NCS1_1_VFD1"* vs *"using a VFD"*)
- ✅ **Paste actual errors** when asking for fixes
- ✅ **Validate** generated logic before deploying to production

### **Version Control:**
- ✅ **Git** works well for L5X files and Python scripts
- ✅ **Commit** both original and AI-generated versions
- ✅ **Tag** versions before major changes
- ✅ **Document** what AI tools were used in commit messages

### **Team Collaboration:**
- ✅ **Share** successful fix scripts with team
- ✅ **Document** common AI requests in project notes  
- ✅ **Create** team templates for common patterns
- ✅ **Review** AI-generated logic with senior team members

---

## 🎯 **Advanced Features**

### **SDK Integration:**
- Creates real .ACD project files using official Rockwell SDK
- Generates complete projects with MainProgram, MainTask, and logic (work in progress, only empty projects are reliable)
- Professional-grade output that opens directly in Studio 5000

### **Documentation Database:**
- Access to complete Studio 5000 instruction documentation
- Real-time validation against official Rockwell specifications
- Search by category, function, or natural language

### **Pattern Recognition:**
- Automatically detects start/stop, timer, counter patterns
- Intelligent tag naming based on function
- Smart error handling and safety logic integration

---

## 🚀 **Getting Started Checklist**

### **For New Team Members:**

- [ ] **Install** Python 3.12 and MCP server following README
- [ ] **Create** your first project folder with proper structure  
- [ ] **Export** one routine from existing Studio 5000 project
- [ ] **Ask AI** to make a simple improvement to the routine
- [ ] **Import** the result back into Studio 5000 and verify it works
- [ ] **Practice** with fix scripts on non-critical routines
- [ ] **Share** your results with the team

### **For Project Leads:**

- [ ] **Set up** team folder structure standards
- [ ] **Create** common fix script templates  
- [ ] **Document** project-specific AI request patterns
- [ ] **Establish** code review process for AI-generated logic
- [ ] **Train** team members on workflow best practices

---

## 📞 **Support & Resources**

### **When You Need Help:**
1. **Check** this guide first for common solutions
2. **Try** asking the AI to explain what it's doing  
3. **Paste** actual error messages when asking for fixes
4. **Ask** experienced team members about workflow
5. **Review** working examples in team project folders

### **Advanced Learning:**
- Study the working fix scripts in project folders
- Experiment with different AI request phrasings  
- Learn to read and modify L5X files manually
- Practice with the documentation search features

---

**Remember:** This tool accelerates your PLC programming but doesn't replace engineering judgment. Always validate AI-generated logic for your specific application and safety requirements.

🎉 **Happy Programming!**
