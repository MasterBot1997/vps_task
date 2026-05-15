# vps4.6-docker-start-problem

Ansible-проект для развёртывания задания **"Контейнер постоянно перезапускается / падает после старта"**.

Плейбук устанавливает Docker, собирает образ Node.js-приложения и поднимает заведомо сломанный `docker-compose.yml`. После запуска кандидат получает сервер, на котором контейнер `app` постоянно падает и перезапускается.

## Structure

```text
vps4.6-docker-start-problem/
├── inventory.ini
├── vps4.6-docker-start-problem.yml
├── group_vars/
│   └── all.yml
├── handlers/
│   └── main.yml
├── requirements.yml
├── tasks/
│   ├── preflight.yml
│   ├── docker.yml
│   ├── app.yml
│   └── deploy.yml
└── templates/
    ├── app.js.j2
    ├── package.json.j2
    ├── Dockerfile.j2
    └── docker-compose.yml.j2
```

## Что Делает Плейбук

1. Проверяет Ubuntu 22.04+.
2. Устанавливает Docker CE + `docker-compose-plugin` из официального репозитория.
3. Создаёт `/opt/notes-app/`, копирует исходники Node.js-приложения и собирает образ `notes-app:latest`.
4. Разворачивает `docker-compose.yml` с намеренной ошибкой и запускает контейнеры.

## Что Сломано

### 1. `DB_HOST: localhost` вместо `DB_HOST: db`

Приложение при старте сразу пытается подключиться к PostgreSQL. Внутри контейнера `localhost` — это сам контейнер, а не БД. Соединение завершается ошибкой:

```
Connecting to PostgreSQL at localhost:5432 ...
Failed to connect to database: connect ECONNREFUSED 127.0.0.1:5432
```

Контейнер выходит с кодом 1 → `restart: always` немедленно перезапускает его → цикл.

### 2. `restart: always` маскирует проблему

В `docker ps` контейнер отображается как `Restarting (1) X seconds ago`. В `docker ps` без `-a` может вовсе не попасться в момент проверки.

### 3. Нет `depends_on` и `healthcheck` для `db`

`app` может стартовать раньше, чем PostgreSQL примет соединения — даже после исправления `DB_HOST` приложение иногда падает на первом запуске (бонусный пункт для кандидата).

## Before Running

Поставь IP сервера в `inventory.ini`:

```ini
[web]
1.2.3.4 ansible_user=root ansible_private_key_file=~/.ssh/ansible_task ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
```

Переменные в `group_vars/all.yml` менять не нужно — они подставляются в шаблоны и соответствуют тому, что кандидат увидит на сервере.

## Run

```bash
ansible-playbook -i inventory.ini vps4.6-docker-start-problem.yml
```

После завершения плейбука на сервере будет запущена сломанная связка. Контейнер `app` сразу уйдёт в цикл рестартов.

## Проверка Развёртывания

```bash
# увидеть Restarting (1) X seconds ago
docker ps -a

# увидеть ошибку подключения к localhost:5432
docker logs app
```

## Ожидаемое Решение Кандидата

1. `docker ps -a` — заметить статус `Restarting`.
2. `docker logs app` — увидеть `ECONNREFUSED 127.0.0.1:5432`.
3. Понять: `localhost` внутри контейнера — это сам контейнер, БД там нет.
4. Исправить `DB_HOST: localhost` → `DB_HOST: db` в `docker-compose.yml`.
5. `docker compose down && docker compose up -d` — пересоздать контейнеры (не `restart`).
6. Убедиться: `docker ps` показывает `app` в статусе `Up`.
7. `curl http://localhost:8080` — приложение отвечает.

**Бонус:** добавить `depends_on` с `condition: service_healthy` и `healthcheck` для `db`.

## Критерии Оценки

| Балл | Критерий |
|------|----------|
| 1 | Диагностика через `docker ps -a` и `docker logs`, а не угадывание |
| 1 | Понимает: `localhost` ≠ другой контейнер; DNS в docker-сети работает по имени сервиса |
| 1 | Корректно правит `docker-compose.yml` |
| 1 | Применяет изменения через `down/up`, а не `restart`, понимает почему |
| 1 | Проверяет стабильность (`Up`, не `Restarting`) и доступность через `curl` |
