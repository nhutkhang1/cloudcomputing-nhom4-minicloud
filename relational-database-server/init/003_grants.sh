#!/bin/sh
# Grant the Flask application account read-only access to studentdb.
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT SELECT ON studentdb.* TO '${MARIADB_USER}'@'%';
FLUSH PRIVILEGES;
SQL
