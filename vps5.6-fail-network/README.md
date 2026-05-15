# vps5.6-fail-network

Ansible-проект для подготовки VPS с намеренно сломанной сетевой конфигурацией. Плейбук кладёт скрипт `haha.sh` на сервер и регистрирует его в cron на событие `@reboot`.

При перезагрузке скрипт ждёт 60 секунд, берёт текущий IP интерфейса `eth0`, добавляет суффикс `99` к IP-адресу и вписывает это значение в `/etc/network/interfaces.d/50-cloud-init.cfg`, после чего перезапускает сетевой сервис. Сервер теряет сетевую доступность — кандидат должен восстановить её.

## Structure

```text
vps5.6-fail-network/
├── inventory.ini
├── vps5.6-fail-network.yml
├── group_vars/
│   └── all.yml
├── handlers/
│   └── main.yml
├── requirements.yml
└── templates/
    └── haha.sh.j2
```

## Before Running

Отредактируй `inventory.ini`, вставив IP целевого сервера:

```ini
[web]
<TARGET_IP> ansible_user=root ansible_private_key_file=~/.ssh/ansible_task ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
```

Ключевые переменные в `group_vars/all.yml`:

```yaml
script_path: /opt/haha.sh        # куда кладётся скрипт
script_sleep: 60                  # задержка в секундах после reboot
network_interface: eth0           # сетевой интерфейс
network_interfaces_file: /etc/network/interfaces.d/50-cloud-init.cfg
ip_suffix: "99"                   # суффикс, дописываемый к IP
```

## Run

```bash
ansible-playbook -i inventory.ini vps5.6-fail-network.yml
```

После запуска плейбука перезагрузи сервер, чтобы активировать cron-задание:

```bash
ansible -i inventory.ini web -m ansible.builtin.reboot
```

Сервер станет недоступен примерно через 60 секунд после старта ОС.

## What Happens

1. `/opt/haha.sh` создаётся с правами `0755`.
2. Cron-запись `@reboot /bin/bash /opt/haha.sh` регистрируется для root.
3. При следующей перезагрузке скрипт берёт IP с `eth0`, строит строку `<IP>99` и заменяет оригинальный IP этой строкой в файле сетевых интерфейсов.
4. `systemctl restart networking.service` применяет сломанную конфигурацию.

## Manual Check

Убедиться, что скрипт и cron установлены:

```bash
ansible -i inventory.ini web -m ansible.builtin.command -a "cat /opt/haha.sh"
ansible -i inventory.ini web -m ansible.builtin.command -a "crontab -l"
```
