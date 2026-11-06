# Decisões do Samuel
- Câmera: por trás do carro (az 0), podendo girar 360°.
- Carro: Honda hatch laranja widebody. Roda oficial: bronze 7 raios. Emblema da grade: SB1. Faixa lateral amarela quadriculada com HONDA: mantida.
- Autorizou corrigir incoerências entre ângulos e criar os ângulos que faltarem.

# Pendências
- Frames intermediários (a cada 22,5°) para o giro ficar fluido: precisam ser gerados na mesma ferramenta de arte; ver docs/pedidos-intermediarios.md quando existir.
- Pista, personagem e cenário: aguardando referências.

## Fisica do carro (2026-11-05)
- Rodas recortadas da arte oficial (traseira, traseira 3/4 direita e esquerda) por `ferramentas/arte2d/separar_rodas.py`: corpo com buraco + "poco" escuro + pneu/roda de cada roda + disco da roda desentortado (gira em tempo real). Pecas em alta resolucao em `arte/carro-honda-laranja/rig-hires/`, na escala do jogo em `demos/corrida-shibuya/img/rig/`.
- Fisica (secao FISICA DO CARRO no index.html, sem depender de canvas, portavel para Godot/Unity): modelo de 3 graus de liberdade (altura, arfagem, rolagem), mola+amortecedor por roda, transferencia de carga (freada/aceleracao/curva), meio-fio, calcada, lombadas, giro da roda = v/raio (com borrao em alta), respingos de agua nas rodas de tras.
- Velocidade maxima 180 km/h = corte de giro (7.700 rpm): limitador + pipocos aleatorios.

## Drift e efeito de giro (2026-11-05)
- Derrapagem: segurar a direcao por ~0,8 s acima de ~50% da velocidade faz o carro escorregar (slip); mostra a vista LATERAL (arte oficial 90/270 com rodas recortadas), fumaca nas rodas de tras, perde velocidade e desliza de lado. Soltar ou contra-esterçar recupera.
- Vista de tras: a banda de rodagem do pneu "rola" para baixo seguindo o giro (borrao em alta velocidade).
- Camera de primeira pessoa: aguardando a foto do interior enviada pelo Samuel.

## Luzes, escapamento e mais fisica (2026-11-05)
- Botao/tecla de drift (freio de mao, Espaco) alem da regra automatica (mantida).
- Faróis iluminando a pista, lanternas e luz de freio, setas (automaticas ao esterçar + pisca-alerta), rastro de luz vermelho das lanternas, brilho aditivo.
- Escapamento: fumaca, labareda nos pipocos, carro treme com o motor ligado.
- Fisica: inercia lateral (peso), aerodinamica abaixa o carro com a velocidade, torque do motor rola a carroceria, mais afundar na freada.

## Cockpit (primeira pessoa)
- Camadas derivadas da foto interior_01.jpg (original intacto) por `ferramentas/arte2d/preparar_cockpit.py`: fundo com buracos (para-brisa, janelas, retrovisores), volante sem mãos, luvas e antebraços separados.
- Para-brisa funcional: pista ao vivo pelo vidro, gotas de chuva, limpador (botão FAN / tecla Q), desembaçador, névoa interna.
- Volante com giro total de 190° (±95°), mola/amortecedor, contra-esterço no drift, treme em buracos. Direção mais lenta na cabine.
- Balanço da cabine (curva, aceleração, buracos); antebraços esticam até as luvas; mão direita solta o volante no freio de mão.
- Painel: ponteiro de velocidade (mostrador só vai até 140) e de rotação (x100), setas verdes, luz vermelha do freio de mão, rádio FM (sem áudio até ele enviar músicas), HEAT/FAN/HEAT = desembaçar/limpador/farol.
- Nitro: botão ou tecla N/Shift; tanque gasta e recarrega; passa de 180 km/h só enquanto ativo.
- Retrovisores: reflexo espelhado da cena (não é a visão real de trás).

## Ajustes pós-cockpit (06/11)
- Volante/braços não tremem mais parado (integração estável + tremor só em movimento).
- Câmbio: automático ou manual (botões Marcha −/+ ou teclas Z/E); em manual cada marcha tem seu limite de velocidade, aceleração própria e freio-motor; mão direita vai ao câmbio.
- Anti-lag (liga/desliga): ao soltar o acelerador em rotação alta, a rotação cai devagar com pipocos e labareda; também nas trocas.
- Câmera de fora mais perto: carro 1,5x maior.
- Linhas de velocidade em ambas as câmeras, crescem com a velocidade.

## Controles em ícones e efeito de velocidade (06/11)
- Layout sem rolagem (cabe na tela em pé e deitado), botões só com ícones, polegares embaixo (esquerda: virar e marcha; direita: freio, acelerar, freio de mão, nitro); ícones pequenos no topo (câmera 1ª pessoa, faróis, pisca, limpador, desembaçar, câmbio M, anti-lag, filtro, chuva, som).
- Alavanca de câmbio desenhada no cockpit (padrão em H, mostra a marcha); a mão direita vai até ela.
- Acima de 100 km/h: tremor de câmera, zoom (FOV), embaçado radial nas bordas e linhas de velocidade. Protótipo do CapCut dele fica para depois.

## Câmbio: alavanca grande e mão fluida (06/11)
- Alavanca maior, com boot, haste e bola com o número da marcha; move no padrão em H.
- Mão direita: sai do volante em arco, vai até a alavanca, segura enquanto troca, volta ao volante; antebraço estica junto.
- Aro do volante sob as luvas reconstruído copiando o próprio aro (sem borrão) para a mão poder sair.
- Grade do câmbio em H: 1ª/3ª/5ª puxam a alavanca para frente (cima na tela), 2ª/4ª para trás (baixo); troca de coluna passa pelo ponto morto (centro). A mão acompanha a bola. A luva existente já é um punho fechado (dedos curvados), reaproveitada para segurar a alavanca.
- Câmbio manual: a troca só entra quando a mão chega na alavanca (cockpit) ou ~0,2 s depois (câmera de fora); embreagem pisada (sem tração) enquanto a mão vai; pedidos seguidos são enfileirados.
- Próximo: mapa aberto (mundo aberto) que ele vai enviar; formatos a combinar (ver conversa).

## Mundo aberto — mapa Chicago (Driver 2) (06/11)
- Demo nova: `demos/mundo-aberto` (a do Shibuya continua intacta). Mesmo jogo, mesmas câmeras (atrás e cockpit), mesmo carro 2D e filtro pixel-art; só a pista mudou para o mapa 3D.
- Conversão: `ferramentas/mapa/converter_mapa.py` (OBJ 108 MB → 120 blocos, atlas 2048, grade de colisão). Mapa só para protótipo interno; crédito: pancakesbassoondonut (CC BY).
- Renderização em WebGL puro (`world3d.js`, sem bibliotecas), blocos carregados por proximidade, neblina/noite/farol no shader.
- Física no mapa: rumo + posição, colisão por altura do chão (prédio/vazio = parede), escorregar em parede, batida.
- Futuro: trocar texturas dos prédios por fotos de Tóquio (mesmas áreas de UV do atlas).
