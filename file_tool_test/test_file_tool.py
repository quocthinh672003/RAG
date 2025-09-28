"""Test file tool - main test script."""

import asyncio
import tempfile
from pathlib import Path

from app.agent.tools.file.dto import FileToolInput
from app.agent.tools.file.wiring import create_file_tool


async def test_file_tool():
    """Test file tool - main test script."""
    print("🚀 Testing File Tool...")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file tool using wiring
        file_tool = create_file_tool(Path(temp_dir))

        # Test PDF
        print("\n📄 Testing PDF creation...")
        pdf_input = FileToolInput(
            format="pdf",
            content="This is a test PDF document.\nIt contains multiple lines.\nThis is the third line.",
            title="Test PDF Document",
            data=[
                {"name": "John Doe", "age": 30, "city": "New York"},
                {"name": "Jane Smith", "age": 25, "city": "Los Angeles"},
            ],
        )

        try:
            pdf_result = await file_tool(pdf_input)
            print(f"✅ PDF: {pdf_result.filename} | {pdf_result.size_bytes} bytes")
            print(f"   Path: {pdf_result.file_path}")
        except Exception as e:
            print(f"❌ PDF failed: {e}")

        # Test Excel
        print("\n📊 Testing Excel creation...")
        excel_input = FileToolInput(
            format="excel",
            content="Sales data export",
            data=[
                {"product": "Widget A", "sales": 1000, "region": "North"},
                {"product": "Widget B", "sales": 1500, "region": "South"},
                {"product": "Widget C", "sales": 800, "region": "East"},
            ],
        )

        try:
            excel_result = await file_tool(excel_input)
            print(
                f"✅ Excel: {excel_result.filename} | {excel_result.size_bytes} bytes"
            )
            print(f"   Path: {excel_result.file_path}")
        except Exception as e:
            print(f"❌ Excel failed: {e}")

        # Test Word
        print("\n📝 Testing Word creation...")
        word_input = FileToolInput(
            format="word",
            content="This is the main content of the Word document.",
            title="Company Report",
            data=[
                {"employee": "John Doe", "department": "Engineering", "salary": 75000},
                {"employee": "Jane Smith", "department": "Marketing", "salary": 65000},
            ],
        )

        try:
            word_result = await file_tool(word_input)
            print(f"✅ Word: {word_result.filename} | {word_result.size_bytes} bytes")
            print(f"   Path: {word_result.file_path}")
        except Exception as e:
            print(f"❌ Word failed: {e}")

        print("\n🎉 All tests completed!")

        # Show file structure
        print("\n📁 Generated files:")
        for file_path in Path(temp_dir).rglob("*"):
            if file_path.is_file():
                print(f"   {file_path.relative_to(Path(temp_dir))}")


if __name__ == "__main__":
    asyncio.run(test_file_tool())
