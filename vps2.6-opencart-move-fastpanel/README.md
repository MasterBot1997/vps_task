# vps2.6-opencart-move-fastpanel

Ansible-проект для подготовки исходного OpenCart-сайта на голом Ubuntu 24.04 сервере. Этот сервер имитирует старый VPS: кандидат позже должен перенести сайт руками на новый сервер с FastPanel.

Плейбук не устанавливает и не настраивает FastPanel. Он создаёт обычный рабочий web-stack:

- nginx;
- PHP-FPM 8.2;
- MySQL;
- OpenCart из официального архива;
- nginx vhost под домен;
- БД, пользователя БД и конфиги OpenCart;
- диагностические path-check страницы для проверки переноса.

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
    ├── nginx-opencart.conf.j2
    └── path-check.php.j2
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
9. Создаёт nginx vhost и отключает default site.
10. Создаёт диагностические `path-check-1.php` и `path-check-2.php`.
11. Выполняет финальные проверки главной, `/admin/`, БД и diagnostics.

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

If enabled, the playbook creates:

```text
{{ site_root }}/path-check-1.php
{{ site_root }}/path-check-2.php
```

Each page stores the first observed absolute site path in `oc_path_guard`. Later requests compare the current path to the stored path:

- same path: HTTP 200 with `OK`;
- mismatch: HTTP 500 with `Path mismatch. Expected: ... Current: ...`.

Basic Auth is enabled by default.

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
curl -u pathcheck:PathCheck-9xQ4-vR7m -H 'Host: shop.example.com' http://127.0.0.1/path-check-1.php
curl -u pathcheck:PathCheck-9xQ4-vR7m -H 'Host: shop.example.com' http://127.0.0.1/path-check-2.php
```

From outside, after DNS points to the VPS:

```bash
curl -I http://shop.example.com/
```
