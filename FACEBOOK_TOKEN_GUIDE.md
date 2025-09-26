# 🔑 Facebook Long-Lasting Access Token Guide

## 🎯 How to Get a Long-Lasting Facebook Page Access Token

Facebook access tokens expire frequently (usually within hours or days). Here's how to get a **long-lasting token** that can last up to **60 days** or even **never expire**:

## 📋 Step-by-Step Process:

### **Step 1: Get a User Access Token**
1. Go to [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your **App** from the dropdown
3. Click **"Get Token"** → **"Get User Access Token"**
4. Select these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement` 
   - `pages_show_list`
5. Click **"Generate Access Token"**
6. **Copy this token** (this is a short-lived user token)

### **Step 2: Exchange for Long-Lived User Token**
Use this API call to get a 60-day user token:

```bash
curl -i -X GET "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_USER_TOKEN"
```

**Replace:**
- `YOUR_APP_ID` = Your Facebook App ID
- `YOUR_APP_SECRET` = Your Facebook App Secret  
- `SHORT_LIVED_USER_TOKEN` = Token from Step 1

### **Step 3: Get Your Page ID**
```bash
curl -i -X GET "https://graph.facebook.com/me/accounts?access_token=LONG_LIVED_USER_TOKEN"
```

This returns your pages with their IDs and page tokens.

### **Step 4: Get Long-Lived Page Token**
```bash
curl -i -X GET "https://graph.facebook.com/YOUR_PAGE_ID?fields=access_token&access_token=LONG_LIVED_USER_TOKEN"
```

**This page token can last indefinitely!** 🎉

## 🚀 **Quick Method Using Graph API Explorer:**

### **Alternative Easy Method:**
1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your **App**
3. Click **"Get Token"** → **"Get Page Access Token"**
4. Select your **Page**
5. The token generated here is usually **long-lasting**
6. Test it by making a call to verify it works

## 🔧 **Update Your Token:**

Once you have the long-lasting token, update it using our script:

```bash
./update_token.sh YOUR_NEW_LONG_LASTING_TOKEN
```

## 📱 **For Termux Android:**

```bash
# Make the script executable
chmod +x update_token.sh

# Update with your new token
./update_token.sh YOUR_LONG_LASTING_TOKEN

# Run automation
./run_facebook_automation.sh
```

## ⚠️ **Important Notes:**

### **Token Lifespan:**
- **User tokens**: 1-2 hours (short-lived) → 60 days (long-lived)
- **Page tokens**: Can be **permanent** if generated correctly
- **App tokens**: Never expire but have limited permissions

### **Best Practices:**
1. **Always use Page Access Tokens** for posting to pages
2. **Store tokens securely** (never commit to public repos)
3. **Test tokens regularly** to ensure they're still valid
4. **Have a backup plan** for token renewal

### **Token Validation:**
Test your token with this API call:
```bash
curl -i -X GET "https://graph.facebook.com/me?access_token=YOUR_TOKEN"
```

## 🛠️ **Troubleshooting:**

### **If Token Still Expires:**
1. Make sure you're using a **Page Access Token**, not User Token
2. Ensure your Facebook App has proper permissions
3. Check if your app is in **Development** vs **Live** mode
4. Verify the page permissions are correctly set

### **Common Issues:**
- **"Session has expired"** = Need new token
- **"Invalid access token"** = Token format wrong
- **"Insufficient permissions"** = Need to add permissions to app

## 🎯 **Pro Tip:**
The **Page Access Token** obtained through the Graph API Explorer with proper app setup can last **indefinitely** and won't require frequent renewal!

## 📞 **Need Help?**
If you're still having issues:
1. Check your Facebook App settings
2. Ensure your app has the right permissions
3. Make sure you're using the correct Page ID
4. Verify your app is approved for the required permissions

**Once you get a proper long-lasting Page Access Token, your automation will run smoothly without frequent token updates!** 🚀
