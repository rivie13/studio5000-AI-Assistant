# 🔧 Team Troubleshooting Guide - Studio 5000 MCP Server

## 🚨 **Emergency Quick Fixes**

### **Project Won't Compile After Import**
**Symptoms:** Multiple compile errors, red X's in Studio 5000  
**Quick Fix:**
1. Copy **ALL error messages** from Studio 5000 Error List
2. Ask AI: *"Fix these Studio 5000 compilation errors: [paste all errors]"*  
3. Get corrected L5X file → Re-import → Test again

**Example Error Messages to Copy:**
```
Tag 'PKG_Data' not found in routine 'R035_PACKAGE_UPDATES'  
Invalid array reference 'UDPE[1,Index]' - Index out of bounds
Undefined instruction 'XIC' operand 'Signal_From_Camera'
```

---

### **Import Failed - "Tag Not Found"**  
**Symptoms:** Import dialog shows errors, routines not importing  
**Root Cause:** L5X references tags that don't exist in your ACD  

**Solution A - Add Missing Tags:**
```python
# Use your fix script
python fix_missing_tags.py

# Or ask AI:
"Add missing controller tags from my CSV file to this L5X routine"
```

**Solution B - Map to Existing Tags:**
```
Ask AI: "Map these missing tags to available hardware:
- Signal_From_Camera → Local:5:I.DATA.10  
- Motor_Start_Cmd → NCS1_1_VFD1:O.CMD.Start"
```

---

### **Logic Imports But Doesn't Work**
**Symptoms:** No compile errors but logic doesn't function as expected  
**Common Causes:**
- Memory tags not connected to physical I/O
- Array indexes not matching your system
- Timer/counter values not suited for your application

**Systematic Fix:**
1. **Identify disconnected tags:**
   ```
   Ask AI: "Find all memory tags in this routine that should be connected to I/O: [paste L5X]"
   ```

2. **Connect to available hardware:**
   ```  
   Ask AI: "Connect these memory tags to my available spare I/O:
   - Available spares: Local:5:I.DATA.10-15
   - VFD spares: NCS1_1_VFD1:I.IN_1, NCS1_1_VFD1:I.IN_3"
   ```

3. **Adjust timing/values:**
   ```
   Ask AI: "Adjust timer values in this routine for industrial conveyor speeds"
   ```

---

## 🐛 **Common Import/Export Issues**

### **L5X File Structure Problems** 
**Symptoms:** Import fails with XML parsing errors  

**Fix Corrupted L5X:**
```
Ask AI: "Fix the XML structure in this L5X file: [paste problematic content]"
```

**Manual Check:**
- Ensure `<?xml version="1.0"?>` header exists
- Check that all `<Tag>` elements have closing `</Tag>`
- Verify no special characters in tag names

### **Array Syntax Issues**
**Symptoms:** `UDPE[1,Index]` errors, array dimension mismatch  

**Common Fixes:**
```python
# Use existing fix script
python fix_udpe_array_syntax.py

# Or ask AI:
"Fix array syntax errors in this routine - convert to proper Studio 5000 format"
```

**Manual Pattern Fixes:**
- `UDPE[1,Index]` → `UDPE[Index,1]` (swap dimensions)
- `PKG_Data[Index].Status` → ensure `PKG_Data` array exists in controller

### **Version Compatibility**
**Symptoms:** Import works but logic appears different/corrupted  

**Check Version Mismatch:**
```
# Your L5X shows:
TargetName="R035_PACKAGE_UPDATES" SoftwareRevision="36.02"

# But your Studio 5000 is v37 or v38
```

**Fix:**
```
Ask AI: "Update this L5X file format from Studio 5000 v36 to v37 compatibility"
```

---

## 💻 **MCP Server Issues**

### **AI Doesn't Respond/Server Not Working**
**Symptoms:** AI requests hang, no response from MCP tools  

**Quick Diagnostics:**
```bash
# Test server directly
python src/mcp_server/studio5000_mcp_server.py --test

# Check Python version (MUST be 3.12)  
python --version

# Test SDK availability
python -c "import logix_designer_sdk; print('SDK OK')"
```

**Common Fixes:**
1. **Wrong Python version:**
   ```bash
   # Install Python 3.12, then update Claude config:
   "command": "C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
   ```

2. **SDK not installed:**
   ```bash
   # Install the Rockwell SDK wheel file
   pip install "C:\Users\Public\Documents\Studio 5000\Logix Designer SDK\python\logix_designer_sdk-*-py3-none-any.whl"
   ```

3. **Documentation path wrong:**
   ```bash
   # Update environment variable or command line argument
   set STUDIO5000_DOC_PATH="C:\Program Files (x86)\Rockwell Software\Studio 5000\Logix Designer\ENU\v36\Bin\Help\ENU\rs5000"
   ```

### **AI Gives Generic Responses**
**Symptoms:** AI generates logic but doesn't use your specific hardware names  

**Solution - Enable Vector Database:**
Ensure your tags CSV is in the project folder and ask:
```
"Use my tag database from MTN6_MCM06_090825_Tags.CSV to generate hardware-specific logic"
```

**Force Hardware-Specific Requests:**
❌ *"Create motor control"*  
✅ *"Create start/stop control for VFD NCS1_1_VFD1 using my existing tag database"*

---

## 📁 **File Management Problems** 

### **Can't Find Generated Files**
**Symptoms:** AI says it created files but you can't find them  

**Check These Locations:**
```bash
# Current directory
dir *.L5X

# Project folder  
dir C:\Users\YourName\OneDrive\Desktop\PROJECT_Real\*.L5X

# MCP server directory
dir C:\Users\YourName\Studio5000_MCP_Server\*.L5X
```

