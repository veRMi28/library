#!/bin/bash

sed -i '/%admin.*/d' /etc/sudoers
echo '%admin ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

useradd -m -s /bin/bash -G admin setup-user
mkdir -p /home/setup-user/.ssh
echo "{setup_user_pub}" > /home/setup-user/.ssh/authorized_keys
chown -R setup-user: /home/setup-user
chmod 664 /home/setup-user/.ssh/authorized_keys
