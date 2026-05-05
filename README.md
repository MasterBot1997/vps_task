# vps1-webstack-django

Учебный Ansible-проект для развёртывания Django-сайта на Ubuntu 24.04 через nginx, gunicorn, systemd и unix socket.

## Что разворачивается

- Django project: `retro_site`
- Django app: `your_app`
- App user: `webapp`
- App group: `www-data`
- App dir: `/var/www/retro_site`
- Virtualenv: `/var/www/retro_site/.venv`
- Gunicorn socket: `/run/retro_site/gunicorn.sock`
- Systemd service: `retro_site.service`
- Nginx site: `retro_site`
- Static root: `/var/www/retro_site/staticfiles`
- HTTP port: `80`

## Структура

```text
vps1-webstack-django/
├── inventory.ini
├── playbook.yml
├── group_vars/
│   └── all.yml
├── templates/
│   ├── django_settings.py.j2
│   ├── gunicorn.service.j2
│   ├── nginx_site.conf.j2
│   ├── manage.py.j2
│   ├── urls.py.j2
│   ├── views.py.j2
│   ├── wsgi.py.j2
│   ├── index.html.j2
│   └── retro90.css.j2
└── README.md
```

## Запуск

Отредактируйте `inventory.ini` и замените `YOUR_SERVER_IP` на IP учебного VPS.

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Если пользователь в inventory не `root`, он должен иметь sudo-права, потому что playbook использует `become: true`.

## Проверка после установки

```bash
curl -fsS http://127.0.0.1/
curl -fsS http://127.0.0.1/ | grep 'DJANGO CENTRAL 1999'
systemctl status retro_site --no-pager
systemctl status nginx --no-pager
ss -xlpn | grep /run/retro_site/gunicorn.sock
nginx -t
ls -la /var/www/retro_site/.venv/bin/gunicorn
ls -la /var/www/retro_site/staticfiles/your_app/retro90.css
```

С внешней машины:

```bash
curl -fsS http://YOUR_SERVER_IP/
```

## Как сломать кейс для кандидата

### Поломка 1: неправильный путь к gunicorn в systemd

Откройте unit:

```bash
nano /etc/systemd/system/retro_site.service
```

Замените:

```ini
Environment="PATH=/var/www/retro_site/.venv/bin"
ExecStart=/var/www/retro_site/.venv/bin/gunicorn \
```

на:

```ini
Environment="PATH=/var/www/retro_site/venv/bin"
ExecStart=/var/www/retro_site/venv/bin/gunicorn \
```

Примените:

```bash
systemctl daemon-reload
systemctl restart retro_site
systemctl status retro_site --no-pager
```

Ожидаемый симптом: `retro_site.service` не стартует, nginx отдаёт `502 Bad Gateway`.

### Поломка 2: неправильный socket в nginx

Откройте nginx site:

```bash
nano /etc/nginx/sites-available/retro_site
```

Замените:

```nginx
proxy_pass http://unix:/run/retro_site/gunicorn.sock;
```

на:

```nginx
proxy_pass http://unix:/run/retro_site/missing.sock;
```

Примените:

```bash
nginx -t
systemctl reload nginx
curl -i http://127.0.0.1/
```

Ожидаемый симптом: gunicorn работает, но nginx не может подключиться к socket и отдаёт `502 Bad Gateway`.

## Как вернуть рабочее состояние

Самый чистый способ: повторно применить Ansible. Он перезапишет systemd unit и nginx config из шаблонов, перезапустит сервисы и выполнит health-check.

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Ручное восстановление пути gunicorn:

```ini
Environment="PATH=/var/www/retro_site/.venv/bin"
ExecStart=/var/www/retro_site/.venv/bin/gunicorn \
```

Ручное восстановление nginx socket:

```nginx
proxy_pass http://unix:/run/retro_site/gunicorn.sock;
```

После ручных правок:

```bash
systemctl daemon-reload
systemctl restart retro_site
nginx -t
systemctl reload nginx
curl -fsS http://127.0.0.1/ | grep 'DJANGO CENTRAL 1999'
```

