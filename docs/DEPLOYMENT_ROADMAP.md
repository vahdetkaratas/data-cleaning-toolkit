# VPS’te Deploy Roadmap — Adım Adım

Kendi domain’inle Data Cleaning Toolkit’i VPS’te yayına almak için sıfırdan rehber. **Docker**, **docker-compose** ve **Caddy** (ters vekil + otomatik HTTPS) kullanıyoruz; deneyim gerektirmez, komutları sırayla uygulaman yeterli.

Bu depodaki `docker-compose.yml` uygulamayı yalnızca **8501** portunda yayınlar. Dışarıdan domain ve HTTPS için **Caddy** 80/443 üzerinden içerideki **127.0.0.1:8501** adresine yönlendirir.

---

## Ne Yapacağız (Özet)

1. VPS’e **SSH** ile bağlanacağız.
2. Sunucuya **Docker** ve **Docker Compose** kuracağız.
3. Projeyi VPS’e **kopyalayıp** Docker ile **çalıştıracağız**.
4. **Caddy** kurup domain’i **8501**’e yönlendireceğiz (reverse proxy; **Let’s Encrypt otomatik**).
5. **Domain’i** VPS’in IP’sine yönlendireceğiz (DNS).

Böylece `https://YOUR_DOMAIN` (ör. `https://app.example.com`) ile uygulama açılır.

---

## 0. Hazırlık (Bilgisayarında)

