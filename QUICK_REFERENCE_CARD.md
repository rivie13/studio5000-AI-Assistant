# 🚀 Studio 5000 MCP Server - Quick Reference Card

## **Daily Commands - Copy & Paste Ready**

### **🧠 AI Code Generation**
```
"Create ladder logic for [description]"
"Generate conveyor control with jam detection using photoeyes"
"Add 5-second delay timer for solenoid valve"
"Create start/stop logic for motor with VFD [VFD_name]"
```

### **📁 Project Creation** 
```
"Create complete L5X project for [project description]"
"Generate L5X routine for [routine description]"
"Create .ACD project template for [controller type]"
```

### **🔧 Fix Common Issues**
```
"Fix these Studio 5000 errors: [paste error messages]"
"Connect [tag_name] to spare input [input_address]"
"Fix missing tags in this routine: [paste L5X content]"
"Fix array syntax errors in my package tracking"
```

### **📚 Documentation Lookup**
```
"What are the parameters for [instruction_name]?"
"Show me all [category] instructions"
"How do I use GSV instruction?"
"What's the difference between TON and TOF timers?"
```

### **✅ Validation**
```
"Validate this logic: [paste ladder logic]"
"Check this routine for errors: [paste L5X file]"
```

---

## **📁 Project Folder Setup**

### **Required Structure:**
```
📁 PROJECT_NAME_Real/
├── 📄 PROJECT.ACD                 # Main project
├── 📄 PROJECT_Tags.CSV            # Tag export  
├── 📄 R###_ROUTINE_RLL.L5X        # Routine exports
├── 📄 fix_*.py                    # Fix scripts
├── 📄 *.pdf                       # Documentation
└── 📄 *.backup                    # Auto backups
```

---

## **🔄 Workflow Steps**

### **1. Export (Studio 5000 → Folder)**
- Export routines: Right-click → Export → L5X
- Export tags: Logic → Tags → File → Export → CSV

### **2. AI Processing (Use MCP)**  
- Ask AI to improve/fix/create logic
- Get L5X files ready for import

### **3. Import (Folder → Studio 5000)**
- File → Import → Select L5X files
- Choose: Routines ✅, Tags ✅ (selective)

### **4. Validate & Fix**
- Compile project, check errors
- If errors: paste back to AI for fixes
- Repeat until clean compile

---

## **⚡ Speed Tips**

### **For Motor Control:**
- *"Create start/stop logic for [motor_name] using [VFD_tag]"*
- Always specify your actual VFD tag names

### **For Sensors:**  
- *"Add photoeye logic using spare input [input_address]"*
- Check your available spare I/O first

### **For Timing:**
- *"Add [X]-second timer for [operation] with [conditions]"*  
- Be specific about timer trigger conditions

### **For Arrays:**
- *"Fix UDPE array indexing in my tracking routine"*
- AI knows common PLC array syntax issues

### **For Troubleshooting:**
- Always paste **actual error messages**
- Include **context**: "In routine R035, when importing..."
- Be **specific** about what's not working

---

## **🚨 Emergency Fixes**

### **Won't Compile:**
```
Copy all error messages → Ask AI:
"Fix these Studio 5000 compilation errors: [paste errors]"
```

### **Import Failed:**
```  
"Fix import errors in this L5X file: [paste file content]"
"Add missing controller tags from CSV to this routine"
```

### **Tag Not Found:**
```
"Map these memory tags to available spare I/O: [list tags]"
"Add missing tag definitions for: [list missing tags]"  
```

### **Array Syntax:**
```
"Fix array syntax errors in this routine: [paste problematic section]"
```

---

## **📋 File Naming Conventions**

### **Routines:**
- `R010_DESCRIPTION_RLL.L5X`  
- `R020_DESCRIPTION_RLL.L5X`
- `R035_PACKAGE_UPDATES_RLL.L5X`

### **Backups:**
- `filename.L5X.backup`
- `filename.L5X.backup_tags`  
- `filename.L5X.backup_structure`

### **Fix Scripts:**
- `fix_camera_signal.py`
- `fix_missing_tags.py`
- `fix_array_syntax.py`

---

## **🎯 Best Results Tips**

### **Be Specific:**
❌ *"Fix my conveyor"*  
✅ *"Fix conveyor jam detection using upstream PE Local:4:I.DATA.15 and downstream PE Local:4:I.DATA.16"*

### **Use Your Hardware:**
❌ *"Add VFD control"*  
✅ *"Add start/stop control for VFD NCS1_1_VFD1"*

### **Include Context:**
❌ *"Timer not working"*  
✅ *"TON timer in R035 routine line 47 not triggering - here's the logic: [paste]"*

### **Paste Real Data:**
❌ *"I have errors"*  
✅ *"Studio 5000 compilation errors: Tag 'PKG_Data' not found in routine R035"*

---

---

## **🔍 Vector Database Features**  
*(AI knows your real hardware)*

- AI uses **your actual VFD names** (NCS1_1_VFD1)  
- Knows **your spare I/O** (Local:5:I.DATA.10-15)
- References **your existing tags** from CSV export
- Generates **hardware-specific** logic

---

## **📞 When Stuck**

### **Quick Checks:**
1. ✅ Did you export the routine first?
2. ✅ Is the folder structure correct?  
3. ✅ Are you pasting actual error messages?
4. ✅ Did you try asking AI to explain the issue?

### **Advanced Help:**
1. Ask AI: *"Explain what this error means: [paste error]"*
2. Ask AI: *"What's wrong with this logic: [paste code]"*  
3. Check team folder for similar working examples
4. Try breaking complex requests into smaller steps

---

**🎯 Remember: Be specific, use real hardware names, and always validate before production!**
