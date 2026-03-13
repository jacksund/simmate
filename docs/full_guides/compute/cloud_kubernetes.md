# Cloud & Kubernetes

Simmate workers can easily be containerized and deployed to cloud environments like AWS, Google Cloud, or DigitalOcean using Docker and Kubernetes.

## Docker

A Simmate worker only needs the Simmate python package and any external scientific software (like VASP, Quantum Espresso, or RDKit) installed.

### Example Dockerfile
Simmate provides several example Dockerfiles in the `envs/docker/` directory of the repository. A basic worker Dockerfile looks like this:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Install Simmate
RUN pip install simmate

# Copy your configuration (or use environment variables)
COPY settings.yaml /root/.simmate/settings.yaml

# Start the worker by default
CMD ["simmate", "engine", "start-worker"]
```

---

## Kubernetes

Deploying workers as a **Kubernetes Deployment** allows you to easily scale the number of workers up or down.

### Example Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simmate-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: simmate-worker
  template:
    metadata:
      labels:
        app: simmate-worker
    spec:
      containers:
      - name: worker
        image: your-registry/simmate-worker:latest
        env:
        - name: SIMMATE_DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: password
```

### Helm Charts
For more complex deployments (including the Web UI, Database, and Workers), Simmate provides Helm charts in `envs/helm/`. These charts help manage:

- Scaling workers based on queue size.
- Secret management for database credentials.
- Ingress for the Web UI.

---

## Serverless & Ephemeral Workers

Because Simmate workers can be configured to shut down when the queue is empty (`--close-on-empty-queue`), they are ideal for "serverless" or "auto-scaling" environments. You can trigger the creation of new worker pods/instances whenever new jobs are submitted to the database.
