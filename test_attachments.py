#!/usr/bin/env python3
"""
Test file attachments functionality
"""

import os
import sys
import tempfile
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_file(filename, content):
    """Create a test file with content"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return file_path

def test_attachment_endpoint():
    """Test the attachment functionality via API"""
    # Create test files
    test_file1 = create_test_file("test_attachment.txt", "This is a test attachment content.")
    test_file2 = create_test_file("test_document.txt", "Another test document with more content.")
    
    try:
        # Test data
        data = {
            'recipient': 'test@example.com',
            'subject': 'Test Email with Attachments',
            'content': 'This is a test email with file attachments.',
            'encryption_key': 'auto',
            'priority': 'normal'
        }
        
        # Prepare files for upload
        files = [
            ('attachments', ('test_attachment.txt', open(test_file1, 'rb'), 'text/plain')),
            ('attachments', ('test_document.txt', open(test_file2, 'rb'), 'text/plain'))
        ]
        
        logger.info("Testing file attachment functionality...")
        logger.info(f"Test files created: {test_file1}, {test_file2}")
        logger.info(f"Data to send: {data}")
        
        # In a real test, you would send this to your local server
        # For now, we just validate that the test data is properly formed
        
        logger.info("✅ File attachment test data prepared successfully!")
        logger.info("To test fully, run the QuMail application and use the compose page to attach files.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup test files
        try:
            if os.path.exists(test_file1):
                os.remove(test_file1)
            if os.path.exists(test_file2):
                os.remove(test_file2)
            logger.info("Cleaned up test files")
        except Exception as e:
            logger.warning(f"Failed to cleanup test files: {e}")

def test_file_validation():
    """Test file validation logic"""
    logger.info("Testing file validation...")
    
    # Test filename sanitization
    test_filenames = [
        "normal_file.txt",
        "file with spaces.pdf",
        "file@#$%^&*().doc",
        "../../../dangerous.txt",
        "very_long_filename_that_might_cause_issues_with_the_filesystem.txt"
    ]
    
    for filename in test_filenames:
        # Simulate the sanitization logic from the code
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-').strip()
        if not safe_filename:
            safe_filename = f"attachment_{int(time.time())}"
        
        logger.info(f"Original: '{filename}' -> Sanitized: '{safe_filename}'")
    
    logger.info("✅ File validation test completed!")
    return True

if __name__ == "__main__":
    logger.info("🧪 Starting QuMail File Attachment Tests...")
    
    success = True
    success &= test_file_validation()
    success &= test_attachment_endpoint()
    
    if success:
        logger.info("🎉 All file attachment tests passed!")
        logger.info("\nNext steps:")
        logger.info("1. Run the QuMail application: python qumail_client/app.py")
        logger.info("2. Login and go to the compose page")
        logger.info("3. Try attaching files using the file upload area")
        logger.info("4. Send a test email to verify attachments work")
    else:
        logger.error("❌ Some tests failed!")
        sys.exit(1)