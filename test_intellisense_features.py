#!/usr/bin/env python3
"""
Test script to verify IntelliSense features
Run this in Cursor to test if IntelliSense is working
"""

# Test 1: Import suggestions
from services.question_service import QuestionService
from services.cocoindex_service import CocoIndexService
from flow.scan_flow import ScanFlow

# Test 2: Class instantiation
question_service = QuestionService()
cocoindex_service = CocoIndexService()

# Test 3: Method calls (these should show IntelliSense)
# Try typing: question_service.
# Try typing: cocoindex_service.

# Test 4: Type hints
def test_function(service: QuestionService) -> str:
    return service.ask_question("test", "test")

# Test 5: Import from services
# Try typing: from services.
# Should show: question_service, cocoindex_service, etc.

print("✅ IntelliSense test file loaded successfully!")
print("Try the following in Cursor:")
print("1. Type 'question_service.' and wait for suggestions")
print("2. Type 'from services.' and wait for suggestions")
print("3. Hover over 'QuestionService' to see documentation")
print("4. Cmd+Click on 'QuestionService' to go to definition")
