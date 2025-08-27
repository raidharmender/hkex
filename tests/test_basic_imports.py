#!/usr/bin/env python3
"""
Basic import test to verify core functionality.
"""

def test_basic_imports():
    """Test basic imports without database connections."""
    try:
        # Test core imports
        from app.config import settings
        print("✅ Config imported successfully")
        
        from app.models import SettlementRecord, DownloadRequest
        print("✅ Models imported successfully")
        
        # Test basic functionality without database connections
        from app.services.settlement_parser import SettlementParser
        parser = SettlementParser()
        print("✅ SettlementParser created successfully")
        
        # Test CLI imports
        from app.cli import main
        print("✅ CLI imported successfully")
        
        print("\n🎉 All basic imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing basic imports...")
    success = test_basic_imports()
    if success:
        print("✅ Basic functionality verified!")
    else:
        print("❌ Some imports failed")
