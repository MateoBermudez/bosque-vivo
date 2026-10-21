# ADR 0002: Ejecución 100 % local, sin Docker ni máquinas virtuales

- Estado: aceptada

## Contexto
La instancia oficial corre en un PC con Windows 11. Docker en Windows usa WSL2/Hyper-V, que es una máquina virtual.

## Decisión
Todo corre como procesos normales: API, panel y, solo cuando hace falta WhatsApp, un túnel. `scripts/dev.ps1` los arranca juntos.

## Consecuencias
- El PC es el único servidor: debe estar encendido y sin suspensión durante el piloto.
- Se evitan dependencias que exijan librerías del sistema (WeasyPrint, Redis, Celery).
