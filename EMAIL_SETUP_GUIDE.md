# 📧 Email Digest Setup Guide

## Problem Identified
Your email digests aren't being sent because **SendGrid API key is not configured**.

## Quick Fix (5 minutes)

### Step 1: Create `.env` File

Create a file named `.env` in the `backend` folder with this content:

```env
# SendGrid Email Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
FROM_EMAIL=your_verified_email@domain.com

# Scheduler Settings
ENABLE_SCHEDULER=1
DIGEST_GENERATION_TIME=00:00

# Add your other API keys here (OpenAI, etc.)
```

### Step 2: Verify Sender Email in SendGrid

**IMPORTANT:** You must verify your sender email in SendGrid:

1. Go to https://app.sendgrid.com/
2. Navigate to **Settings** → **Sender Authentication**
3. Click **Verify a Single Sender**
4. Add and verify: `ramnathan.au@gmail.com`
5. Check your Gmail for verification email

**Without sender verification, SendGrid will reject all emails!**

### Step 3: Restart Backend Server

After creating the `.env` file:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd backend
python main.py
```

Or if using uvicorn:
```bash
uvicorn main:app --reload
```

### Step 4: Test Email Sending

Two ways to test:

#### Option A: Use the Test Page (Easiest)
1. Open http://localhost:8000/test-email.html in your browser
2. Login if prompted
3. Click "Send Test Email"
4. Check your inbox (and spam folder!)

#### Option B: Use API Directly
```bash
# Get your auth token from localStorage after login
# Then:
curl -X POST http://localhost:8000/api/test-email \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Verify Setup

Run the diagnostic script to confirm everything is configured:

```bash
cd backend
python diagnose_email.py
```

You should see:
- ✓ SendGrid API key is set
- ✓ Email notifications: ENABLED
- ✓ Primary location: Gowanbrae, Melbourne

## Troubleshooting

### Problem: "Failed to send email"
**Solution:** Check SendGrid sender verification status

### Problem: "Still not receiving emails"
**Solutions:**
1. Check spam/junk folder
2. Verify `FROM_EMAIL` matches verified sender in SendGrid
3. Check SendGrid activity log at https://app.sendgrid.com/email_activity
4. Ensure `ENABLE_SCHEDULER=1` in `.env`

### Problem: "Emails sent but nothing in inbox"
**Solution:** 
1. Check SendGrid Activity Feed for delivery status
2. Look for bounces or blocks
3. Your Gmail might be blocking emails - add to contacts

## Scheduled Digest Times

Your current settings:
- **Notification time:** 07:00 AM
- **Timezone:** Australia/Melbourne
- **Scheduler runs:** Every hour (UTC)

The system will automatically send digests at your preferred time each day.

## Testing Scheduled Digests

To test without waiting:

1. Go to http://localhost:8000/test-email.html
2. Click "Generate & Send Digest Now"
3. This will create a digest and email it immediately

## Current Status

Based on diagnostic:
- ✅ You have 19 historical digests generated
- ❌ 0 emails sent (SendGrid not configured)
- ✅ Email notifications enabled
- ✅ Location set: Gowanbrae, Melbourne

Once you complete the setup above, future digests will be emailed automatically!

## Need Help?

Check logs at:
- Backend console output
- SendGrid Activity Feed: https://app.sendgrid.com/email_activity

Common SendGrid errors:
- **403 Forbidden:** API key invalid or sender not verified
- **400 Bad Request:** Email format issue
- **Check your spam folder first!**

