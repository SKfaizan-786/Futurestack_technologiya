# MedMatch AI - Kubernetes Deployment Guide
# Get Your Application Online with Public URL Access

## 🎯 **DEPLOYMENT OPTIONS (Choose One):**

### 🌟 **OPTION 1: Quick Cloud Deployment (Recommended)**

#### **A. DigitalOcean App Platform** ⭐ EASIEST
```bash
# 1. Push your code to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Go to DigitalOcean App Platform
# 3. Connect GitHub repo
# 4. Auto-detects Docker setup
# 5. Get instant public URL: https://your-app.ondigitalocean.app
```
**Cost**: ~$12-25/month | **Time**: 5 minutes | **URL**: Automatic

#### **B. Google Cloud Run** ⚡ SERVERLESS
```bash
# 1. Build and push images
docker build -t gcr.io/YOUR_PROJECT/medmatch-backend ./backend
docker build -t gcr.io/YOUR_PROJECT/medmatch-frontend ./frontend

# 2. Deploy
gcloud run deploy medmatch-backend --image gcr.io/YOUR_PROJECT/medmatch-backend
gcloud run deploy medmatch-frontend --image gcr.io/YOUR_PROJECT/medmatch-frontend
```
**Cost**: Pay per request | **Time**: 10 minutes | **URL**: Automatic HTTPS

#### **C. Heroku Container Registry**
```bash
# 1. Install Heroku CLI
# 2. Login and create apps
heroku create medmatch-backend
heroku create medmatch-frontend

# 3. Deploy containers
heroku container:push web -a medmatch-backend
heroku container:release web -a medmatch-backend
```
**Cost**: ~$7-25/month | **Time**: 15 minutes | **URL**: Automatic

---

### 🔥 **OPTION 2: Full Kubernetes (Production Ready)**

#### **A. Local Kubernetes + Tunnel**
```bash
# 1. Start local Kubernetes
minikube start

# 2. Deploy your application
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/ingress.yaml

# 3. Get public URL with ngrok
kubectl port-forward svc/medmatch-frontend-service 3000:3000
ngrok http 3000  # Get public URL instantly!
```

#### **B. Cloud Kubernetes**
```bash
# Google GKE
gcloud container clusters create medmatch-cluster --num-nodes=3
kubectl apply -f kubernetes/

# AWS EKS
eksctl create cluster --name medmatch-cluster --nodes=3
kubectl apply -f kubernetes/

# Azure AKS
az aks create --resource-group myResourceGroup --name medmatch-cluster --node-count 3
kubectl apply -f kubernetes/
```

---

## 🚀 **FASTEST PUBLIC URL (5 minutes)**

### **ngrok Tunnel (Works with your current setup)**
```bash
# 1. Your app is already running locally!
# Frontend: http://localhost:5173
# Backend: http://localhost:8000

# 2. Install ngrok
# Download from: https://ngrok.com/download

# 3. Get public URLs
ngrok http 5173  # Frontend public URL
ngrok http 8000  # Backend public URL

# 4. Share your links!
# Frontend: https://abc123.ngrok.io
# Backend: https://def456.ngrok.io
```

---

## 📋 **DEPLOYMENT CHECKLIST**

### **Before Deployment:**
- [ ] Update `kubernetes/service.yaml` secrets with real API keys
- [ ] Replace `your-domain.com` in `ingress.yaml` with your domain
- [ ] Set production environment variables
- [ ] Build and push Docker images to registry

### **Production Security:**
- [ ] Change all default passwords in `service.yaml`
- [ ] Set real `CEREBRAS_API_KEY` in secrets
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS with cert-manager
- [ ] Set up monitoring and logging

### **Required Environment Variables for Production:**
```bash
# API Keys
CEREBRAS_API_KEY=your_real_cerebras_key
SECRET_KEY=your_jwt_secret_key

# Database
POSTGRES_PASSWORD=secure_production_password
REDIS_PASSWORD=secure_redis_password

# Domains
CORS_ORIGINS=https://yourdomain.com
REACT_APP_API_URL=https://api.yourdomain.com
```

---

## 🎯 **RECOMMENDED NEXT STEPS:**

1. **IMMEDIATE (5 min)**: Use ngrok with your running app
2. **SHORT TERM (1 hour)**: Deploy to DigitalOcean App Platform
3. **LONG TERM**: Set up full Kubernetes with custom domain

**Your app is READY TO DEPLOY RIGHT NOW!** 🎉

Choose your preferred option and let's get you a public URL!