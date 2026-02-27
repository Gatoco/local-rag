#!/bin/bash

echo "=== Estado del repositorio ==="
git status

echo ""
echo "=== Agregando archivos ==="
git add -A

echo ""
echo "=== Creando commit ==="
git commit -m "Initial commit: RAG system with hexagonal architecture"

echo ""
echo "=== Verificando remoto ==="
git remote -v

echo ""
echo "=== Subiendo a GitHub ==="
git push -u origin master

echo ""
echo "=== Verificando resultado ==="
git branch -vv
