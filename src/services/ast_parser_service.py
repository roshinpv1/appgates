"""
AST parser service for code analysis
"""

import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️ Tree-sitter not available, using regex-based parsing")

try:
    import ast as python_ast
    PYTHON_AST_AVAILABLE = True
except ImportError:
    PYTHON_AST_AVAILABLE = False

from models.scan_models import Symbol, ImportInfo


class ASTParserService:
    """AST parser service for code analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AST parser service"""
        self.config = config
        self.supported_languages = config.get("supported_languages", [
            "python", "javascript", "typescript", "java", "csharp", "go", "rust"
        ])
        
        # Initialize tree-sitter if available
        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()
        else:
            self.parsers = {}
            print("⚠️ Using regex-based parsing (tree-sitter not available)")
        
        # Language-specific patterns
        self.language_patterns = self._init_language_patterns()
        
        print(f"🔍 ASTParserService initialized with {len(self.supported_languages)} supported languages")
    
    def _init_tree_sitter(self):
        """Initialize tree-sitter parsers"""
        self.parsers = {}
        
        # Try to load tree-sitter languages
        try:
            # Python
            if "python" in self.supported_languages:
                self.parsers["python"] = self._create_parser("python")
            
            # JavaScript/TypeScript
            if "javascript" in self.supported_languages:
                self.parsers["javascript"] = self._create_parser("javascript")
            
            if "typescript" in self.supported_languages:
                self.parsers["typescript"] = self._create_parser("typescript")
            
            # Java
            if "java" in self.supported_languages:
                self.parsers["java"] = self._create_parser("java")
            
            # C/C++
            if "c" in self.supported_languages:
                self.parsers["c"] = self._create_parser("c")
            
            if "cpp" in self.supported_languages:
                self.parsers["cpp"] = self._create_parser("cpp")
            
            # Go
            if "go" in self.supported_languages:
                self.parsers["go"] = self._create_parser("go")
            
            # Rust
            if "rust" in self.supported_languages:
                self.parsers["rust"] = self._create_parser("rust")
            
        except Exception as e:
            print(f"⚠️ Tree-sitter initialization failed: {e}")
            self.parsers = {}
    
    def _create_parser(self, language: str) -> Optional[Parser]:
        """Create parser for specific language"""
        try:
            parser = Parser()
            # Note: In a real implementation, you'd need to install language grammars
            # For now, we'll return None to fall back to regex parsing
            return None
        except Exception as e:
            print(f"⚠️ Failed to create parser for {language}: {e}")
            return None
    
    def _init_language_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize language-specific regex patterns"""
        return {
            "python": {
                "function": r"def\s+(\w+)\s*\(",
                "class": r"class\s+(\w+)",
                "import": r"import\s+([^\n]+)",
                "from_import": r"from\s+([^\s]+)\s+import\s+([^\n]+)",
                "method": r"def\s+(\w+)\s*\(",
                "variable": r"(\w+)\s*=",
            },
            "javascript": {
                "function": r"function\s+(\w+)\s*\(",
                "class": r"class\s+(\w+)",
                "import": r"import\s+([^;]+);",
                "const": r"const\s+(\w+)",
                "let": r"let\s+(\w+)",
                "var": r"var\s+(\w+)",
            },
            "typescript": {
                "function": r"function\s+(\w+)\s*\(",
                "class": r"class\s+(\w+)",
                "interface": r"interface\s+(\w+)",
                "import": r"import\s+([^;]+);",
                "const": r"const\s+(\w+)",
                "let": r"let\s+(\w+)",
            },
            "java": {
                "function": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:[\w<>\[\]]+\s+)?(\w+)\s*\(",
                "class": r"class\s+(\w+)",
                "import": r"import\s+([^;]+);",
                "method": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:[\w<>\[\]]+\s+)?(\w+)\s*\(",
                "variable": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:[\w<>\[\]]+\s+)?(\w+)\s+(\w+)\s*;",
            },
            "go": {
                "function": r"func\s+(\w+)\s*\(",
                "struct": r"type\s+(\w+)\s+struct",
                "import": r"import\s+(?:\(([^)]+)\)|['\"]([^'\"]+)['\"])",
                "method": r"func\s*\(\s*\w+\s+\w+\s*\)\s+(\w+)\s*\(",
                "variable": r"(\w+)\s*:=",
            },
            "rust": {
                "function": r"fn\s+(\w+)\s*\(",
                "struct": r"struct\s+(\w+)",
                "use": r"use\s+([^;]+);",
                "method": r"fn\s+(\w+)\s*\(",
                "variable": r"let\s+(\w+)",
            }
        }
    
    def parse_file(self, content: str, language: str) -> Dict[str, Any]:
        """Parse file content and extract AST information"""
        try:
            # Try tree-sitter first
            if TREE_SITTER_AVAILABLE and language in self.parsers:
                return self._parse_with_tree_sitter(content, language)
            else:
                # Fallback to regex-based parsing
                return self._parse_with_regex(content, language)
                
        except Exception as e:
            print(f"⚠️ Failed to parse {language} file: {e}")
            # Return basic structure
            return {
                "language": language,
                "symbols": [],
                "imports": [],
                "exports": [],
                "error": str(e)
            }
    
    def _parse_with_tree_sitter(self, content: str, language: str) -> Dict[str, Any]:
        """Parse using tree-sitter"""
        try:
            if language not in self.parsers or self.parsers[language] is None:
                return self._parse_with_regex(content, language)
            
            parser = self.parsers[language]
            tree = parser.parse(bytes(content, 'utf8'))
            root_node = tree.root_node
            
            # Extract symbols from the AST
            symbols = []
            imports = []
            
            # Walk through the AST and extract information
            self._extract_from_node(root_node, symbols, imports, language)
            
            return {
                "language": language,
                "symbols": symbols,
                "imports": imports,
                "exports": [],  # Would need language-specific logic
                "ast": str(root_node)  # For debugging
            }
            
        except Exception as e:
            print(f"⚠️ Tree-sitter parsing failed for {language}: {e}")
            # Fall back to regex parsing
            return self._parse_with_regex(content, language)
    
    def _extract_from_node(self, node, symbols, imports, language):
        """Recursively extract symbols and imports from AST nodes"""
        try:
            # Extract based on node type
            if node.type == "function_definition" or node.type == "function_declaration":
                # Extract function name
                for child in node.children:
                    if child.type in ["identifier", "name"]:
                        symbols.append(Symbol(
                            name=child.text.decode('utf8'),
                            kind="function",
                            start_line=child.start_point[0] + 1,
                            end_line=child.end_point[0] + 1,
                            start_column=child.start_point[1],
                            end_column=child.end_point[1],
                            signature=node.text.decode('utf8')[:100]  # First 100 chars
                        ))
                        break
            
            elif node.type == "class_definition" or node.type == "class_declaration":
                # Extract class name
                for child in node.children:
                    if child.type in ["identifier", "name"]:
                        symbols.append(Symbol(
                            name=child.text.decode('utf8'),
                            kind="class",
                            start_line=child.start_point[0] + 1,
                            end_line=child.end_point[0] + 1,
                            start_column=child.start_point[1],
                            end_column=child.end_point[1],
                            signature=node.text.decode('utf8')[:100]
                        ))
                        break
            
            elif node.type == "import_statement" or node.type == "import":
                # Extract import information
                import_text = node.text.decode('utf8')
                imports.append(ImportInfo(
                    module=import_text,
                    line=node.start_point[0] + 1,
                    type="import"
                ))
            
            # Recursively process children
            for child in node.children:
                self._extract_from_node(child, symbols, imports, language)
                
        except Exception as e:
            print(f"⚠️ Error extracting from node: {e}")
    
    def _parse_with_regex(self, content: str, language: str) -> Dict[str, Any]:
        """Parse using regex patterns"""
        try:
            symbols = []
            imports = []
            
            if language not in self.language_patterns:
                return {
                    "language": language,
                    "symbols": [],
                    "imports": [],
                    "exports": []
                }
            
            patterns = self.language_patterns[language]
            lines = content.split('\n')
            
            # Extract functions
            if "function" in patterns:
                for i, line in enumerate(lines):
                    matches = re.finditer(patterns["function"], line)
                    for match in matches:
                        symbols.append(Symbol(
                            name=match.group(1),
                            kind="function",
                            start_line=i + 1,
                            end_line=i + 1,
                            start_column=match.start(),
                            end_column=match.end(),
                            signature=line.strip()
                        ))
            
            # Extract classes
            if "class" in patterns:
                for i, line in enumerate(lines):
                    matches = re.finditer(patterns["class"], line)
                    for match in matches:
                        symbols.append(Symbol(
                            name=match.group(1),
                            kind="class",
                            start_line=i + 1,
                            end_line=i + 1,
                            start_column=match.start(),
                            end_column=match.end(),
                            signature=line.strip()
                        ))
            
            # Extract imports
            if "import" in patterns:
                for i, line in enumerate(lines):
                    matches = re.finditer(patterns["import"], line)
                    for match in matches:
                        imports.append(ImportInfo(
                            module=match.group(1),
                            line=i + 1,
                            type="import"
                        ))
            
            return {
                "language": language,
                "symbols": [s.__dict__ for s in symbols],
                "imports": [i.__dict__ for i in imports],
                "exports": []
            }
            
        except Exception as e:
            print(f"⚠️ Regex parsing failed for {language}: {e}")
            return {
                "language": language,
                "symbols": [],
                "imports": [],
                "exports": [],
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check AST parser service health"""
        try:
            # Test with simple code
            test_code = """
def hello_world():
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
"""
            
            result = self.parse_file(test_code, "python")
            
            return {
                "status": "healthy",
                "supported_languages": self.supported_languages,
                "tree_sitter_available": TREE_SITTER_AVAILABLE,
                "python_ast_available": PYTHON_AST_AVAILABLE,
                "test_parse_symbols": len(result.get("symbols", [])),
                "test_parse_imports": len(result.get("imports", []))
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "supported_languages": self.supported_languages,
                "tree_sitter_available": TREE_SITTER_AVAILABLE,
                "python_ast_available": PYTHON_AST_AVAILABLE
            }
