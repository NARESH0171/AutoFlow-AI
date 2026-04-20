# AutoFlow-AI
AI-powered tool that converts code and text into professional flowcharts and visual diagrams.

# AutoFlow AI

AutoFlow AI is an application that converts programming code and natural language text into structured visual diagrams such as flowcharts, circular diagrams, block diagrams, and timelines. The system focuses on simplifying complex logic into clear, readable steps.

## Overview

The project supports multiple programming languages and unstructured text input. It extracts logical steps, identifies decisions, and generates multiple diagram representations for better understanding and presentation.

## Features

- Multi-language support: Python, Java, C, C++, JavaScript
- Text-to-diagram conversion for workflow descriptions and problem statements
- Logical step extraction and decision detection
- Simplification engine to reduce complexity and improve readability
- Multiple diagram outputs for a single input
- Editable step interface before diagram generation
- Export options for generated diagrams

## How It Works

1. The user provides code or a text description.
2. The system detects the input type.
3. Language-specific patterns or text analysis are applied.
4. Logical steps and decisions are extracted.
5. Steps are simplified and structured.
6. Multiple diagram formats are generated.
7. The user selects and exports the preferred diagram.

## Architecture

- Input Layer: Accepts code or text
- Parser Layer: Language-based parsing and text analysis
- Logic Engine: Step extraction and decision mapping
- Simplification Engine: Reduces and refines steps
- Visualization Layer: Generates diagrams using graph-based rendering

## Tech Stack

Frontend:
- HTML
- CSS
- JavaScript (or React)

Backend:
- Python (Flask) or Node.js

Visualization:
- SVG rendering / Graph-based libraries

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/autoflow-ai.git
cd autoflow-ai
