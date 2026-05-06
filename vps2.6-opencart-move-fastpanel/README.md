# vps2.6-opencart-move-fastpanel

Ansible-проект для подготовки исходного OpenCart-сайта на голом Ubuntu 24.04 сервере. Этот сервер имитирует старый VPS: кандидат позже должен перенести сайт руками на новый сервер с FastPanel.

Плейбук не устанавливает и не настраивает FastPanel. Он создаёт обычный рабочий web-stack:

- nginx;
- PHP-FPM 8.3;
- MySQL;
- OpenCart из официального архива;
- nginx vhost под домен;
- БД, пользователя БД и конфиги OpenCart;
- диагностические товарные страницы для проверки переноса.

## Structure

```text
vps2.6-opencart-move-fastpanel/
├── inventory.ini
├── vps2.6-opencart-move-fastpanel.yml
├── group_vars/
│   └── all.yml
├── handlers/
│   └── main.yml
├── requirements.yml
├── tasks/
│   ├── configure.yml
│   ├── database.yml
│   ├── diagnostics.yml
│   ├── filesystem.yml
│   ├── migration.yml
│   ├── opencart.yml
│   ├── packages.yml
│   ├── preflight.yml
│   ├── verify.yml
│   └── vhost.yml
└── templates/
    ├── admin_config.php.j2
    ├── config.php.j2
    ├── htaccess.j2
    ├── nginx-opencart.conf.j2
    ├── path-check.php.j2
    └── user.ini.j2
```

## Что Делает

1. Проверяет, что исходный сервер Ubuntu 24.04+.
2. Ставит пакеты nginx, PHP-FPM, PHP extensions, MySQL, unzip, curl, wget, rsync, python3-pymysql.
3. Настраивает PHP-параметры.
4. Создаёт директорию сайта `/var/www/<домен>`.
5. Создаёт БД `lowrain` и пользователя `lowbrain_usr`.
6. Скачивает официальный архив OpenCart.
7. Копирует содержимое `upload/` в site root.
8. Генерирует `config.php` и `admin/config.php`.
9. Создаёт `.htaccess` и `.user.ini` с повышенными PHP limits.
10. Создаёт nginx vhost и отключает default site.
11. Создаёт скрытые диагностические PHP-файлы и открывает их через товарные URL.
12. Выполняет финальные проверки главной, `/admin/`, БД и diagnostics.

## Before Running

Install required Ansible collections:

```bash
ansible-galaxy collection install -r requirements.yml
```

Edit:

```bash
inventory.ini
group_vars/all.yml
```

Inventory uses the repository-wide standard. Usually only the IP changes:

```ini
[web]
217.114.4.19 ansible_user=root ansible_private_key_file=~/.ssh/ansible_task ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
```

Important variables:

```yaml
site_domain: ""
site_root: "/var/www/{{ site_domain }}"
db_name: "lowrain"
db_user: "lowbrain_usr"
db_password: "DB-LowRain-7mK2-xP9q-V4sZ"
manage_vhost: true
migration_mode: false
enable_path_diagnostics: true
remove_install_dir: true
```

Production passwords should be moved into Ansible Vault.

Per-site PHP limits are rendered into both `.htaccess` and `.user.ini`:

```yaml
site_php_values:
  memory_limit: "512M"
  upload_max_filesize: "128M"
  post_max_size: "128M"
  max_execution_time: "300"
  max_input_time: "300"
  max_input_vars: "5000"
```

On the source nginx server `.user.ini` is relevant for PHP-FPM. The `.htaccess` file is kept for Apache/LiteSpeed/FastPanel-style migrations.

## Run

The deployment domain is intentionally not hardcoded. Pass it at runtime:

```bash
ansible-playbook -i inventory.ini vps2.6-opencart-move-fastpanel.yml -e site_domain=shop.example.com
```

The default site root becomes:

```text
/var/www/shop.example.com
```

## OpenCart Install

The playbook prepares the official OpenCart files, database, configs and permissions. It also tries CLI install when the selected OpenCart archive provides a compatible CLI installer.

If automatic install is not available for the selected OpenCart version, finish the install in browser:

```text
http://shop.example.com/install/
```

Use DB values from `group_vars/all.yml`. Set this only in a controlled environment if you want Ansible to print passwords:

```yaml
show_credentials_after_install: true
```

## Diagnostics For Manual Move

If enabled, the playbook creates product-looking diagnostic URLs:

```text
http://shop.example.com/index.php?route=product/product&product_id=43
http://shop.example.com/index.php?route=product/product&product_id=40
```

Behind nginx these URLs are internally rewritten to hidden PHP files in the site root. The same rewrite rules are also rendered into `.htaccess` for a later FastPanel/Apache/LiteSpeed migration. Each page stores the first observed absolute site path in `oc_path_guard`. Later requests compare the current path to the stored path:

- same path: HTTP 200 with `OK`;
- mismatch: HTTP 500 with `Path mismatch. Expected: ... Current: ...`.

Diagnostics are public by default because they are part of the candidate-facing migration check. The OpenCart admin credentials are used for the CMS admin user, not for these pages.

Optional Basic Auth can still be enabled if needed:

```yaml
path_diagnostics_basic_auth: true
```

Disable diagnostics:

```yaml
enable_path_diagnostics: false
```

## Optional Migration Mode

For this case the default is:

```yaml
migration_mode: false
```

The playbook is meant to create the source VPS. The `tasks/migration.yml` file remains available only as an optional helper if later you want to seed this source from another old site.

## Final Checks

The playbook checks locally through `127.0.0.1` with the configured `Host` header, so DNS does not need to be switched before verification.

Manual checks:

```bash
curl -I -H 'Host: shop.example.com' http://127.0.0.1/
curl -I -H 'Host: shop.example.com' http://127.0.0.1/admin/
mysql -u lowbrain_usr -p lowrain -e 'SELECT DATABASE();'
curl -H 'Host: shop.example.com' 'http://127.0.0.1/index.php?route=product/product&product_id=43'
curl -H 'Host: shop.example.com' 'http://127.0.0.1/index.php?route=product/product&product_id=40'
```

From outside, after DNS points to the VPS:

```bash
curl -I http://shop.example.com/
```
