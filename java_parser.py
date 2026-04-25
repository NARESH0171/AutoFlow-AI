def parse(code: str) -> list[str]:
    """Parse Java code and extract logical steps."""
    steps = []
    code = code.lower()
    
    for line in code.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        if "scanner" in line or "system.in" in line:
            steps.append("Take Input")
        elif "if(" in line or "if (" in line or "switch(" in line:
            steps.append("Check Condition")
        elif "for(" in line or "for (" in line or "while(" in line or "while (" in line:
            steps.append("Repeat Process")
        elif "system.out.print" in line:
            steps.append("Display Output")
        elif "=" in line and "==" not in line and "!=" not in line and "<=" not in line and ">=" not in line:
             if "==" not in line and not line.startswith("if") and not line.startswith("for") and not line.startswith("while"):
                 steps.append("Process Data")

    return steps
