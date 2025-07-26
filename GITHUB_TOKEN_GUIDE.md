# How to Find Personal Access Tokens on GitHub - Step by Step

This guide shows you exactly where to find and create Personal Access Tokens on GitHub.

## 🔍 Step-by-Step Navigation

### Step 1: Go to GitHub.com
1. Open your web browser
2. Go to **https://github.com**
3. **Sign in** to your GitHub account

### Step 2: Access Your Profile Settings
1. **Click your profile picture** in the top-right corner of GitHub
2. **Click "Settings"** from the dropdown menu

### Step 3: Find Developer Settings
1. **Scroll down** on the left sidebar
2. Look for **"Developer settings"** (it's near the bottom)
3. **Click "Developer settings"**

### Step 4: Access Personal Access Tokens
1. In the left sidebar under "Developer settings"
2. **Click "Personal access tokens"**
3. **Click "Tokens (classic)"**

### Step 5: Generate New Token
1. **Click "Generate new token"**
2. **Click "Generate new token (classic)"**

## 📍 Alternative Navigation Path

If you can't find the settings, here's the direct URL:

```
https://github.com/settings/tokens
```

Just replace `YOUR_USERNAME` with your actual GitHub username.

## 🔧 Detailed Steps with Screenshots

### Step 1: Profile Picture
- Look at the **top-right corner** of GitHub
- You'll see your **profile picture/avatar**
- **Click on it**

### Step 2: Settings Menu
- A dropdown menu will appear
- **Click "Settings"** (it's usually the first option)

### Step 3: Left Sidebar Navigation
- On the left side of the page, you'll see a menu
- **Scroll down** to find "Developer settings"
- It's usually near the bottom of the sidebar

### Step 4: Developer Settings
- **Click "Developer settings"**
- This will open a submenu

### Step 5: Personal Access Tokens
- In the submenu, **click "Personal access tokens"**
- Then **click "Tokens (classic)"**

### Step 6: Generate Token
- You'll see a page with your existing tokens (if any)
- **Click "Generate new token"**
- **Click "Generate new token (classic)"**

## 🎯 What You Should See

After clicking "Generate new token (classic)", you'll see a form with:

### Token Settings:
- **Note**: Enter `VPS Deployment`
- **Expiration**: Choose 90 days (recommended)
- **Scopes**: Check these boxes:
  - ✅ `repo` (Full control of private repositories)
  - ✅ `workflow` (if using GitHub Actions)

### Important:
- **Click "Generate token"** at the bottom
- **Copy the token immediately** (you won't see it again!)

## 🔗 Direct Links (Replace YOUR_USERNAME)

### Method 1: Direct Token Page
```
https://github.com/settings/tokens
```

### Method 2: Full Navigation Path
```
https://github.com/settings/developer
```

## 🆘 If You Still Can't Find It

### Check 1: Are you logged in?
- Make sure you're signed in to GitHub
- You should see your profile picture in the top-right

### Check 2: Do you have the right permissions?
- Personal Access Tokens are available to all GitHub users
- You don't need any special permissions

### Check 3: Try the direct URL
- Go directly to: `https://github.com/settings/tokens`
- This should take you straight to the tokens page

### Check 4: Look for "Developer settings"
- In the left sidebar, scroll down
- Look for "Developer settings" (it's usually at the bottom)
- It might be collapsed, so make sure to scroll

## 📱 Mobile vs Desktop

### Desktop (Recommended):
- Use a computer/laptop
- The navigation is easier to see
- All options are visible in the sidebar

### Mobile:
- The menu might be hidden
- Try rotating to landscape mode
- Or use the direct URL: `https://github.com/settings/tokens`

## 🔍 Visual Cues to Look For

### Profile Picture:
- Usually a circular image in the top-right
- Might be your photo or a default GitHub avatar

### Settings Icon:
- Sometimes there's a gear icon (⚙️) next to your profile picture
- Click that instead of the profile picture

### Developer Settings:
- Usually has a small icon (like a code symbol)
- Located near the bottom of the left sidebar

## ✅ Success Indicators

You're in the right place when you see:

1. **Page title**: "Personal access tokens"
2. **Button**: "Generate new token (classic)"
3. **List**: Your existing tokens (if any)
4. **URL**: Contains `/settings/tokens`

## 🚀 After Creating the Token

Once you have your token:

1. **Copy it** (you won't see it again!)
2. **Go back to your VPS**
3. **Use the token as your "password"** when connecting to GitHub

### Example:
```bash
# On your VPS
git clone https://github.com/YOUR_USERNAME/exportco.git

# When prompted:
# Username: indrapurnayasa
# Password: your-personal-access-token (NOT your GitHub password!)
```

## 🆘 Still Having Trouble?

If you still can't find it:

1. **Try the direct URL**: `https://github.com/settings/tokens`
2. **Check if you're logged in** to the right GitHub account
3. **Try a different browser**
4. **Clear your browser cache**
5. **Contact GitHub support** if needed

---

**The Personal Access Token is essential for connecting your VPS to GitHub. Once you find it, the rest of the deployment process will be much easier! 🚀** 