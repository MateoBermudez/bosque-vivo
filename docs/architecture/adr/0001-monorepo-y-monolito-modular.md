# ADR 0001: Monorepo y monolito modular

- Estado: aceptada

## Contexto
Equipo de cuatro personas, un solo computador de ejecución y un plazo de ocho semanas.

## Decisión
Un único repositorio con una aplicación Python modular (`backend/`) y un panel (`panel/`). Los módulos tienen fronteras claras: `api → servicios → db`.

## Consecuencias
- Un solo CI, un solo versionado y cambios atómicos entre módulos.
- Sin costo operativo de microservicios ni colas externas.
- Si un módulo creciera, puede extraerse porque solo se comunica por su interfaz pública.
