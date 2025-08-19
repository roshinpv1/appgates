#!/usr/bin/env python3
"""
Installation script for PDF generation support in CodeGates
This installs ReportLab library for generating individual gate PDFs for JIRA upload
"""

import subprocess
import sys
import os

def install_reportlab():
    """Install ReportLab library for PDF generation"""
    print("🔧 Installing ReportLab for PDF generation support...")
    print("=" * 50)
    
    try:
        # Install ReportLab
        print("📦 Installing reportlab...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "reportlab"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ReportLab installed successfully!")
        else:
            print(f"❌ Failed to install ReportLab:")
            print(result.stderr)
            return False
        
        # Test import
        print("\n🧪 Testing PDF generation...")
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate
            print("✅ ReportLab import test successful!")
        except ImportError as e:
            print(f"❌ ReportLab import test failed: {e}")
            return False
        
        # Test PDF generation
        try:
            from gates.pdf_generator import CodeGatesPDFGenerator
            generator = CodeGatesPDFGenerator()
            print("✅ CodeGates PDF generator ready!")
        except ImportError as e:
            print(f"⚠️ CodeGates PDF generator not ready: {e}")
            print("💡 Make sure you're running this from the project root directory")
        
        print("\n🎉 PDF generation support installed successfully!")
        print("\n📋 What you can do now:")
        print("   • Generate individual PDF documents for each gate")
        print("   • Upload gate PDFs to JIRA tickets")
        print("   • Organize PDFs by status (FAIL, WARNING, PASS)")
        print("   • Create summary PDFs for overall scan reports")
        
        print("\n🚀 Usage:")
        print("   • Via API: GET /api/v1/scan/{scan_id}/pdfs")
        print("   • Via UI: Use the PDF generation section in scan results")
        print("   • Via CLI: python gates/pdf_generator.py <scan_id>")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def check_existing_installation():
    """Check if ReportLab is already installed"""
    try:
        import reportlab
        print("✅ ReportLab is already installed!")
        print(f"   Version: {reportlab.__version__}")
        return True
    except ImportError:
        print("⚠️ ReportLab not found - installation needed")
        return False

def main():
    """Main installation function"""
    print("📄 CodeGates PDF Generation Setup")
    print("=" * 40)
    
    # Check if already installed
    if check_existing_installation():
        response = input("\nReportLab is already installed. Reinstall? (y/N): ")
        if response.lower() != 'y':
            print("🔧 Testing existing installation...")
            try:
                from gates.pdf_generator import CodeGatesPDFGenerator
                generator = CodeGatesPDFGenerator()
                print("✅ PDF generation is ready to use!")
                return
            except Exception as e:
                print(f"⚠️ Issue with existing installation: {e}")
                print("🔧 Proceeding with reinstallation...")
    
    # Install ReportLab
    success = install_reportlab()
    
    if success:
        print("\n✅ Installation complete!")
        print("\n💡 Next steps:")
        print("   1. Restart your CodeGates server")
        print("   2. Run a scan to generate results")
        print("   3. Use the PDF generation features in the UI")
        print("   4. Download individual gate PDFs for JIRA upload")
    else:
        print("\n❌ Installation failed!")
        print("\n🔧 Manual installation:")
        print("   pip install reportlab")

if __name__ == "__main__":
    main() 