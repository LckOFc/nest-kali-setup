# Pushing to Private GitHub Repository

## 1. Create Private Repository on GitHub

Go to: https://github.com/new

Fill in:
- **Repository name:** nest-kali-setup
- **Description:** The Forged Nest — Kali Linux Setup (Private)
- **Visibility:** 🔒 Private
- **Initialize:** Do NOT initialize (we have commits)
- Click **Create repository**

## 2. Connect and Push

```powershell
cd C:\tmp\nest-kali-setup
git remote add origin https://github.com/privar/nest-kali-setup.git
git branch -M main
git push -u origin main
```

If prompted for credentials:
- Username: `privar`
- Password: Use your GitHub Personal Access Token (not password)

## 3. Generate Personal Access Token (if needed)

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Select scopes: `repo` (full control)
4. Click **Generate token**
5. Copy the token (starts with `ghp_...`)
6. Use this token as password when pushing

## 4. Verify Push

```powershell
git remote -v
git status
```

## 5. Clone on Kali

```bash
git clone https://github.com/privar/nest-kali-setup.git
cd nest-kali-setup
chmod +x kali-setup.sh
./kali-setup.sh
source ~/.bashrc
nest
```

---

**cold wire. warm scent. gnaw through. find home.**
