# Audio do motor VTEC

Originais do Samuel (intactos) em `referencias/`:
- `honda-vtec-flyby.mp3` — carro passando em alta rotacao (corte de giro, troca de marcha, reducao)
- `loud-civic-vtec.mp3` — arrancada completa de um Civic VTEC, da marcha lenta ao corte de giro (23 s)

O jogo (`demos/corrida-shibuya/audio/*.wav`) usa SO cortes do `loud-civic-vtec.mp3`, sem sintese:

| clipe | trecho original | uso |
|---|---|---|
| s0 ... s7 | 8 fatias de rotacao fixa (~1,1 s cada, centros em 4,2 / 5,6 / 7,1 / 8,8 / 10,8 / 13,0 / 16,0 / 19,8 s) | loops; o jogo mistura as 2 vizinhas conforme a rpm e ajusta o tom ate ~15% |
| idle | 21,4–22,95 s | marcha lenta (loop) |
| cut | 20,78–21,5 s | tirou o pe em alta rotacao (queda de giro) |

Mixagem no jogo: sem acelerar = som mais abafado e baixo (freio-motor); troca de marcha = corte rapido do som (embreagem);
limitador = som pulsando a 8 Hz no corte de 7.700 rpm.

## Camada de alta rotacao (flyby)
Acima de ~6.400 rpm entra o `honda-vtec-flyby.mp3` (cortes `f_*`): f_acc (motor forte em alta), f_lim (corte de giro, no limite),
f_shift (marcha trocada, em toda troca), f_blip (reducao), f_pop (tirou o pe em alta: pipocos).
