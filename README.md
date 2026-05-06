# VPS Task Playbooks

Repository with separate Ansible tasks for VPS training stands.

## Inventory Standard

All task inventories must use the same connection profile. Only the target server IP should normally change:

```ini
[web]
217.114.4.19 ansible_user=root ansible_private_key_file=~/.ssh/ansible_task ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
```

When adding a new playbook:

- keep the inventory group name as `[web]`;
- set the playbook `hosts: web`;
- keep `ansible_user`, `ansible_private_key_file`, and `ansible_ssh_common_args` identical;
- change only the IP address for the server where the task is being deployed.

## Tasks

- `vps1-webstack-django/` - Django + nginx + gunicorn troubleshooting stand.
- `vps2.6-opencart-move-fastpanel/` - source OpenCart VPS for a later manual FastPanel migration task.
