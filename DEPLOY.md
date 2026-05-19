# Déploiement sur Google Cloud Run

## Prérequis
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- [Terraform >= 1.6](https://developer.hashicorp.com/terraform/install)
- [Docker](https://docs.docker.com/get-docker/) avec support buildx

## Étapes

### 1. Authentification
```bash
gcloud auth login
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

### 2. Init Terraform — créer le registry + le secret vide
```bash
cd terraform
terraform init
terraform apply \
  -var="project_id=shopllm-gateway-prod-496812" \
  -var="image=europe-west1-docker.pkg.dev/shopllm-gateway-prod-496812/shopllm-gateway/api:bootstrap" \
  -target=google_artifact_registry_repository.gateway \
  -target=google_secret_manager_secret.anthropic_key \
  -auto-approve
```

### 3. Ajouter la clé Anthropic dans Secret Manager
```bash
printf "%s" "TA_CLE_ANTHROPIC" | gcloud secrets versions add ANTHROPIC_API_KEY --data-file=-
```

### 4. Build + push de l'image (linux/amd64 requis pour Cloud Run)
```bash
cd ..
IMAGE="europe-west1-docker.pkg.dev/shopllm-gateway-prod-496812/shopllm-gateway/api:v0.3.0"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push .
```

### 5. Apply complet
```bash
cd terraform
terraform apply \
  -var="project_id=shopllm-gateway-prod-496812" \
  -var="image=$IMAGE" \
  -auto-approve
```

## URL de production
```
https://shopllm-gateway-1032746299850.europe-west1.run.app
```

## Mise à jour d'une nouvelle version
```bash
IMAGE="europe-west1-docker.pkg.dev/shopllm-gateway-prod-496812/shopllm-gateway/api:vX.Y.Z"
docker buildx build --platform linux/amd64 -t "$IMAGE" --push .
cd terraform && terraform apply -var="project_id=shopllm-gateway-prod-496812" -var="image=$IMAGE" -auto-approve
```