- **VPS bilgileri:** IP adresi (örn. `203.0.113.10`), kullanıcı adı (çoğunlukla `root`), şifre veya SSH key.
- **Domain:** Bir domain’in olmalı ve DNS’ini yönetebilmelisin (A kaydı ekleyeceğiz).
- **SSH istemcisi:**
  - **Windows:** PowerShell veya Windows Terminal (OpenSSH varsayılan gelir). Alternatif: [PuTTY](https://www.putty.org/).
  - **Mac/Linux:** Terminal’de `ssh` komutu vardır.

---

## 1. VPS’e İlk Bağlantı (SSH)

### Windows (PowerShell veya Terminal)

```powershell
ssh root@VPS_IP_ADRESI
```

Örnek: `ssh root@203.0.113.10`  
Şifre sorarsa VPS sağlayıcıdan aldığın şifreyi yaz (yazarken görünmez, Enter’a bas).

### Mac / Linux

```bash
ssh root@VPS_IP_ADRESI
```

Bağlandığında komut satırı `root@sunucuadi:~#` gibi bir şeye dönüşür. Artık komutları **VPS üzerinde** çalıştırıyorsun.

---

## 2. Sistemi Güncellemek

Bağlandıktan sonra sırayla:

**Debian / Ubuntu:**

```bash
apt update && apt upgrade -y
```

**CentOS / Rocky / Alma:**

```bash
dnf update -y
```

Bu rehberde komutlar **Debian/Ubuntu** için yazıldı. Başka dağıtım kullanıyorsan “Docker install [dağıtım adı]” diye aratıp ilk adımı ona göre değiştirirsin.

---

## 3. Docker Kurulumu

Docker, uygulamayı “konteyner” içinde çalıştırır; sunucuya doğrudan Python kurmadan aynı ortamı her yerde kullanırsın.

### 3.1 Docker’ı Yükle (Debian/Ubuntu)

```bash
apt install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a644 /etc/apt/keyrings/docker.asc

# Ubuntu için:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
# Saf Debian için yukarıdaki satır yerine (ubuntu → debian):
# echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Kurulum bitince kontrol:

```bash
docker --version
docker compose version
```

İkisi de sürüm yazıyorsa tamam.

---

## 4. Projeyi VPS’e Almak

İki yol var: **Git ile** (tercih) veya **dosya kopyalama**.

### Yol A: Git ile (GitHub’a attıysan)

```bash
apt install -y git
cd /opt
git clone https://github.com/your-username/data-cleaning-toolkit.git
cd data-cleaning-toolkit
```

`your-username` kısmını kendi GitHub kullanıcı veya organizasyon adınla değiştir; repo adını değiştirdiysen URL’yi ona göre güncelle. Repo özel ise token ile clone etmen gerekir; public ise bu yeterli.

### Yol B: Bilgisayarından Dosya Göndermek

Bilgisayarında proje klasörü açıkken (PowerShell / Terminal):

```bash
scp -r . root@VPS_IP_ADRESI:/opt/data-cleaning-toolkit
```

VPS’te:

```bash
cd /opt/data-cleaning-toolkit
```

Proje burada olmalı: `Dockerfile`, `docker-compose.yml`, `src/`, `data/`, `requirements.txt` vs.

---

## 5. Docker ile Uygulamayı Çalıştırmak

VPS’te proje dizinindeyken:

```bash
cd /opt/data-cleaning-toolkit
docker compose up -d --build
```

- `--build`: Image’ı projeden yeniden build eder.  
- `-d`: Arka planda çalışır.

Kontrol:

```bash
docker compose ps
```

`app` servisi “Up” görünmeli. Şimdilik tarayıcıda şu adresi dene:

`http://VPS_IP_ADRESI:8501`

Açılıyorsa Streamlit çalışıyordur. Üretimde **8501**’i internete açmak yerine yalnızca **Caddy** üzerinden domain ile vereceğiz.

---

## 6. Caddy Kurulumu (Reverse proxy + HTTPS)

**Caddy**, 80 ve 443’ü dinler; istekleri içerideki Streamlit’e (`127.0.0.1:8501`) iletir ve geçerli DNS olduğunda **Let’s Encrypt** sertifikasını **otomatik** alır ve yeniler (ayrıca Certbot gerekmez).

### 6.1 Caddy’yi yükle (Debian / Ubuntu)

[Caddy resmi kurulum](https://caddyserver.com/docs/install) ile uyumlu özet:

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update
apt install -y caddy
```

### 6.2 Caddyfile oluştur

```bash
nano /etc/caddy/Caddyfile
```

Var olan örnek içeriği silip aşağıdakine benzer bir blok yaz; **`YOUR_DOMAIN`** yerine gerçek host adını yaz (ör. `app.example.com`):

```caddyfile
YOUR_DOMAIN {
    request_body {
        max_size 50MB
    }
    reverse_proxy 127.0.0.1:8501
}
```

Kaydet: `Ctrl+O`, Enter, çık: `Ctrl+X`.

### 6.3 Yapılandırmayı uygula

```bash
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
systemctl enable caddy
```

`validate` hata vermezse devam. Sorun olursa `journalctl -u caddy -e` ile günlüğe bak.

**HTTPS:** A kaydı DNS’te VPS IP’sine işaret ettikten ve yayıldıktan sonra Caddy ilk istekte sertifikayı kendisi alır. DNS hazır değilse sertifika aşamasında hata görebilirsin; DNS’i doğrulayıp `systemctl reload caddy` yeterli olabilir.

---

## 7. Domain’i VPS’e Yönlendirmek (DNS)

Domain sağlayıcında (GoDaddy, Namecheap, Cloudflare, vs.) DNS ayarlarına gir.

- **Kayıt türü:** A  
- **Ad (Host):** `app` (veya `@` apex için; sağlayıcıya göre değişir)  
- **Değer (Value):** VPS’in **IP adresi**  
- TTL: 300 veya 3600

Örnek: `app.example.com` için host `app`, value `203.0.113.10`.  
Kaydı kaydedip birkaç dakika–saat bekle (DNS yayılımı). Sonra tarayıcıda `http://YOUR_DOMAIN` dene; Caddy arkada 8501’e proxy’ler. Uygulama çalışmıyorsa **502** benzeri bir hata görebilirsin; o zaman `docker compose ps` ile konteyneri kontrol et.

---

## 8. HTTPS notu (Caddy ile)

Bu yolda **Certbot kurmana gerek yok**: Caddy, domain doğru çözümlenince **Let’s Encrypt** kullanır. Tarayıcıda `https://YOUR_DOMAIN` açılıyorsa tamam.

---

## 9. Güvenlik Duvarı (Firewall)

Sadece gerekli portları aç:

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

22: SSH, 80: HTTP (ACME / yönlendirme), 443: HTTPS. **8501’i dışarı açma**; yalnızca **Caddy** içeriden `127.0.0.1:8501`’e bağlansın.

---

## 10. Sunucu Yeniden Açılınca Uygulamanın Başlaması

Docker Compose’ta `restart: unless-stopped` kullandık; VPS restart olsa bile konteyner tekrar ayağa kalkar. Caddy de servis olarak açılışta gelir (`systemctl enable caddy`).

Kontrol için:

```bash
docker compose ps
systemctl status caddy --no-pager
```

“Up” / `active` görünüyorsa tamam.

---

## 11. Güncelleme (Yeni Kod Attığında)

Git kullandıysan:

```bash
cd /opt/data-cleaning-toolkit
git pull
docker compose up -d --build
```

Dosya ile gönderdiysen yine `scp` ile atıp aynı `docker compose up -d --build` komutunu çalıştır.

---

## 12. Sorun Giderme

| Sorun | Ne Yapmalı |
|--------|-------------|
| `http://IP:8501` açılmıyor | `docker compose ps` ve `docker compose logs -f` ile konteyner çalışıyor mu, hata var mı bak. |
| Domain açılmıyor | DNS: `ping YOUR_DOMAIN` veya `dig YOUR_DOMAIN` ile IP doğru mu. **Caddy:** `caddy validate --config /etc/caddy/Caddyfile`, `journalctl -u caddy -e`. |
| 502 Bad Gateway | Caddy, 8501’e ulaşamıyor. VPS içinde `curl -sS http://127.0.0.1:8501` çalışıyor mu dene; `docker compose ps` ile app’in Up olduğundan emin ol. |
| HTTPS / sertifika hatası | A kaydı VPS’e işaret mi, 80/443 firewall’da açık mı; bir süre bekle, sonra `systemctl reload caddy`. |

---

## 13. Özet Komut Listesi (Kopyala-Yapıştır)

VPS’e ilk kez kurarken (Debian/Ubuntu, root) — Docker blokunu §3’teki gibi tam ekle; ardından:

```bash
apt install -y git debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy
cd /opt && git clone https://github.com/your-username/data-cleaning-toolkit.git
cd data-cleaning-toolkit
docker compose up -d --build
# Sonra /etc/caddy/Caddyfile içinde YOUR_DOMAIN + reverse_proxy 127.0.0.1:8501 (§6.2)
caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy
ufw allow 22,80,443 && ufw enable
```

Domain’i DNS’te VPS IP’sine A kaydı ile yönlendirmeyi unutma.

---

## Proje İçindeki Deploy Dosyaları

- **Dockerfile:** Uygulamanın Docker image tanımı.  
- **docker-compose.yml:** Tek komutla build + çalıştırma (port **8501**).  
- **Caddyfile:** Sunucuda `/etc/caddy/Caddyfile`; örnek blok bu rehberin **§6.2** bölümünde.

---

## Ek (isteğe bağlı): Nginx

Stack’ini **Nginx** ile kurmak istersen aynı rolü görür: 80/443’te dinleyip `proxy_pass http://127.0.0.1:8501` ile Streamlit’e yönlendirirsin; HTTPS için **Certbot** (`certbot --nginx`) kullanırsın. Bu rehberin ana yolu **Caddy**’dir; Nginx yalnızca alternatif bir seçenektir.

Bu roadmap’i takip edersen uygulama kendi domain’inle (HTTPS ile) VPS’te yayında olur. Takıldığın adımı yazarsan o adımı birlikte netleştirebiliriz.
