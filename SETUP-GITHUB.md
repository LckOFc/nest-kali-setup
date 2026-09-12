# INSTRUÇÕES — PUSH PARA GITHUB

## 1. Instale GitHub CLI (se não tiver)

```powershell
winget install GitHub.cli
```

## 2. Faça login

```powershell
gh auth login
```

Escolha:
- GitHub.com
- HTTPS
- Login with a web browser
- Cole o código que aparecer

## 3. Crie o repositório e push

```powershell
cd C:\tmp\nest-kali-setup
gh repo create nest-kali-setup --public --source=. --push
```

Ou manualmente:

```powershell
cd C:\tmp\nest-kali-setup
git remote add origin https://github.com/SEU-USUARIO/nest-kali-setup.git
git branch -M main
git push -u origin main
```

## 4. No Kali, clone e use

```bash
git clone https://github.com/SEU-USUARIO/nest-kali-setup.git
cd nest-kali-setup
chmod +x kali-setup.sh
./kali-setup.sh
source ~/.bashrc
nest
```

## 5. Sincronizar tools do Windows

Após o setup, copie as ferramentas:

```bash
# Shadow Toolkit
cp -r /mnt/c/Users/devel/shadow-toolkit/* ~/.nest/tools/shadow/

# RE Toolkit
cp -r /mnt/c/Users/devel/tools/reverse/RE-Toolkit/* ~/.nest/tools/re-toolkit/

# Payload Manager
cp -r /mnt/c/Users/devel/tools/payload-manager/* ~/.nest/tools/payload-manager/
```

---

**cold wire. warm scent. gnaw through. find home.**
