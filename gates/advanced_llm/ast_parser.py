"""
AST Parser Component
Parses code into AST for intelligent chunking and symbol extraction
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

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


@dataclass
class Symbol:
    """Code symbol information"""
    name: str
    kind: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    signature: Optional[str] = None
    references: Optional[List[str]] = None
    imports: Optional[List[str]] = None


@dataclass
class ImportInfo:
    """Import information"""
    module: str
    line: int
    name: Optional[str] = None
    alias: Optional[str] = None
    type: str = "import"  # import, from_import


class ASTParser:
    """
    AST parser with tree-sitter integration and fallback to regex parsing
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AST parser"""
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
        
        print(f"🔍 ASTParser initialized with {len(self.supported_languages)} supported languages")
    
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
            print(f"⚠️ Failed to initialize tree-sitter parsers: {e}")
            self.parsers = {}
    
    def _create_parser(self, language: str):
        """Create a tree-sitter parser for a language"""
        try:
            # Set the language based on the language name
            if language == "python":
                import tree_sitter_python
                parser = Parser()
                parser.set_language(tree_sitter_python.language)
                return parser
            elif language == "javascript":
                import tree_sitter_javascript
                parser = Parser()
                parser.set_language(tree_sitter_javascript.language)
                return parser
            elif language == "java":
                import tree_sitter_java
                parser = Parser()
                parser.set_language(tree_sitter_java.language)
                return parser
            elif language == "c":
                import tree_sitter_c
                parser = Parser()
                parser.set_language(tree_sitter_c.language)
                return parser
            elif language == "cpp":
                import tree_sitter_cpp
                parser = Parser()
                parser.set_language(tree_sitter_cpp.language)
                return parser
            elif language == "go":
                import tree_sitter_go
                parser = Parser()
                parser.set_language(tree_sitter_go.language)
                return parser
            elif language == "rust":
                import tree_sitter_rust
                parser = Parser()
                parser.set_language(tree_sitter_rust.language)
                return parser
            else:
                print(f"⚠️ No tree-sitter grammar available for {language}")
                return None
                
        except Exception as e:
            print(f"⚠️ Failed to create parser for {language}: {e}")
            return None
    
    def _init_language_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize regex patterns for different languages"""
        return {
            "python": {
                "function": r"def\s+(\w+)\s*\([^)]*\)\s*:",
                "class": r"class\s+(\w+)(?:\s*\([^)]*\))?\s*:",
                "import": r"(?:from\s+(\w+(?:\.\w+)*)\s+import\s+(\w+)|import\s+(\w+(?:\.\w+)*))",
                "method": r"def\s+(\w+)\s*\([^)]*\)\s*:",
                "variable": r"(\w+)\s*=",
            },
            "javascript": {
                "function": r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(|let\s+(\w+)\s*=\s*(?:async\s*)?\(|var\s+(\w+)\s*=\s*(?:async\s*)?\()",
                "class": r"class\s+(\w+)",
                "import": r"(?:import\s+(?:\{([^}]+)\}\s+from\s+)?['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"])",
                "method": r"(\w+)\s*\([^)]*\)\s*\{",
                "variable": r"(?:const|let|var)\s+(\w+)",
            },
            "typescript": {
                "function": r"(?:function\s+(\w+)|const\s+(\w+)\s*:\s*\w*\s*=\s*(?:async\s*)?\(|let\s+(\w+)\s*:\s*\w*\s*=\s*(?:async\s*)?\()",
                "class": r"class\s+(\w+)",
                "import": r"(?:import\s+(?:\{([^}]+)\}\s+from\s+)?['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"])",
                "method": r"(\w+)\s*\([^)]*\)\s*\{",
                "variable": r"(?:const|let|var)\s+(\w+)",
            },
            "java": {
                "function": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*\(",
                "class": r"(?:public\s+)?class\s+(\w+)",
                "import": r"import\s+([^;]+);",
                "method": r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*\(",
                "variable": r"(?:final\s+)?\w+\s+(\w+)\s*=",
            },
            "csharp": {
                "function": r"(?:public|private|protected|internal)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(",
                "class": r"(?:public\s+)?class\s+(\w+)",
                "using": r"using\s+([^;]+);",
                "method": r"(?:public|private|protected|internal)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(",
                "variable": r"\w+\s+(\w+)\s*=",
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
        """
        Parse file content and extract AST information
        """
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
        """
        Parse using tree-sitter
        """
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
                            signature=node.text.decode('utf8')[:100]  # First 100 chars
                        ))
                        break
            
            elif node.type in ["import_statement", "import_declaration"]:
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
            # Continue processing other nodes even if one fails
            pass
    
    def _parse_with_regex(self, content: str, language: str) -> Dict[str, Any]:
        """
        Parse using regex patterns
        """
        lines = content.split('\n')
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
        
        # Extract symbols
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Extract functions
            if "function" in patterns:
                matches = re.findall(patterns["function"], line)
                for match in matches:
                    if isinstance(match, tuple):
                        name = next((m for m in match if m), None)
                    else:
                        name = match
                    if name:
                        symbols.append(Symbol(
                            name=name,
                            kind="function",
                            start_line=line_num,
                            end_line=line_num,
                            start_column=line.find(name),
                            end_column=line.find(name) + len(name),
                            signature=line.strip()
                        ))
            
            # Extract classes
            if "class" in patterns:
                matches = re.findall(patterns["class"], line)
                for match in matches:
                    if isinstance(match, tuple):
                        name = next((m for m in match if m), None)
                    else:
                        name = match
                    if name:
                        symbols.append(Symbol(
                            name=name,
                            kind="class",
                            start_line=line_num,
                            end_line=line_num,
                            start_column=line.find(name),
                            end_column=line.find(name) + len(name),
                            signature=line.strip()
                        ))
            
            # Extract methods
            if "method" in patterns:
                matches = re.findall(patterns["method"], line)
                for match in matches:
                    if isinstance(match, tuple):
                        name = next((m for m in match if m), None)
                    else:
                        name = match
                    if name:
                        symbols.append(Symbol(
                            name=name,
                            kind="method",
                            start_line=line_num,
                            end_line=line_num,
                            start_column=line.find(name),
                            end_column=line.find(name) + len(name),
                            signature=line.strip()
                        ))
            
            # Extract imports
            if "import" in patterns:
                matches = re.findall(patterns["import"], line)
                for match in matches:
                    if isinstance(match, tuple):
                        module = next((m for m in match if m), None)
                    else:
                        module = match
                    if module:
                        imports.append(ImportInfo(
                            module=module,
                            line=line_num,
                            type="import"
                        ))
            
            # Language-specific import patterns
            if language == "csharp" and "using" in patterns:
                matches = re.findall(patterns["using"], line)
                for match in matches:
                    imports.append(ImportInfo(
                        module=match,
                        line=line_num,
                        type="using"
                    ))
            
            if language == "rust" and "use" in patterns:
                matches = re.findall(patterns["use"], line)
                for match in matches:
                    imports.append(ImportInfo(
                        module=match,
                        line=line_num,
                        type="use"
                    ))
        
        return {
            "language": language,
            "symbols": [self._symbol_to_dict(s) for s in symbols],
            "imports": [self._import_to_dict(i) for i in imports],
            "exports": [],  # Would be extracted in full implementation
            "total_lines": len(lines),
            "total_symbols": len(symbols)
        }
    
    def _symbol_to_dict(self, symbol: Symbol) -> Dict[str, Any]:
        """Convert Symbol to dictionary"""
        return {
            "name": symbol.name,
            "kind": symbol.kind,
            "start_line": symbol.start_line,
            "end_line": symbol.end_line,
            "start_column": symbol.start_column,
            "end_column": symbol.end_column,
            "signature": symbol.signature,
            "references": symbol.references or [],
            "imports": symbol.imports or []
        }
    
    def _import_to_dict(self, import_info: ImportInfo) -> Dict[str, Any]:
        """Convert ImportInfo to dictionary"""
        return {
            "module": import_info.module,
            "name": import_info.name,
            "alias": import_info.alias,
            "line": import_info.line,
            "type": import_info.type
        }
    
    def extract_symbols(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract symbols from AST"""
        return ast.get("symbols", [])
    
    def extract_imports(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract imports from AST"""
        return ast.get("imports", [])
    
    def extract_exports(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract exports from AST"""
        return ast.get("exports", [])
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.supported_languages
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for AST parser"""
        try:
            # Simple health check without actual parsing
            return {
                "status": "healthy",
                "supported_languages": self.supported_languages,
                "tree_sitter_available": TREE_SITTER_AVAILABLE,
                "test_symbols_found": 0
            }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
