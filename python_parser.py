def parse(code: str) -> list[str]:
    """Parse Python code using pattern matching instead of ast."""
    steps = []
    code = code.lower()
    
    for line in code.split("\n"):
        line = line.strip()
        if not line:
            continue
            
        if "input(" in line:
            steps.append("Take Input")
        elif "if " in line or "elif " in line:
            steps.append("Check Condition")
        elif "for " in line or "while " in line:
            steps.append("Repeat Process")
        elif "print(" in line:
            steps.append("Display Output")
        elif "=" in line and "==" not in line and "!=" not in line and "<=" not in line and ">=" not in line:
             if not line.startswith("if") and not line.startswith("for") and not line.startswith("while"):
                 steps.append("Process Data")

    return steps
