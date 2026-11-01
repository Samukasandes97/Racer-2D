# Honda laranja — conjunto de ângulos

Originais do Samuel (intocados): ../referencias/carro-honda-laranja/originais/
Ângulos recebidos (intocados): oficiais/
Versão FINAL para o jogo (usar esta): ajustados/
  traseira-3-4-direita / esquerda  (sem alteração)
  frente-3-4-esquerda              (sem alteração)
  frente-3-4-direita               (emblema TB2 -> SB1)
  lateral-direita / esquerda       (roda de 9 raios -> bronze 7 raios; esquerda = espelho, textos legíveis)
  topo                             (vidro traseiro liso no lugar das ripas; "HONDA" invertido removido)
Rascunhos do Claude (descartados): rascunhos-claude/

Decisões do Samuel: roda oficial = bronze 7 raios; emblema = SB1; faixa lateral amarela quadriculada com HONDA = mantida.
Observação: as duas laterais recebidas olhavam para a direita; a esquerda foi gerada por espelho.

Rotação (câmera de trás girando 360°): sprites/
  png/car_<azimute>_<nome>.png  8 direções, fundo transparente, mesma escala e chão (2100x800)
  spritesheet_8dir.png          as 8 em uma faixa
  manifesto.json                azimute -> arquivo (para Godot/Unity ler)
Demo HTML: ../../demos/giro-camera/index.html
Ferramentas: ../../ferramentas/arte2d/montar_rotacao.py
