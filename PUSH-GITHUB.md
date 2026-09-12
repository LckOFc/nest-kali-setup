# Push para GitHub Privado

## Passo 1: Instalar GitHub CLI (se necessário)

```powershell
winget install GitHub.cli
```

## Passo 2: Fazer login

```powershell
gh auth login
```

Escolha:
- GitHub.com
- HTTPS
- Login with a web browser
- Cole o código que aparecer no terminal

## Passo 3: Criar repositório privado e push

```powershell
cd C:\tmp\nest-kali-setup
gh repo create nest-kali-setup --private --source=. --push
```

Ou se já tiver criado na web:

```powershell
cd C:\tmp\nest-kali-setup
git remote add origin https://github.com/privar/nest-kali-setup.git
git branch -M main
git push -u origin main
```

## Passo 4: No Kali, clone e use

```bash
git clone https://github.com/privar/nest-kali-setup.git
cd nest-kali-setup
chmod +x kali-setup.sh
./kali-setup.sh
source ~/.bashrc
nest
```

## Passo 5: Sincronizar tools do Windows

Após o setup no Kali:

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
