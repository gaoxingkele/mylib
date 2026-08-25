"""Reference Workbench Skill — environment check (cross-platform)."""
import sys
import importlib.util

def main():
    print("=== Reference Workbench setup ===")

    # Python check
    ver = sys.version_info
    print(f"Python: {ver.major}.{ver.minor}.{ver.micro}")
    if ver < (3, 10):
        print("ERROR: Python 3.10+ required")
        sys.exit(1)

    # Rich check
    if importlib.util.find_spec("rich"):
        print("rich:   installed")
    else:
        print("MISSING: pip install rich")

    # MCP check
    print("MCP:    Claude will verify arxiv/scholar/paper-search/pdf-reader/crossref")

    print("Setup complete.")

if __name__ == "__main__":
    main()
