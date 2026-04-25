def parse(code: str) -> list[str]:
    """Parse JavaScript code and extract logical steps."""
    steps = []
    code = code.lower()
    
    for line in code.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        if "prompt(" in line or "readline(" in line or "document.getelement" in line:
            steps.append("Take Input")
        elif "if(" in line or "if (" in line or "switch(" in line:
            steps.append("Check Condition")
        elif "for(" in line or "for (" in line or "while(" in line or "while (" in line:
            steps.append("Repeat Process")
        elif "console.log" in line or "alert(" in line or "document.write" in line or "innerhtml" in line:
            steps.append("Display Output")
        elif "=" in line and "==" not in line and "===" not in line and "!==" not in line:
             if "==" not in line and not line.startswith("if") and not line.startswith("for") and not line.startswith("while"):
                 steps.append("Process Data")

    return steps
