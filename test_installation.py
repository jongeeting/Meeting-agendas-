#!/usr/bin/env python3
"""
Test script to validate the installation and basic functionality.
"""

import sys


def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")

    try:
        import requests
        print("✓ requests")
    except ImportError:
        print("✗ requests - run: pip install requests")
        return False

    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4")
    except ImportError:
        print("✗ beautifulsoup4 - run: pip install beautifulsoup4")
        return False

    try:
        from PyPDF2 import PdfReader
        print("✓ PyPDF2")
    except ImportError:
        print("✗ PyPDF2 - run: pip install PyPDF2")
        return False

    try:
        from anthropic import Anthropic
        print("✓ anthropic")
    except ImportError:
        print("✗ anthropic - run: pip install anthropic")
        return False

    return True


def test_script_syntax():
    """Test that the main script has valid syntax."""
    print("\nTesting script syntax...")

    try:
        import pcpc_agenda_tracker
        print("✓ pcpc_agenda_tracker.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in pcpc_agenda_tracker.py: {e}")
        return False
    except Exception as e:
        # Other exceptions are okay at this point (e.g., missing API key)
        print(f"✓ pcpc_agenda_tracker.py syntax is valid (runtime check: {type(e).__name__})")
        return True


def test_api_key():
    """Test if API key is configured."""
    print("\nTesting API key configuration...")

    import os
    from pathlib import Path

    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
        with open(env_file) as f:
            if "ANTHROPIC_API_KEY" in f.read():
                print("✓ ANTHROPIC_API_KEY found in .env")
    else:
        print("⚠ .env file not found")

    # Check environment variable
    if os.getenv("ANTHROPIC_API_KEY"):
        print("✓ ANTHROPIC_API_KEY environment variable is set")
        return True
    else:
        print("⚠ ANTHROPIC_API_KEY environment variable not set")
        print("  Set it with: export ANTHROPIC_API_KEY='your_key_here'")
        print("  Or create a .env file with: ANTHROPIC_API_KEY=your_key_here")
        return False


def test_website_access():
    """Test if we can access the PCPC website."""
    print("\nTesting website access...")

    try:
        import requests
        url = "https://www.phila.gov/departments/philadelphia-city-planning-commission/public-meetings/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"✓ Can access PCPC website ({response.status_code})")

            # Check if we can find agenda PDFs
            if "PCPC-Agenda.pdf" in response.text or "pcpc-agenda.pdf" in response.text.lower():
                print("✓ Found agenda PDF references on page")
                return True
            else:
                print("⚠ No agenda PDFs found (page structure may have changed)")
                return True
        else:
            print(f"⚠ Website returned status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ Error accessing website: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("PCPC Agenda Tracker - Installation Test")
    print("=" * 60)
    print()

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Script Syntax", test_script_syntax()))
    results.append(("API Key", test_api_key()))
    results.append(("Website Access", test_website_access()))

    print()
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")

    print()

    if all(result[1] for result in results):
        print("✓ All tests passed! You're ready to run the tracker.")
        print()
        print("Next steps:")
        print("1. Make sure your ANTHROPIC_API_KEY is set")
        print("2. Run: python pcpc_agenda_tracker.py")
        return 0
    else:
        print("⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
