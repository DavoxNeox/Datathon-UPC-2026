# Guía de la demo, para hacerla una sola persona

Cómo la haría yo, qué enseñaría y qué tienes que hacer tú, paso a paso. Todo lo de aquí está
ensayado en la placa el 14 de noviembre de 2026 con `main` en `20705e2` o posterior. Los
documentos largos siguen siendo `pitch.md` (guion palabra por palabra en catalán e inglés),
`demo-problems.md` (por qué estos problemas), `runbook.md` (la mañana, en inglés) y
`contingency.md` (qué hacer si algo falla). Esta guía los resume en el orden en que los usarás.
Las letras correctas de los problemas están en `local/respuestas.md`, que no se sube al repo.

## 1. La idea en una frase

Un copiloto de matemáticas que corre entero dentro de un Arduino UNO Q sin red. El modelo
pequeño **no razona**: clasifica, extrae y escribe una frase; quien razona es el alumno, con
una escalera de pistas (problema vecino, estrategia, un paso escrito, una lección) y una matriz
LED que acompaña. La mitad Reason de la nota la cubre `predict.py` con una política medida y
honesta; la mitad Teaching la ve el jurado en 90 segundos de demo.

## 2. Lo que enseñaría, en orden (3 minutos)

| cuándo | qué se ve | qué digo (idea; el texto exacto en `pitch.md`) |
| --- | --- | --- |
| 0:00 | La placa en la mano, la pantalla de inicio en el proyector, la matriz respirando | Esto es la placa, sin Wi-Fi; el portátil solo muestra la página que sirve por USB |
| 0:10 | `Comença` con Mariona1, 6è | La alumna no lo ve claro y pide una pista en vez de arriesgar |
| 0:15 | `Pista`: tarjeta "Un problema semblant" con su figura | El copiloto busca dentro de la placa un problema del mismo tema, un nivel más fácil. Ninguna respuesta, ningún modelo razonando |
| 0:30 | `Pista`: estrategia del tema | Ahora sí responde |
| 0:36 | Letra correcta. En la placa: la letra en grande, el tick, las barras de dominio creciendo | Acierta con pistas: el progreso del tema sube |
| 0:45 | `Continua`; segundo problema (dos cursos más arriba); `Pista`, `Pista` | El diagnóstico sube el nivel; vecino con imagen y estrategia "gira i volteja" |
| 1:00 | Letra equivocada a propósito. Cruz en la placa | Las pistas no le han dicho la respuesta; la corrección llega solo ahora |
| 1:05 | `Pista` después de fallar: un paso escrito a mano; otra vez: la lección | Puede seguir aprendiendo tras fallar: un paso, y luego la idea matemática, sin fórmula ni solución |
| 1:20 | `Menú` → `Vista del professor` | El profesor lo ve todo: progreso por tema y alumno, intervalos, diagnóstico |
| 1:30 | `Quadre de decisions` (desde la vista del profesor) | Cada decisión del proyecto con su medida y su fuente, dentro de la placa |
| 1:40 | De vuelta al alumno; cierre con los números | Ver §5 |

Dos cosas que debe notar el jurado y conviene decir con esas palabras: **el modelo no razona**
(y por qué eso es una virtud en una placa de 4 GB), y **todo corre offline en la placa con
tiempos reales** (cada paso de la demo tarda menos de medio segundo dentro de la placa).

## 3. La noche antes

- Placa, cable USB-C de datos (no de solo carga), cargador del portátil, adaptador al proyector,
  móvil con el vídeo de respaldo (`contingency.md` §9).
- En el portátil: `adb` instalado, suspensión y notificaciones apagadas, zoom del navegador al
  150 % recordado para `127.0.0.1:7002`.
- No hagas `git pull` en la placa la mañana de la demo. El chequeo de la mañana te dice en qué
  commit está.
- Imprime `local/respuestas.md` (las letras) y `one-pager.md` para el jurado.

## 4. La mañana: un comando

Enchufa la placa al portátil por USB-C. Espera dos minutos y medio. Después, desde la carpeta
del repo en el portátil:

```bash
dev/demo_preflight.sh --clean
```

`--clean` borra la base de alumnos de la placa (los alias de los ensayos aparecerían en la vista
del profesor). El chequeo hace, en este orden: USB, los tres servicios y los dos modelos, la app,
las tres páginas por el túnel USB, la matriz LED (mira la placa: 2 segundos encendida entera y
después un tick), las dos cadenas de la demo con sus pistas (eso además calienta el índice, que
la primera `Pista` carga del disco) y deja la placa en la pantalla de inicio. Cada línea es
`ok`, `FAIL` o `note`; un `FAIL` nombra la sección de `contingency.md` que lo resuelve. Si
termina en `READY`, sigue.

Luego, en el navegador, pestañas en este orden y nada más abierto:

1. `http://127.0.0.1:7002/` al 150 %: escribe el alias **Mariona1**, curso **6è de primària
   (nivell 1)**, y **no pulses Comença**. Ese es el primer clic de la demo.
2. `http://127.0.0.1:7002/teacher.html` al 150 %.
3. El vídeo de respaldo, parado en 0:00.

Pantalla completa, barra de marcadores oculta. El terminal queda detrás con el túnel hecho.
La placa, con la matriz hacia el jurado y el cable con holgura. Nadie toca el cable.

## 5. Los clics, uno a uno

