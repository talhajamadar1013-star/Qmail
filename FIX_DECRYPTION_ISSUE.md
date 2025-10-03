# 🔧 Fix for "Content is encrypted - decryption key not found or invalid"

## Problem Summary

The issue was that **recipients couldn't decrypt emails** because:
1. When sending an email, only the sender got the encryption key
2. Recipients had the encrypted email but no decryption key
3. The database schema didn't support multiple users having the same key

## Solution Overview

I've implemented **key sharing** - when you send an email, the encryption key is now shared with the recipient automatically.

---

## 🚀 Step-by-Step Fix Instructions

### Step 1: Run Database Migration

**IMPORTANT**: You must run this migration before the fixes will work!

```powershell
# In your QUmail directory
python migrate_keys_table.py
```

This will:
- Update the database schema to allow key sharing
- Change PRIMARY KEY from `key_id` to `(key_id, user_id)`
- Allow recipients to have copies of encryption keys

### Step 2: Restart Your Application

```powershell
# Stop the current Flask app (Ctrl+C)
# Then restart:
python qumail_client/app.py
```

### Step 3: Test the Fix

#### A. Use the Debug Page

1. Navigate to: `http://localhost:5000/debug/keys`
2. Click **"Run Encryption Test"** - should show ✓ success
3. View **"Your Quantum Keys"** - see all available keys

#### B. Test With Your Encrypted Email

1. Go to the debug page
2. In the **"Manual Decryption Test"** section:
   - Paste encrypted content: `HApOV4vWJUT451c5j2coRD1FNFWHil9KLg02KcaGrW1O9pIQVw==`
   - Enter the Key ID (find it in the email details or database)
   - Click **"Try Decrypt"**

#### C. Send a Test Email

1. Go to **Compose**
2. Send an email to another QuMail user
3. Log in as the recipient
4. Check if they can decrypt the email

---

## 📋 What Changed

### Files Modified:

1. **`qumail_client/embedded_km/neon_key_manager.py`**
   - Added `share_key_with_recipient()` method
   - Fixed field name inconsistencies in `get_sent_emails()` and `get_received_emails()`

2. **`qumail_client/app.py`**
   - Enhanced logging in `view_email()` route
   - Improved decryption logic with multiple methods
   - Added key sharing when sending emails
   - Added debug endpoints: `/api/debug/encryption_test`, `/api/debug/list_keys`, `/api/debug/manual_decrypt`
   - Added debug page route: `/debug/keys`

3. **`qumail_client/templates/view_email.html`**
   - Better error messages
   - Shows possible causes when decryption fails

4. **`qumail_client/templates/debug_keys.html`** (NEW)
   - Complete debugging interface
   - Encryption testing tools
   - Manual decryption tester

5. **`qumail_client/templates/base.html`**
   - Added "Debug" link to navigation

6. **`migrate_keys_table.py`** (NEW)
   - Database migration script

---

## 🔍 Debugging Existing Emails

### For OLD Emails (before the fix):

If you have emails that can't be decrypted because the key was never shared:

**Option 1: Share Keys Retroactively**

Create a script to share keys for existing emails:

```python
# Run in Python console or create a script
from qumail_client.embedded_km.neon_key_manager import NeonKeyManager
from config.settings import load_config

config = load_config()
km = NeonKeyManager(config)

# Get all sent emails for a user
sent_emails = km.get_sent_emails('sender@email.com')

# Share keys with recipients
for email in sent_emails:
    km.share_key_with_recipient(
        key_id=email['key_id'],
        sender_id='sender@email.com',
        recipient_id=email['recipient']
    )
```

**Option 2: Re-send Important Emails**

For critical emails, the easiest solution is to re-send them. The new emails will have shared keys.

---

## ✅ Verification Checklist

After applying the fix:

- [ ] Database migration completed successfully
- [ ] Application restarted
- [ ] Debug page accessible at `/debug/keys`
- [ ] Encryption test passes ✓
- [ ] Can see all your keys on debug page
- [ ] New emails can be decrypted by recipients
- [ ] Logs show "Shared decryption key... with recipient"

---

## 📊 What the Logs Should Show

When viewing an email, you should now see:

```
Looking for email 123 among X sent and Y received emails
Found email 123: Test Subject
Attempting decryption - Key ID: abc123
Encrypted content length: 48
Found 5 total keys for user user@email.com
Looking for key_id: 'abc123'
Key 1: ID='abc123', Purpose=email_encryption, Expired=False
✓ Found matching key: abc123
Key data type: <class 'bytes'>, Length: 256
Trying Method 1: Base64 decode + decrypt
Decoded to 32 bytes
✓ Successfully decrypted using Method 1 (base64)
```

---

## 🐛 Still Having Issues?

If decryption still fails:

1. **Check the logs** - Look for error messages
2. **Verify key exists** - Go to `/debug/keys` and check if the key_id is listed
3. **Check key ownership** - Make sure the key is associated with your user_id
4. **Test encryption** - Run the encryption test on debug page
5. **Check encrypted format** - The content should be base64 (ends with `==`)

### Common Issues:

**"All decryption methods failed"**
- The key might be corrupted
- Wrong key is being used
- Encrypted content is in unexpected format

**"Decryption key not found"**
- Key was never shared with you
- Key was deleted
- You're logged in as wrong user

**"No encryption key ID available"**
- Email record is missing the key_id field
- Database inconsistency

---

## 📞 Need More Help?

Check the application logs in `logs/qumail.log` for detailed error messages. The enhanced logging will show exactly where the process fails.

---

## 🎉 Success!

Once working, you should:
- ✅ Be able to decrypt all NEW emails
- ✅ See detailed debug information
- ✅ Have shared keys between sender/recipient
- ✅ View encryption test success on debug page

**Remember**: This fix only applies to emails sent AFTER the migration. Old emails may need keys shared retroactively.
