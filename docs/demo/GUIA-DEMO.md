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

Dos cosas que debe notar el jurado y conviene decir con esas palabras: **el modelo pequeño no razona en texto**
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

Memoriza estas cifras; están en `docs/reason-experiments.md` (set de práctica, "Experiment 8" y
"The exam setting on the board"), en `docs/results-A.md` y en el cuadro de decisiones.

| qué | cifra |
| --- | --- |
| set de práctica de la organización (100 filas, 20 por letra), cualquier letra fija | 20/100 |
| la política de M3Kang (valor central, si no D) en ese set | 16/100: las opciones numéricas vienen en orden, el valor central es siempre C |
| razonamiento breve del modelo, en la placa, 100 filas | 27/100, 33 s por problema |
| política del examen (programa Python escrito por el modelo, traducción previa al inglés, intérprete restringido, razonamiento breve de respaldo), portátil | 38/100 |
| la misma política en la placa, tiempos reales, 20 filas | 8 de 20, frente a 5 del razonamiento breve en las mismas filas; muestra pequeña |
| tiempo de esa corrida | 29 s de media, 49 s el peor, unos 10 minutos los 20 problemas |
| historia, M3Kang: el modelo eligiendo la letra | 21,7 % (opciones v1, no repetido), como el azar |
| historia, M3Kang: política del valor central | 70/281 = 24,9 % en validación, 140/562 = 24,9 % en la placa (siempre D 130) |
| velocidad de la placa | 11,4 tokens/s leyendo, 5,6 escribiendo |
| cada paso de la demo dentro de la placa | menos de 0,5 s; una pista del modelo, 10 a 16 s |

El mensaje: el modelo pequeño sigue sin razonar en texto; lo que funciona es hacerle escribir un
programa corto y que la placa lo ejecute, exacto cuando acierta. Si preguntan por la regla del
valor central: es un prior sobre cómo se construyen los distractores de M3Kang, no razonamiento, y
en el set de práctica (letras equilibradas) baja a 16/100.

La frase que lo resume: "el 0,8B no sabe razonar en texto, así que el copiloto no le deja
intentarlo delante del alumno: enseña; y para el examen le hacemos escribir un programa que la
placa ejecuta".

## 7. La parte Reason y el examen

Si el jurado quiere ver `predict.py`, en el portátil por el túnel USB:

```bash
adb shell 'cd /home/arduino/Datathon-UPC-2026 && THINK_LEVELS= python3 predict.py --input data/sample_problems.jsonl --output /tmp/demo.csv --fresh && cat /tmp/demo.csv'
```

Cinco problemas en menos de un segundo con la política de M3Kang (la variable vacía la fuerza),
una fila por problema con letra, segundos y estado.

El examen lo ejecuta la organización con nuestro `predict.py` en la placa tras el last call de
las 12:00: 20 problemas, un idioma cada uno, 4 con figura, 60 s por problema. La política que
sale en `main` es el programa en Python que escribe el modelo (con traducción previa al inglés,
ejecutado en la placa en un intérprete restringido) y, de respaldo, el razonamiento breve: 38/100
en el set de práctica en el portátil; en la placa, 8 de 20 frente a 5 del razonamiento breve,
29 s de media, unos 10 minutos los 20. El procedimiento completo, preparado y ensayado con su set de práctica, está en
`runbook.md`, sección 11: preparar el parquet en el portátil con el entorno de OCR, copiar a la
placa, ejecutar, comprobar una fila por problema. Si la placa se reinicia a mitad, se relanza el
mismo comando y continúa donde estaba.

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
