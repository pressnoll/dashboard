# Streamlit Cloud Deployment Guide

## 🚀 Quick Fix for Deployment Error

The app is showing "You do not have access to this app or it does not exist" because **Firebase credentials are missing** in Streamlit Cloud.

## ✅ Step-by-Step Solution:

### 1. **Set up Firebase Secrets in Streamlit Cloud:**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Find your deployed app (`ToksNet/NFC_Dashboard`)
3. Click on the **⚙️ Settings** (gear icon)
4. Go to **"Secrets"** tab
5. Add the following content (replace with your actual Firebase credentials):

```toml
[FIREBASE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
```

### 2. **Where to get Firebase credentials:**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** (gear icon)
4. Go to **"Service accounts"** tab
5. Click **"Generate new private key"**
6. Download the JSON file
7. Copy the content into the Streamlit secrets (format as shown above)

### 3. **Alternative: Use the JSON format directly:**

Instead of the TOML format above, you can also paste the entire JSON content like this:

```toml
FIREBASE_SERVICE_ACCOUNT = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
'''
```

### 4. **Restart the app:**

After adding the secrets:
1. Save the secrets
2. **Reboot the app** from the Streamlit Cloud interface
3. The app should now work correctly

## ⚠️ Important Security Notes:

- ✅ The `serviceAccountKey.json` was correctly **NOT** pushed to GitHub (good security practice)
- ✅ All credentials should only be in Streamlit Cloud secrets
- ❌ Never commit Firebase credentials to Git repositories

## 🎯 Expected Result:

After completing these steps, your staff attendance system should be accessible at:
`https://share.streamlit.io/app/nfcdashboard-[random-id]/`

The app will show a login page where you can:
- Login with admin/staff credentials
- Access the dashboard, reports, and staff management features
- View attendance analytics and export data

## 📞 Support:

If you still encounter issues after following these steps, the problem might be:
1. Incorrect Firebase project configuration
2. Firestore database rules
3. Missing collections in the Firebase database

Contact the developer for further assistance with specific Firebase setup questions.
