# How to Connect VPS to GitHub Repository

This guide shows you how to connect your VPS (101.50.2.59) to your GitHub repository using username and password/token.

## 🔑 Method 1: Personal Access Token (Recommended)

### Step 1: Create Personal Access Token on GitHub

1. **Go to GitHub.com** and sign in to your account
2. **Click your profile picture** → **Settings**
3. **Scroll down** → **Developer settings** (left sidebar)
4. **Click "Personal access tokens"** → **Tokens (classic)**
5. **Click "Generate new token"** → **Generate new token (classic)**
6. **Fill in the details:**
   - **Note**: `VPS Deployment`
   - **Expiration**: Choose (90 days recommended)
   - **Scopes**: Select these:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (if using GitHub Actions)
7. **Click "Generate token"**
8. **Copy the token** (you won't see it again!)

### Step 2: Connect VPS to GitHub

```bash
# SSH to your VPS
ssh root@101.50.2.59

# Configure Git with your GitHub credentials
git config --global user.name "Your GitHub Username"
git config --global user.email "your-email@example.com"

# Store credentials (this will ask for username and password/token)
git config --global credential.helper store

# Test the connection by cloning a repository
git clone https://github.com/YOUR_USERNAME/hackathon-service.git /tmp/test-clone

# When prompted:
# Username: your-github-username
# Password: your-personal-access-token (not your GitHub password!)

# If successful, remove test clone
rm -rf /tmp/test-clone
```

### Step 3: Alternative - Store Credentials Directly

```bash
# Create credentials file
echo "https://YOUR_USERNAME:YOUR_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Configure Git to use stored credentials
git config --global credential.helper store

# Test connection
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

## 🔑 Method 2: Username and Password (Deprecated)

**Note**: GitHub no longer accepts regular passwords for Git operations. You must use a Personal Access Token.

### If you try to use regular password:
```bash
git clone https://github.com/YOUR_USERNAME/hackathon-service.git
# Username: your-github-username
# Password: your-github-password  # This will FAIL!
```

**Error**: `remote: Support for password authentication was removed on August 13, 2021. Please use a personal access token instead.`

## 🔑 Method 3: SSH Keys (Alternative)

### Step 1: Generate SSH Key on VPS

```bash
# SSH to your VPS
ssh root@101.50.2.59

# Generate SSH key
ssh-keygen -t rsa -b 4096 -C "vps@101.50.2.59"
# Press Enter for all prompts (use default settings)

# Display the public key
cat ~/.ssh/id_rsa.pub
```

### Step 2: Add SSH Key to GitHub

1. **Copy the public key** from the previous command
2. **Go to GitHub.com** → **Settings** → **SSH and GPG keys**
3. **Click "New SSH key"**
4. **Fill in:**
   - **Title**: `VPS 101.50.2.59`
   - **Key**: Paste the public key
5. **Click "Add SSH key"**

### Step 3: Test SSH Connection

```bash
# Test the connection
ssh -T git@github.com

# You should see: "Hi username! You've successfully authenticated..."
```

## 🚀 Quick Setup Script

I've created a script to automate this process:

```bash
# Upload the script to your VPS
scp github-setup.sh root@101.50.2.59:/root/

# SSH to VPS and run the script
ssh root@101.50.2.59
chmod +x github-setup.sh
./github-setup.sh

# Choose option 1 (Personal Access Token)
# Enter your GitHub username and token
```

## 🔧 Manual Setup Commands

### For Personal Access Token:

```bash
# SSH to VPS
ssh root@101.50.2.59

# Configure Git
git config --global user.name "Your GitHub Username"
git config --global user.email "your-email@example.com"

# Store credentials
echo "https://YOUR_USERNAME:YOUR_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
git config --global credential.helper store

# Test connection
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### For SSH Keys:

```bash
# SSH to VPS
ssh root@101.50.2.59

# Generate SSH key
ssh-keygen -t rsa -b 4096 -C "vps@101.50.2.59"

# Display public key
cat ~/.ssh/id_rsa.pub

# Test connection
ssh -T git@github.com
```

## ✅ Test Your Connection

### Test with Personal Access Token:
```bash
# Test API access
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Test repository access
git clone https://github.com/YOUR_USERNAME/hackathon-service.git /tmp/test
rm -rf /tmp/test
```

### Test with SSH:
```bash
# Test SSH connection
ssh -T git@github.com

# Test repository access
git clone git@github.com:YOUR_USERNAME/hackathon-service.git /tmp/test
rm -rf /tmp/test
```

## 🆘 Troubleshooting

### Common Issues:

#### 1. "Support for password authentication was removed"
**Solution**: Use Personal Access Token instead of password

#### 2. "Permission denied (publickey)"
**Solution**: 
- Check if SSH key is added to GitHub
- Test SSH connection: `ssh -T git@github.com`

#### 3. "Repository not found"
**Solution**:
- Check repository name and username
- Verify you have access to the repository
- Check if repository is private and you have proper permissions

#### 4. "Authentication failed"
**Solution**:
- Verify your Personal Access Token is correct
- Check token expiration date
- Ensure token has proper scopes (repo, workflow)

## 📋 Quick Reference

### Personal Access Token Setup:
```bash
# 1. Create token on GitHub.com
# 2. On VPS:
git config --global user.name "Your Username"
git config --global user.email "your-email@example.com"
echo "https://YOUR_USERNAME:YOUR_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
git config --global credential.helper store
```

### SSH Key Setup:
```bash
# 1. Generate key on VPS
ssh-keygen -t rsa -b 4096 -C "vps@101.50.2.59"

# 2. Add to GitHub.com
cat ~/.ssh/id_rsa.pub

# 3. Test connection
ssh -T git@github.com
```

## 🎯 Next Steps

After connecting to GitHub:

1. **Clone your repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/hackathon-service.git /opt/hackathon-service
   ```

2. **Deploy your application**:
   ```bash
   cd /opt/hackathon-service
   ./deploy-github.sh
   ```

3. **Test your deployment**:
   ```bash
   curl http://101.50.2.59/api/v1/
   ```

---

**Your VPS is now connected to GitHub and ready for deployment! 🚀** 