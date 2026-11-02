# Pedidos para gerar os frames intermediários (a cada 22,5°)

Usar na mesma ferramenta que gerou as imagens do carro, anexando como referência as imagens de `arte/carro-honda-laranja/ajustados/`.

Texto base (colar em todos):
"Mesmo carro das imagens de referência: Honda hatch laranja widebody com rebites, rodas bronze de 7 raios, aerofólio e difusor pretos, escapamento duplo, emblema SB1 na grade, faixa lateral amarela quadriculada com HONDA. Estilo pixel-art com contorno preto fino, sombreado em cel e leve textura de tinta desgastada. Fundo branco liso, sombra no chão, carro inteiro enquadrado, mesma altura e mesma linha do chão das referências. Câmera na altura do carro, levemente acima."

Ângulo (acrescentar ao texto base). O azimute 0° é a câmera atrás do carro; a câmera gira para o lado direito do carro:
- 22,5°: "visto de trás, girado 22,5° para o lado direito do carro (quase de trás, mostrando um pouco da lateral direita)"
- 67,5°: "visto de trás e do lado direito, girado 67,5° (mais lateral que traseira)"
- 112,5°: "visto do lado direito e um pouco da frente, 112,5°"
- 157,5°: "visto de frente e do lado direito, 157,5° (quase de frente)"
- 202,5°: "visto de frente e do lado esquerdo, 202,5° (quase de frente)"
- 247,5°: "visto do lado esquerdo e um pouco da frente, 247,5°"
- 292,5°: "visto de trás e do lado esquerdo, 292,5° (mais lateral que traseira)"
- 337,5°: "visto de trás, girado 22,5° para o lado esquerdo (quase de trás)"

Depois de gerar: enviar para o Claude, que confere consistência (roda, emblema, faixa), recorta o fundo, alinha escala e chão e inclui no giro (16 direções).

## Referência de pose (do vídeo novo)
Pasta: `arte/carro-honda-laranja/referencias-de-pose/` (um arquivo por ângulo + `folha-de-poses.png`).
Anexar, junto com as imagens de `ajustados/`, o `pose_<ângulo>.png` do ângulo pedido e acrescentar ao pedido:
"Copiar SOMENTE a pose e o ângulo da imagem de pose. Ignorar o estilo 3D realista, o fundo cinza, as rodas, os textos (PRO TURBO RB26, TUB26), a faixa lateral preta e a barra frontal. O visual do carro vem das imagens em pixel-art com contorno."
Observação: `pose_112.5` e `pose_157.5` são o espelho de 247.5 e 202.5 (o vídeo não chega a esses ângulos), então os textos aparecem invertidos; ignorar.