Cadena B (Mariona1). Las letras correctas están en `local/respuestas.md`.

1. `Comença`. Aparece el primer problema (tableros y patrones, con figura). En la placa, cuatro
   bloques abajo: las cuatro pistas disponibles.
2. `Pista · 4`. Mientras la placa busca, un punto recorre la fila de abajo de la matriz. Llega
   la tarjeta "Un problema semblant" con la figura del vecino. Señálala; no la leas entera.
3. `Pista · 3`. Tarjeta de estrategia del tema.
4. La letra correcta del problema 1. En la placa: la letra en grande, el tick, y a los tres
   segundos las barras de dominio creciendo. Da tiempo a que se vea.
5. `Continua`. Segundo problema (razonamiento espacial, con figura).
6. `Pista · 4`, `Pista · 3`.
7. Una letra equivocada a propósito. Cruz en la placa. El veredicto se queda en pantalla.
8. `Pista · 2`: un paso escrito a mano. `Pista · 1`: la lección (la idea matemática, sin
   fórmula ni solución). La quinta pulsación se rechaza; no la hagas en escena.
9. `Menú` (icono arriba a la izquierda) → `Vista del professor`. En la pestaña 2 recarga
   (`Cmd+R`) para que salga Mariona1; señala el progreso por tema y el diagnóstico con sus n.
10. `Quadre de decisions`, enlace arriba de la vista del profesor: deja ver dos paneles
    (el modelo solo, 21,7 %; la escalera y los tiempos) y vuelve.
11. Pestaña 1 y cierre con los números (§6).

Si sobra tiempo o el jurado quiere tocar: cualquier alias y curso valen; la cadena A
(`Guillem`, 1r d'ESO) es texto puro y enseña que el vecino funciona también sin figura.

## 6. Los números, honestos (40 segundos)

Memoriza estas cifras; están en `docs/results-A.md` y en el cuadro de decisiones.

| qué | cifra |
| --- | --- |
| el modelo eligiendo la letra, 281 problemas de validación | 21,7 % (opciones v1, no repetido), como el azar; siempre D da 22,8 % con las opciones v2 (23,1 % con v1) |
| política entregada (solvers, valor central, D), validación, inglés | 70/281 = 24,9 % (siempre D 64/281 = 22,8 %; v1: 77 = 27,4 %) |
| la misma política, validación, catalán | 70/281 = 24,9 % (v1: 73) |
| la misma política en la placa, 562 problemas en dos idiomas | 140/562 = 24,9 %, frente a 130 de siempre D (v1: 150 = 26,7 %); menos de un segundo por problema |
| razonamiento breve del propio modelo, medido y apagado | +2 puntos esperados, cola bajo cero del 6 %, 21 s por problema |
| velocidad de la placa | 11,4 tokens/s leyendo, 5,6 escribiendo |
| cada paso de la demo dentro de la placa | menos de 0,5 s; una pista del modelo, 10 a 16 s |

Con el OCR v2 de las opciones (15 nov), la ganancia de la regla sobre siempre D en la placa
bajó de +20 (v1) a +10; si preguntan, es un prior sobre los distractores, no razonamiento.

La frase que lo resume: "el 0,8B no sabe resolver problemas Cangur, así que el copiloto no le
deja intentarlo: enseña, y la única ganancia de Reason que entregamos es un prior sobre cómo se
construyen los distractores".

## 7. La parte Reason, si piden verla

En el portátil, por el túnel USB, o en la propia placa:

```bash
adb shell 'cd /home/arduino/Datathon-UPC-2026 && python3 predict.py --input data/sample_problems.jsonl --output /tmp/demo.csv --fresh && cat /tmp/demo.csv'
```

Cinco problemas en menos de un segundo, una fila por problema con letra, segundos y estado.
Para el examen: el mismo comando con el fichero de la organización; si la placa se reinicia a
mitad, se relanza igual y continúa donde estaba (`--fresh` solo para empezar de cero). La
política del examen y la lista de condiciones para encender el razonamiento breve están en
`runbook.md`, sección "El examen".

## 8. Si algo falla (resumen; detalle en `contingency.md`)

| síntoma | qué haces en menos de 15 s | qué dices |
| --- | --- | --- |
| la página no carga | `adb forward tcp:7002 tcp:7000` otra vez; recarga | "La página la sirve la placa por el cable; la vuelvo a enlazar" |
| sale otro problema tras `Comença` | sigue igual: `Pista`, `Pista`, una letra; la historia es la misma | di el tema que aparece bajo el problema |
| una pista tarda más de 10 s | en catalán no se usa el modelo: la app está atascada; a los 15 s, vídeo | "Mientras la placa busca el vecino, compara embeddings de todo el tema" |
| la matriz no cambia | nada que arreglar en escena: `Menú` muestra el mismo cuadro dibujado en la página | "La matriz de la página es el mismo cuadro que envía a la placa" |
| la placa no arranca o `adb` no la ve | cable de repuesto, otro puerto; si pasa de 15 s, vídeo | "Os enseño la grabación de esta mañana con esta misma placa" |

Regla: la narración no se para nunca; a los 15 segundos de cualquier fallo, el vídeo.

## 9. Después

```bash
curl -s http://127.0.0.1:7002/api/reset > /dev/null
```

Deja la placa encendida para las preguntas. Si hay un segundo pase, vuelve a §4 con `--clean`.
Al final del día: `adb shell sudo poweroff`.