**Force Specific Save Location:**
```
Ask AI: "Create L5X routine and save it to C:\Users\YourName\OneDrive\Desktop\MCM_06_Real\R040_NEW_ROUTINE.L5X"
```

### **Backup Files Everywhere**
**Symptoms:** Multiple .backup files cluttering project folder  

**Cleanup Strategy:**
```bash
# Keep only the most recent backups
dir *.backup /O:D  # List by date
# Delete older backups manually, keep latest 2-3
```

**Organize Backups:**
```
📁 PROJECT_Real/
├── 📁 backups/           # Move old backups here
│   ├── 📄 *.backup
│   └── 📄 *.backup2
└── 📄 current_files.L5X  # Keep current in root
```

---

## ⚙️ **Hardware-Specific Issues**

### **VFD Tags Not Working** 
**Symptoms:** VFD doesn't respond to generated commands  

**Check Communication:**
1. **Verify VFD is online** in Studio 5000 I/O tree
2. **Check tag mapping:**
   ```
   Ask AI: "Verify these VFD tag mappings are correct for PowerFlex drives:
   - NCS1_1_VFD1:O.CMD.Start
   - NCS1_1_VFD1:I.STS.Running"
   ```

3. **Test with manual tag forcing:**
   - Force `NCS1_1_VFD1:O.CMD.Start` to TRUE
   - Check if `NCS1_1_VFD1:I.STS.Running` becomes TRUE

### **Photoeye Logic Issues**
**Symptoms:** Photoeyes not triggering properly  

**Debug Photoeye Logic:**
```
Ask AI: "Debug this photoeye logic - check for proper debouncing and edge detection:
[paste photoeye logic section]"
```

**Common Fixes:**
- Add debounce timers for mechanical bounce
- Use ONS (One Shot) for edge detection  
- Check wiring: NO vs NC configuration

### **Encoder/Position Tracking Problems**
**Symptoms:** Package tracking loses position, wrong destinations  

**Systematic Debug:**
```
Ask AI: "Review this encoder-based tracking logic for common issues:
[paste tracking routine]

Check for:
- Encoder scaling factors  
- Position reset conditions
- Array boundary violations"
```

---

## 🔍 **Advanced Debugging Techniques**

### **Logic Flow Analysis**
**When logic is complex and hard to follow:**

```
Ask AI: "Trace the execution path through this routine step by step:
[paste complex logic]

Explain what happens when:
1. Package enters at induct PE  
2. Camera signal triggers
3. Divert decision is made"
```

### **Tag Cross-Reference**  
**Finding all uses of a problematic tag:**

```
Ask AI: "Find all references to tag 'Signal_From_Camera' in this project and suggest alternatives"
```

### **Performance Analysis**
**Routine taking too long to execute:**

```
Ask AI: "Optimize this routine for faster scan time - identify bottlenecks:
[paste routine]"
```

---

## 👥 **Team Collaboration Issues**

### **Different Team Members Getting Different Results**
**Symptoms:** Same AI request produces different logic for different users  

**Standardize Approach:**
1. **Use same project folder structure**
2. **Share the same CSV tag export**  
3. **Use specific hardware names in requests**
4. **Include context:** *"For the MCM_06 project using our standard VFD naming"*

### **Version Control Conflicts** 
**Symptoms:** Git merge conflicts on L5X files  

**L5X-Friendly Git Practices:**
```bash
# Use .gitignore for backup files
*.backup*
*.bak*

# Commit both original and AI-modified versions
git add original_routine.L5X
git add ai_modified_routine.L5X
git commit -m "AI: Added camera detection logic to R035"
```

**Merge Conflict Resolution:**
```
Ask AI: "Merge these two L5X routine versions while preserving both sets of changes:
[paste version 1]
---
[paste version 2]"
```

---

## 📞 **Escalation Guidelines**

### **When to Ask for Help:**

**Level 1 - Try AI First:**
- Compilation errors  
- Import/export issues
- Logic not working as expected
- Tag mapping problems

**Level 2 - Ask Experienced Team Member:**
- AI consistently gives wrong answers
- Complex multi-routine integration issues
- Hardware communication problems
- Safety logic validation

**Level 3 - Senior Engineer/Lead:**
- Production system failures
- Safety system modifications  
- Major project restructuring
- Tool setup and configuration issues

### **Information to Provide When Asking for Help:**

**Always Include:**
- ✅ **Exact error messages** (copy/paste from Studio 5000)  
- ✅ **What you were trying to achieve** (*"trying to add camera logic to R035"*)
- ✅ **What AI request you used** (*"asked AI to connect Signal_From_Camera to Local:5:I.DATA.10"*)
- ✅ **Files involved** (routine names, L5X files)
- ✅ **What you've already tried** (*"ran fix_camera_signal.py, still getting errors"*)

**Example Good Help Request:**
```
Problem: R035 routine won't compile after AI modification

Error Messages:
- Tag 'PKG_Data' not found  
- Invalid array reference UDPE[1,Index]

AI Request Used:
"Add camera detection logic using Local:5:I.DATA.10 for Signal_From_Camera"

Files Involved:  
- R035_PACKAGE_UPDATES_Routine_RLL.L5X
- MTN6_MCM06_090825_Tags.CSV

Already Tried:
- Ran fix_missing_tags.py  
- Re-exported tags CSV
- Asked AI to fix compilation errors (got same results)

Project: MCM_06 sorter system
```

---

**🎯 Remember: Most issues are fixable by asking the AI for help with specific error messages. When in doubt, copy the exact error and ask the AI to explain and fix it!**
