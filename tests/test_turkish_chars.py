"""
Test script for Turkish character handling in the Agentic RAG API.
This script tests both sending and receiving Turkish characters.
"""

import requests
import json
import sys

# Set up UTF-8 encoding for console output
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# API URL
API_URL = "http://localhost:8000"


def test_turkish_query():
    """Test querying the API with Turkish characters."""
    print("Testing Turkish character handling in API queries...")

    # Turkish test queries with special characters
    test_queries = [
        "Merhaba, nasılsın?",  # Basic greeting with ı
        # "Öğrenci kayıt işlemleri nasıl yapılır?",  # Contains ö, ğ, ı
        # "Şu anda çalışan dersler hangileri?",  # Contains ş, ç
        # "İstanbul'daki üniversiteler",  # Contains İ, ü
        # "Güz döneminde açılan dersler nelerdir?",  # Contains ü, ç, ı
    ]

    # Test each query
    for query in test_queries:
        print(f"\nTesting query: {query}")

        try:
            # Prepare the request
            payload = {"query": query, "session_id": "test-turkish-chars"}

            # Make the request with proper content type
            response = requests.post(
                f"{API_URL}/bots/StudentBot/query",
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
            )

            # Check the response
            if response.status_code == 200:
                # Print the response with proper encoding
                response_json = response.json()
                print("Response received successfully!")
                print(f"Original query: {response_json.get('query', 'N/A')}")
                print(f"Response: {response_json.get('response', 'N/A')[:100]}...")

                # Verify Turkish characters in the response
                original_query = response_json.get("query", "")
                if original_query == query:
                    print("✓ Query preserved Turkish characters correctly")
                else:
                    print("✗ Query did not preserve Turkish characters")
                    print(f"  Original: {query}")
                    print(f"  Received: {original_query}")
            else:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response: {response.text}")

        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the API server. Make sure it's running.")
            return False
        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    return True


def main():
    """Main function to run the tests."""
    print("=== Turkish Character Handling Test ===")
    print("This script tests the API's ability to handle Turkish characters.")
    print("Make sure the API server is running before executing this test.")
    print("API URL:", API_URL)
    print("=" * 40)

    # Run the tests
    success = test_turkish_query()

    if success:
        print("\nAll tests completed. Check the results above for any issues.")
    else:
        print("\nTests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
