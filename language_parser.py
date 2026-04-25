import python_parser
import java_parser
import c_parser
import cpp_parser
import js_parser

def extract_steps(code: str, language: str) -> list[str]:
    """Route code to the specific Language Parser Module for logic extraction."""
    lang = language.lower()
    
    if lang == "java":
        return java_parser.parse(code)
    elif lang == "c":
        return c_parser.parse(code)
    elif lang == "c++" or lang == "cpp":
        return cpp_parser.parse(code)
    elif lang == "javascript" or lang == "js":
        return js_parser.parse(code)
    elif lang == "python":
        return python_parser.parse(code)
    
    # Fallback to python
    return python_parser.parse(code)
