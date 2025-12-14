# Guía rápida de Git (para el equipo)

## 1. Configuración inicial (solo una vez)

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```
## 2. Clonar el repositorio (primera vez)
```bash
git clone https://github.com/TU_USUARIO/mmi-helipuertos-2025.git
cd mmi-helipuertos-2025
Reemplaza <TU_USUARIO> por tu usuario de GitHub.
```
Si prefieres SSH:
```bash
git clone git@github.com:<TU_USUARIO>/mmi-helipuertos-2025.git
```
## 3. Guardar cambios (flujo básico)
Ver el estado:
```bash
git status
```
Añadir cambios (stage):
```bash
git add archivo.py       # un archivo específico
git add .                # todos los cambios (con cuidado)
```
Confirmar cambios (commit):
```bash
git commit -m "descripción corta del cambio"
```
Subir al repo remoto:
```bash
git push origin NOMBRE_RAMA
```
## 4. Trabajar con ramas
Crear y cambiar a una nueva rama:
```bash
git checkout -b feature/nombre-tarea
o:
git switch -c feature/nombre-tarea
```
Subir la rama al remoto:
```bash
git push -u origin feature/nombre-tarea
```
## 5. Actualizar con los últimos cambios de main
```bash
git checkout main
git pull origin main
git checkout feature/nombre-tarea
git merge main
```
## 6. Pull Request (PR) en GitHub
Empuja tu rama:
```bash
git push origin feature/nombre-tarea
```
En GitHub → botón Compare & pull request.
Escribe título y descripción clara.
Asigna revisor/es.
Tras aprobación → merge a main.

## 7. Borrar ramas después de merge
```bash
git branch -d feature/nombre-tarea              # borrar local
git push origin --delete feature/nombre-tarea   # borrar remoto
```
## 8. Comandos útiles
```bash
git log --oneline    # historial resumido
git diff             # ver diferencias antes de hacer add
git fetch origin     # traer ramas sin hacer merge
```
## 9. Buenas prácticas
Una rama por tarea: feature/, fix/, docs/.

Commits pequeños y descriptivos.

No subir datos pesados a GitHub → usad data/README.md con enlaces si hace falta.

Subid el archivo environment.yml para que todos puedan recrear el entorno con:
```
conda env create -f environment.yml
conda activate mmi-helipuertos-2025
```
