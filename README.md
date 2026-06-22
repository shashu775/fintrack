# FinTrack

A Kubernetes-based microservices financial application built as a CKA-prep
and portfolio project. Five FastAPI services communicate over a mix of
synchronous REST calls (via Ingress) and asynchronous events (via Kafka),
backed by per-service PostgreSQL databases, Redis caching, and a full
observability stack (assumed already deployed from your ELK/Prometheus work).

## Architecture

```
Client -> Ingress -> Auth Service       -> account-db (read)
                   -> Account Service   -> account-db
                   -> Transaction Service -> transaction-db
                                          -> publishes "transaction.created" to Kafka

Kafka "transaction.created" topic
        |-> Ledger Service       (consumes, writes to ledger-db, idempotent)
        |-> Notification Service (consumes, sends notification)
```

Transaction Service never calls Ledger or Notification directly — it
publishes an event and moves on. This means a slow or failing
Notification Service cannot block a transaction from being recorded,
which is the core argument for the event-driven design.

## Layout

```
fintrack/
├── services/
│   ├── auth-service/          # issues JWTs, in-memory user store (replace before real use)
│   ├── account-service/       # owns account-db, basic CRUD
│   ├── transaction-service/   # owns transaction-db, publishes Kafka events
│   ├── ledger-service/        # consumes Kafka, writes idempotent ledger entries
│   └── notification-service/  # consumes Kafka, sends notifications (logs for now)
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-secrets.yaml          # template — replace before applying
    ├── 02-postgres-account.yaml
    ├── 03-postgres-transaction.yaml
    ├── 04-postgres-ledger.yaml
    ├── 05-redis.yaml
    ├── 06-kafka-strimzi.yaml    # requires the Strimzi operator already installed
    ├── 07-auth-service.yaml
    ├── 08-account-service.yaml
    ├── 09-transaction-service.yaml
    ├── 10-ledger-service.yaml
    ├── 11-notification-service.yaml
    ├── 12-ingress.yaml
    └── 13-networkpolicy.yaml    # restricts DB access to only the owning services
```

## Build and push images

Each service has its own Dockerfile. Build and push all five (swap in your
own registry, matching what's referenced in the k8s manifests):

```bash
for svc in auth-service account-service transaction-service ledger-service notification-service; do
  docker build -t <your-registry>/$svc:latest services/$svc
  docker push <your-registry>/$svc:latest
done
```

Then replace every `<your-registry>/...` placeholder in `k8s/07-*.yaml`
through `k8s/11-*.yaml` with your actual image references.

## Deploy

Requires the Strimzi Kafka operator already installed in the cluster, and
a StorageClass named `manual` available (matching the static-PV pattern
used in your home lab — adjust `storageClassName` in the Postgres and
Kafka manifests if you're using a different provisioner).

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secrets.yaml          # edit values first
kubectl apply -f k8s/02-postgres-account.yaml
kubectl apply -f k8s/03-postgres-transaction.yaml
kubectl apply -f k8s/04-postgres-ledger.yaml
kubectl apply -f k8s/05-redis.yaml
kubectl apply -f k8s/06-kafka-strimzi.yaml

# wait for Kafka to be ready before deploying consumers
kubectl wait kafka/fintrack -n fintrack --for=condition=Ready --timeout=300s

kubectl apply -f k8s/07-auth-service.yaml
kubectl apply -f k8s/08-account-service.yaml
kubectl apply -f k8s/09-transaction-service.yaml
kubectl apply -f k8s/10-ledger-service.yaml
kubectl apply -f k8s/11-notification-service.yaml
kubectl apply -f k8s/12-ingress.yaml
kubectl apply -f k8s/13-networkpolicy.yaml
```

## Verify

```bash
kubectl get pods -n fintrack -w
kubectl get pvc -n fintrack
kubectl logs -n fintrack -l app=ledger-service -f
kubectl logs -n fintrack -l app=notification-service -f
```

Create a transaction and watch the events flow through:

```bash
kubectl port-forward -n fintrack svc/transaction-service 8000:80
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"account_id": "00000000-0000-0000-0000-000000000001", "amount": "42.50"}'
```

You should see the Ledger Service log an idempotent insert and the
Notification Service log a notification, both within a second or two
of the POST.

## Known gaps (intentional, for honesty in interviews)

- Auth Service uses a hardcoded in-memory user store, not real password
  hashing or a real user table — swap for bcrypt + account-db lookup.
- No mTLS between services and no TLS on the Kafka listener — fine for a
  home lab, not fine for anything resembling production.
- No HPA / autoscaling configured yet.
- No retry/backoff or dead-letter topic for failed Kafka consumption —
  a poison message will stall ledger-service's consumer loop.
