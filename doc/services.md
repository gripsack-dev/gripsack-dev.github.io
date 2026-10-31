# Docker Engine services

Services are explicit workspace outputs for existing container images. `grip up` starts selected services and waits for their declared readiness; there is no Gripsack daemon. Native packages, environments and dotfiles remain independent of Docker.

## Prerequisites

Use Linux x86_64 or WSL2 with a reachable local Linux Docker Engine Unix socket and permission to use it. Docker access is powerful host authority: source approval is not a container-security guarantee. For a nondefault local socket, pass `grip up --socket /path/to/docker.sock postgres`; later inspection and down use recorded state.

Images must use immutable `name@sha256:DIGEST` references, not floating tags. The PostgreSQL 18 digest below was obtained from an actual Docker pull and inspected repository digest during release preparation; that alone is not evidence of a Gripsack runtime test. Cold startup requires registry access and disk space.

## PostgreSQL workspace

Create `gripsack.ts`:

```typescript
import {
  defineWorkspace, exec, lit, service, task, workspace,
} from "@gripsack/core";

const postgres = service("postgres", {
  image: "docker.io/library/postgres@sha256:979bccfde35445db618c65107d27d08c6c21339d8dc3ad4c830c6633947be0e4",
  ports: [{ address: "127.0.0.1", host: 55432, container: 5432 }],
  volumes: [{ name: "gripsack-guide-postgres18", target: "/var/lib/postgresql" }],
  env: {
    POSTGRES_USER: { kind: "literal", value: "app" },
    POSTGRES_DB: { kind: "literal", value: "app" },
    POSTGRES_PASSWORD: { kind: "inherited", name: "GRIPSACK_POSTGRES_PASSWORD" },
  },
  health: {
    kind: "command",
    argv: ["pg_isready", "-U", "app", "-d", "app"],
    interval_seconds: 2,
    timeout_seconds: 2,
    retries: 30,
  },
});
const databaseReady = task("database-ready", {
  services: ["postgres"],
  steps: [exec({ argv: [lit("/usr/bin/printf"), lit("postgres is healthy\\n")] })],
});

export default defineWorkspace(() => workspace({ outputs: [postgres, databaseReady] }));
```

The task deliberately uses a trusted host `/usr/bin/printf`; ensure it exists. `task.services` requires the recorded service to be **already healthy**. It never starts a service implicitly and this task is not a SQL or migration test. Service `depends_on: ["other-service"]` orders explicit startup by readiness, separately from task prerequisites.

## Start and inspect

Supply `GRIPSACK_POSTGRES_PASSWORD` from your secret manager into the calling process environment, not a literal in captured source, shell history or a committed file. The reference is captured; the secret value is inherited at startup. Docker administrators can inspect container environment values. Application logs may contain secrets too.

```sh
: "${GRIPSACK_POSTGRES_PASSWORD:?export the database secret from your secret manager}"
grip check
grip up postgres --timeout-seconds 180
grip services status --json
grip task run database-ready --closed-stdin
grip services logs postgres --lines 50
```

Review and approve the exact captured source and policy when prompted before startup. Ports must bind explicit loopback addresses; the example exposes PostgreSQL on `127.0.0.1:55432`, not the LAN. Readiness uses `pg_isready` inside the container; it does not prove your application's schema, credentials or queries work.

## Stop without deleting data

```sh
grip down postgres
grip services status --json
```

`down` stops/removes owned containers and retains named volumes. Startup can reuse the database data. PostgreSQL's initialization variables apply to a new data directory; changing the inherited password does not rotate credentials in an existing database. Use database-native administration and backups.

Changing a running service definition requires explicit `grip down postgres` followed by `grip up postgres`; startup does not silently replace it. Inherited credentials are resolved at startup, not continuously synchronized.

Status, logs and down inspect recorded owned state without evaluating current workspace source. They do not adopt or delete arbitrary containers. Profile generations and rollback do **not** roll back database contents, migrations, task effects or external services. No automatic database rollback is promised.

## Three different uses of OCI

These services run pre-existing container images through Docker Engine. [Native sharing](sharing.md) transports retained native artifacts through an OCI registry without making them container images. The old [BuildKit source builder and image exporter](builds.md) are retired.
