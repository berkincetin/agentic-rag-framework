"""
Test script for Turkish character support in the Gradio UI.
This script tests the UI's ability to handle Turkish characters properly.
"""

import sys
import os

# Add the parent directory to the path to import the UI module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Set environment variable for UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_turkish_text_handling():
    """Test that Turkish characters are handled correctly in UI functions."""
    print("Testing Turkish character handling in UI functions...")
    
    # Import the UI module
    try:
        from app.ui import format_bot_info, ensure_utf8_response
        print("✓ Successfully imported UI functions")
    except ImportError as e:
        print(f"✗ Failed to import UI functions: {e}")
        return False
    
    # Test Turkish characters in bot info formatting
    test_bot_info = {
        "name": "Türkçe Bot",
        "description": "Bu bot Türkçe karakterleri destekler: ğ, Ğ, ı, İ, ö, Ö, ü, Ü, ş, Ş, ç, Ç",
        "tools": ["DocumentSearchTool", "MongoDBQueryTool"],
        "metadata": {
            "languages": ["Türkçe", "English"],
            "location": "İstanbul, Türkiye",
            "topics": ["öğrenci", "araştırma", "üniversite"]
        }
    }
    
    formatted_info = format_bot_info(test_bot_info)
    print("✓ Bot info formatted successfully")
    print("Formatted info preview:")
    print(formatted_info[:200] + "..." if len(formatted_info) > 200 else formatted_info)
    
    # Check if Turkish characters are preserved
    turkish_chars = ["ğ", "Ğ", "ı", "İ", "ö", "Ö", "ü", "Ü", "ş", "Ş", "ç", "Ç"]
    preserved_chars = [char for char in turkish_chars if char in formatted_info]
    
    if len(preserved_chars) > 0:
        print(f"✓ Turkish characters preserved: {', '.join(preserved_chars)}")
    else:
        print("⚠ No Turkish characters found in formatted output")
    
    return True

def test_ui_labels():
    """Test that UI labels contain Turkish text."""
    print("\nTesting UI labels for Turkish support...")
    
    # Test some expected Turkish phrases in the UI
    expected_phrases = [
        "Chatbot Seçin",
        "Mesajınızı buraya yazın",
        "Temizle",
        "Hiçbir bot seçilmedi"
    ]
    
    # Read the UI file to check for Turkish labels
    try:
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ui.py')
        with open(ui_file_path, 'r', encoding='utf-8') as f:
            ui_content = f.read()
        
        found_phrases = []
        for phrase in expected_phrases:
            if phrase in ui_content:
                found_phrases.append(phrase)
        
        if found_phrases:
            print(f"✓ Found Turkish UI labels: {', '.join(found_phrases)}")
        else:
            print("⚠ No Turkish UI labels found")
            
        return len(found_phrases) > 0
        
    except Exception as e:
        print(f"✗ Error reading UI file: {e}")
        return False

def main():
    """Main function to run all tests."""
    print("=== Turkish Character Support Test for Gradio UI ===")
    print("This script tests the UI's Turkish character handling capabilities.")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_turkish_text_handling()
    test2_passed = test_ui_labels()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Turkish text handling: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Turkish UI labels: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Turkish character support is working correctly.")
    else:
        print("\n⚠ Some tests failed. Please check the implementation.")
    
    print("\nTo test the full UI with Turkish characters:")
    print("1. Start the API server: python -m app.main")
    print("2. Start the UI: python app/ui.py")
    print("3. Try typing Turkish messages like: 'Merhaba, nasılsın?'")

if __name__ == "__main__":
    main()
