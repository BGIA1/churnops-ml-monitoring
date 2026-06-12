# Arquitectura

ChurnOps separa la orquestación de las interfaces. `service.py` contiene los casos de uso y es
consumido por Typer, FastAPI, las pruebas y el demo. El generador y la validación no dependen
de sklearn; el registry controla persistencia y aliases; monitoreo usa el mismo contrato de
features que entrenamiento e inferencia.

El mapeo cloud propuesto es FastAPI en Cloud Run, operaciones batch en Cloud Run Jobs,
artefactos en Cloud Storage, imágenes en Artifact Registry, secretos en Secret Manager y
telemetría en Cloud Logging/Monitoring.

