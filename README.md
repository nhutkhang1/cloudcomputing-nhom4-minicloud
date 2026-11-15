# cloudcomputing-nhom4-minicloud

Group 4's Cloud Computing project: **9 server types, 11 containers**, connected
through the `cloud-net` Docker bridge network. The Web and Flask App images are
built locally; the other services use existing images.

## Project team

| Member | Student ID | Responsibilities |
| --- | --- | --- |
| Nguyễn Nhựt Khang | 523H0145 | Web, App, MariaDB, Keycloak, report |
| Nguyễn Trần Hoàng Nhân | 523H0164 | Compose, network, Gateway, Docker Hub, EC2 |
| Nguyễn Thành Nam | 523H0117 | MinIO, BIND9, Prometheus, Grafana, testing |

## Requirements

- Docker Engine on Linux, or Docker Desktop with Linux containers.
- Docker Compose with support for `up --wait` (Compose v2 or newer).
- Git and internet access for cloning, pulling images, and installing build dependencies.
- Bash, curl, and Python 3 for the optional manual API checks below.
- Available host ports listed in [Service addresses](#service-addresses).

The UID/GID examples below target a Linux host. This configuration uses local HTTP
endpoints and Keycloak development mode. Docker Hub publication and EC2 deployment
are separate project stages; they have not been validated by the source packaging checks.

## Repository structure

```text
.
├── docker-compose.yml
├── .env.example
├── .gitattributes
├── .gitignore
├── api-gateway-proxy-server/nginx.conf
├── application-backend-server/       # Flask APIs, sample JSON, templates, tests
├── authentication-identity-server/import/realm_523H0145.json
├── internal-dns-server/              # BIND9 options and cloud.local zone
├── monitoring-grafana-dashboard-server/
│   ├── dashboards/
│   └── provisioning/
├── monitoring-prometheus-server/prometheus.yml
├── object-storage-server/seed/       # Sample HTML and avatar; no runtime data
├── relational-database-server/init/  # SQL initialization and read grants
└── web-frontend-server/              # Nginx image, static pages, metrics exporter
```

Node Exporter is defined directly in Compose and does not need a source directory.

Two shell files are part of the runtime and must be retained:

| File | Purpose |
| --- | --- |
| `web-frontend-server/40-metrics-exporter.sh` | The image entrypoint launches the Nginx exporter, exposed through `/metrics`. |
| `relational-database-server/init/003_grants.sh` | MariaDB initialization grants the App account `SELECT` on `studentdb.*`. |

## First-time setup

Run host commands from the repository root. The commands in this README are
instructions to execute manually; packaging checks have not started the stack.

### 1. Clone and prepare configuration

```bash
git clone https://github.com/nhutkhang1/cloudcomputing-nhom4-minicloud.git
cd cloudcomputing-nhom4-minicloud
cp .env.example .env
id -u
id -g
mkdir -p object-storage-server/data
```

Edit `.env` to set the MinIO administrator username and environment-specific
values. The sample passwords use the repository name for the local demo. Set
`HOST_UID` and `HOST_GID` to your numeric IDs so MinIO can write to the directory
you just created. The MinIO password must contain at least eight characters.
`.env` and runtime data are ignored by Git.

| Variables | Meaning |
| --- | --- |
| `DOCKERHUB_USER`, `IMAGE_TAG` | Namespace and tag for the locally built Web/App images. Replace `your-dockerhub-username` with your namespace before publishing. Building locally does not publish images. |
| `CLOUD_PREFIX` | Network prefix, initially `10.10.10`. Keep the BIND9 zone records in sync if it changes, and increment the zone's SOA serial. |
| `MARIADB_ROOT_PASSWORD` | MariaDB administrator password. |
| `APP_DB_USER`, `APP_DB_PASSWORD` | Dedicated database account used by Flask. |
| `DB_BIND` | Host interface for MariaDB, initially `127.0.0.1`. Containers connect through the Docker network. |
| `KC_ADMIN_USER`, `KC_ADMIN_PASSWORD` | Keycloak bootstrap administrator. |
| `KC_REALM` | Keep `realm_523H0145` to match the realm import and App configuration. |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | MinIO administrator credentials. |
| `HOST_UID`, `HOST_GID` | Linux host ownership IDs for MinIO's bind-mounted data directory. |
| `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD` | Grafana initial administrator credentials. |

Compose rejects missing required credential variables. The sample credentials
satisfy this check.

### 2. Demo user credentials

The imported users `sv01` and `sv02` also use the repository name as their sample
password. To change these values before the first startup, edit each user's
password credential in
`authentication-identity-server/import/realm_523H0145.json` locally.

User credentials and the bootstrap administrator credentials are managed
separately. Keep the realm
`realm_523H0145`, public client `flask-app`, and token audience `myapp` unchanged.
Do not commit the locally edited realm file containing real passwords.

The realm is imported when it does not already exist. For an existing installation,
change user passwords through the Keycloak Admin Console; editing the import file
does not overwrite the existing realm. Bootstrap administrator credentials also
apply to initial setup, rather than acting as a password reset mechanism.

### 3. Check for conflicts, build, and start

Inspect the host before starting another stack:

```bash
docker ps --format 'table {{.Names}}\t{{.Ports}}'
docker network ls
docker compose config --quiet
```

The default network name is `cloud-net`, subnet `10.10.10.0/24`, and project name
is `minicloud`. An existing demo may use the same network, subnet, ports, and volume
names. Coordinate its shutdown or a deliberate configuration change before startup.
Changing only the Compose project name does not resolve the shared ports/network.

```bash
docker compose build
docker compose up -d --wait --wait-timeout 300
docker compose ps
```

Check that all 11 services become healthy. On first startup, MariaDB loads its SQL
and grants, Keycloak imports the realm, and Grafana provisions its datasource and
dashboards. MinIO bucket creation and object upload are manual, as described below.

If a service fails, inspect its status and logs before making changes:

```bash
docker compose ps -a
docker compose logs --tail=100 application-backend-server
docker compose logs --tail=100 relational-database-server
```

Review logs before sharing them; they can contain environment-specific details.

## Service addresses

The following URLs use the default host ports and local machine:

| Service | Address / host port | Container port |
| --- | --- | --- |
| API Gateway | `http://localhost/` | 80 |
| Web replica 1 | `http://localhost:8080/` | 80 |
| Web replica 2 | `http://localhost:8082/` | 80 |
| Flask App | `http://localhost:8085/hello` | 8081 |
| Keycloak Admin Console | `http://localhost:8081/auth/admin/` | 8080 |
| MariaDB | `127.0.0.1:3306` | 3306 |
| MinIO API / Console | `http://localhost:9000/` / `http://localhost:9001/` | 9000 / 9001 |
| BIND9 DNS | `127.0.0.1:1053`, UDP and TCP | 53 |
| Node Exporter | `http://localhost:9100/metrics` | 9100 |
| Prometheus | `http://localhost:9090/targets` | 9090 |
| Grafana | `http://localhost:3000/` | 3000 |

The Gateway routes `/` and `/blog/` to the Web replicas, `/api/` to Flask with
the `/api` prefix removed, `/student/` to Flask's `/student`, and `/auth/` to
Keycloak while preserving its prefix.

## Manual verification

### Web, API, and database

```bash
curl -i http://localhost/gateway-health
curl -i http://localhost/api/hello
curl -sS http://localhost/api/student
curl -sS http://localhost/api/students-db
```

Expect HTTP 200, a greeting, a JSON student list, and rows read from MariaDB.
Open `http://localhost/student/` or append `?format=html` to the student API URLs
to view HTML tables. `?format=json` explicitly requests JSON.

Repeat the Web request to observe the `X-Served-By` header from both replicas:

```bash
for attempt in {1..8}; do
  curl -sS -D - -o /dev/null http://localhost/
done
```

The exact response order may vary; both replicas should serve requests.

To inspect the seed data directly, enter the database password at the prompt:

```bash
docker compose exec relational-database-server mariadb -uroot -p studentdb
```

```sql
SELECT id, student_id, fullname, dob, major FROM students ORDER BY id;
EXIT;
```

The sample date of birth for Nguyễn Thành Nam (`523H0117`) is `2005-11-02`.
Use a fresh database or inspect the existing data before comparing it with the seed.

### Keycloak token authentication

Open the Admin Console, log in using the credentials from `.env`, and select
`realm_523H0145`. Verify users `sv01`/`sv02`, client `flask-app`, and its `myapp`
audience mapper. Localhost access does not require changing the master realm's SSL setting.

Without a token, this request should return HTTP 401:

```bash
curl -i http://localhost/api/secure
```

The following Python check prompts for the user's password without echoing it,
obtains a token, and prints only the protected API response:

```bash
python3 - <<'PY'
import getpass
import json
import urllib.parse
import urllib.request

form = urllib.parse.urlencode({
    "grant_type": "password",
    "client_id": "flask-app",
    "username": "sv01",
    "password": getpass.getpass("Password for sv01: "),
}).encode()
token_request = urllib.request.Request(
    "http://localhost:8081/auth/realms/realm_523H0145/protocol/openid-connect/token",
    data=form,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
with urllib.request.urlopen(token_request, timeout=15) as response:
    token = json.load(response)["access_token"]
secure_request = urllib.request.Request(
    "http://localhost/api/secure",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(secure_request, timeout=15) as response:
    print("HTTP", response.status)
    print(response.read().decode())
PY
```

Expect HTTP 200 with `preferred_username` equal to `sv01`. Repeat with `sv02` by
changing the username and prompt. Tokens expire after 300 seconds; obtain a new
token when needed. Avoid printing or including tokens in screenshots.

### MinIO buckets and sample objects

Log in to `http://localhost:9001/` using the MinIO credentials from `.env`.
To initialize the sample objects with the bundled MinIO client, open a shell:

```bash
docker compose exec object-storage-server sh
```

Run these commands **inside that container**, then return to the host with `exit`:

```sh
mc alias set local http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb --ignore-existing local/demo local/profile-pics local/documents
mc anonymous set private local/demo
mc anonymous set download local/profile-pics
mc anonymous set private local/documents
mc cp /seed/index.html local/demo/index.html
mc cp /seed/avatar.jpg local/profile-pics/avatar.jpg
mc ls --recursive local/
exit
```

The sample upload commands overwrite objects with the same names. Run them against
your intended demo instance. The `mc` alias is stored in the container and may need
to be recreated after the container is replaced; buckets/objects remain in `/data`.

From the host, verify the public avatar:

```bash
curl -I http://localhost:9000/profile-pics/avatar.jpg
```

Expect HTTP 200. The `demo` and `documents` buckets remain private. To upload your
own PDF, replace `/absolute/path/to/report.pdf` below; the PDF is not included in source:

```bash
docker compose exec -T object-storage-server mc pipe \
  --attr 'Content-Type=application/pdf' local/documents/report.pdf \
  < /absolute/path/to/report.pdf
curl -I http://localhost:9000/documents/report.pdf
```

Expect the anonymous PDF request to be denied (normally HTTP 403). Download it through
the authenticated Console or generate a temporary link:

```bash
docker compose exec object-storage-server mc share download --expire 15m local/documents/report.pdf
```

Treat the generated URL as a temporary credential. Updating a local PDF does not
update the object already stored in MinIO; upload the intended version explicitly.

### DNS

Query BIND9 directly using the tools already available in its container:

```bash
docker compose exec internal-dns-server dig @127.0.0.1 app-backend.cloud.local +short
docker compose exec internal-dns-server dig @127.0.0.1 minio.cloud.local +short
docker compose exec internal-dns-server dig @127.0.0.1 keycloak.cloud.local +short
```

Expect `10.10.10.20`, `10.10.10.50`, and `10.10.10.40` with the default prefix.
If `dig` is installed on the host, test the published port over both protocols:

```bash
dig @127.0.0.1 -p 1053 app-backend.cloud.local +short
dig @127.0.0.1 -p 1053 app-backend.cloud.local +tcp +short
```

Docker service-name resolution uses Docker's embedded DNS. The Compose file does
not make BIND9 the default resolver for all containers or for the host.

### Prometheus and Grafana

1. Open `http://localhost:9090/targets`. Expect the `node` target and both `web`
   targets to be UP after a few scrape intervals.
2. Log in to Grafana using the credentials from `.env`.
3. Open `http://localhost:3000/d/minicloud-system-health-523h0117` and check the CPU,
   memory, and network panels of **System Health of 523H0117**.
4. The **Node Exporter Full** dashboard is also provisioned. Select the Prometheus
   datasource, job, and node if they are not selected automatically.

Node Exporter runs with the supplied container configuration. These dashboards do
not provide independent CPU/memory measurements for every container. Panels requiring
additional host mounts or optional collectors may have no data.

## Optional Flask unit tests

These tests mock MariaDB and Keycloak HTTP calls and use RS256 test keys generated
in memory. They do not require or validate a running Compose stack.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r application-backend-server/requirements.txt
.venv/bin/python -m unittest discover -s application-backend-server/tests -v
```

## Persistence and shutdown

| Data | Storage |
| --- | --- |
| MariaDB | Named volume `minicloud-mariadb-data` |
| Keycloak | Named volume `minicloud-keycloak-data` |
| Prometheus | Named volume `minicloud-prometheus-data` |
| Grafana | Named volume `minicloud-grafana-data` |
| MinIO objects | Host directory `object-storage-server/data/` |

The named-volume prefix follows the Compose project name if it is overridden.

```bash
docker compose stop
# To resume:
docker compose start
```

To remove this project's containers and network while retaining persistent data:

```bash
docker compose down
```

Do not add `--volumes` when you want to retain the database, realm, or monitoring data.
Seed SQL and grants run only when MariaDB initializes an empty data directory.
Changing `.env` does not reset accounts already stored in MariaDB, Keycloak, or
Grafana; use each service's account-management tools for an existing installation.
Editing a seed file does not update previously imported rows or MinIO objects.

Keep the repository at a stable path while containers use its bind mounts.
Before moving the source, coordinate shutdown and back up named volumes and MinIO
data; changing a project name does not migrate existing data.

## Validation status

Source packaging checks passed: 12 Flask unit tests, configuration parser checks,
Compose configuration validation, and static integration checks across services.
The manual commands above are a verification procedure to run in your environment.
Full-stack runtime, image publication, and EC2 deployment remain pending for this
packaged repository.
