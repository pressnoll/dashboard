# Staff Attendance Dashboard

A professional Streamlit dashboard for staff attendance and punctuality analytics, integrated with Firebase Firestore.

## Features
- Secure sign-in/sign-up (admin/staff) with hashed passwords
- Attendance check-in/check-out
- Actionable analytics: total check-ins, average check-in time, earliest/latest check-in
- Flexible reporting: custom date range, staff selection, CSV export
- Admin staff management (add/remove)

## Setup
1. Clone this repo:
   ```
   git clone <your-repo-url>
   cd staff-attendance-system
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Add your Firebase credentials:
   - For local: place `serviceAccountkey.json` in the project root (do NOT commit to GitHub)
   - For Streamlit Cloud: add credentials to Streamlit secrets (`.streamlit/secrets.toml`)

## Deployment (Streamlit Cloud)
- Push to GitHub
- On Streamlit Cloud, set up secrets for Firebase
- App will run from `app.py`

## Security
- Passwords are hashed before storing in Firestore
- No hardcoded credentials
- Only admins can register new users

## Usage
- Login or sign up as admin/staff
- Use dashboard, reports, and staff management features

---
For questions or support, contact the project maintainer.
