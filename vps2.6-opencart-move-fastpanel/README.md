# vps2.6-opencart-move-fastpanel

Production-oriented Ansible scaffold for deploying or migrating an OpenCart site to an Ubuntu server managed by FastPanel.

The playbook does not install FastPanel and does not overwrite FastPanel vhosts unless `manage_vhost: true`.

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
manage_vhost: false
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

## Migration Mode

When `migration_mode: true`, the playbook:

- creates `backup_dir`;
- dumps the existing target DB before changes when possible;
- can import `db_dump_path`;
- can rsync from `old_site_root` locally or from `old_server:old_site_root`;
- rewrites `config.php` and `admin/config.php` for the new path;
- clears cache/log directories.

Example:

```bash
ansible-playbook -i inventory.ini vps2.6-opencart-move-fastpanel.yml \
  -e site_domain=shop.example.com \
  -e old_server=root@OLD_SERVER_IP \
  -e old_site_root=/var/www/old-site \
  -e db_dump_path=/root/opencart_backup/source.sql
```

## FastPanel Notes

Default behavior:

```yaml
manage_vhost: false
```

This avoids breaking FastPanel-managed nginx/apache configs. If you want Ansible to manage a simple nginx vhost, set:

```yaml
manage_vhost: true
web_server: nginx
```

For real FastPanel production usage, prefer creating the domain/site in FastPanel first, then point `site_root`, `site_owner`, and `site_group` to the FastPanel-created values.

## Diagnostics

If enabled, the playbook creates:

```text
{{ site_root }}/path-check-1.php
{{ site_root }}/path-check-2.php
```

Each page stores the first observed absolute site path in `oc_path_guard`. Later requests compare the current path to the stored path:

- same path: HTTP 200 with `OK`;
- mismatch: HTTP 500 with `Path mismatch. Expected: ... Current: ...`.

Basic Auth is enabled by default for these pages.

Disable diagnostics:

```yaml
enable_path_diagnostics: false
```

## Manual OpenCart Install Fallback

OpenCart CLI installer support differs between versions. If auto-install cannot be completed universally, the playbook still prepares:

- site files;
- `config.php`;
- `admin/config.php`;
- database and DB user;
- permissions;
- diagnostics.

Then open:

```text
http://shop.example.com/install/
```

Use DB values from `group_vars/all.yml`. Set `show_credentials_after_install: true` only in a controlled environment if you want the playbook to print passwords.

## Final Checks

The playbook checks locally through `127.0.0.1` with the configured `Host` header, so DNS does not need to be switched before verification.

The playbook checks:

- homepage URL;
- admin URL;
- DB query as the OpenCart DB user;
- diagnostic pages when enabled.

Manual checks:

```bash
curl -I http://shop.example.com/
curl -I http://shop.example.com/admin/
mysql -u lowbrain_usr -p lowrain -e 'SELECT DATABASE();'
curl -u pathcheck:PathCheck-9xQ4-vR7m http://shop.example.com/path-check-1.php
curl -u pathcheck:PathCheck-9xQ4-vR7m http://shop.example.com/path-check-2.php
```
