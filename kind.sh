#!/bin/bash

KIND_NODE_IMAGE=kindest/node:v1.25.8@sha256:00d3f5314cc35327706776e95b2f8e504198ce59ac545d0200a89e69fce10b7f

echo "
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: knative
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 32021
    hostPort: 15021
  - containerPort: 32080
    hostPort: 80
  - containerPort: 32443
    hostPort: 443
" | kind create cluster --image ${KIND_NODE_IMAGE} --wait 60s --config -


# Install istio
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update istio

kubectl create namespace istio-system
helm install istio-base istio/base -n istio-system --wait
helm install istiod istio/istiod -n istio-system --wait

kubectl create namespace istio-ingress
helm install istio-ingress istio/gateway -n istio-ingress --values helm_values/istio_gateway.yml --wait

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update jetstack

helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --version v1.11.0 --set installCRDs=true --wait

kubectl apply --wait -f 1-knative-crds
kubectl apply --wait -f 2-serving 
kubectl apply --wait -f 3-eventing
kubectl apply --wait -f 4-rabbitmq-operator

kubectl wait pods --all -A --for condition=Ready --timeout=150s

kubectl create namespace poc
kubectl label namespace poc istio-injection=enabled

kubectl apply --wait -n poc -f 5-poc
