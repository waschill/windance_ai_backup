#!/bin/sh
set -eu
/usr/bin/install -o root -g root -m 0755 /tmp/windance-package-maintenance /usr/local/sbin/windance-package-maintenance
/usr/bin/printf '%s\n' 'waschilladmin ALL=(root) NOPASSWD: /usr/local/sbin/windance-package-maintenance' > /etc/sudoers.d/windance-package-maintenance
/bin/chown root:root /etc/sudoers.d/windance-package-maintenance
/bin/chmod 0440 /etc/sudoers.d/windance-package-maintenance
/usr/sbin/visudo -cf /etc/sudoers.d/windance-package-maintenance
