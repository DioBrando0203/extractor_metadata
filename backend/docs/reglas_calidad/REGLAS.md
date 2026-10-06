# Reglas de calidad (backend)

- QB-01: todo cambio de comportamiento trae una prueba que falla sin el cambio.
- QB-02: fixtures sólo sintéticos: `tests/msg_factory.py` y archivos generados en la prueba (Pillow, pypdf, zipfile, ezdxf).
- QB-03: cada extractor o lector de formato se prueba con un archivo válido y otro corrupto o truncado.
- QB-04: las pruebas de rutas verifican que el directorio temporal queda vacío (fixture `client`).
- QB-05: no se bajan límites de seguridad para que pase un archivo concreto; se documenta en bloqueos.
- QB-06: la cobertura por formato se declara honestamente en `REQUERIMIENTOS.md` ("parcial" cuando aplique).
- QB-07: refactorizaciones sin cambio de comportamiento se validan con la suite completa sin modificar aserciones.
- QB-08: cambios en worker o límites exigen repetir las pruebas de timeout y de MSG grande.
- QB-09: resultados en `calidad/RESULTADOS.md` sólo de ejecuciones reales, con entorno y hora de Lima.
