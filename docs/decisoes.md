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

## Mundo aberto — ajustes (06/11/2026)
- Carro em escala do mapa no mundo aberto (CARW=.62; o 1.5x continua só na pista Shibuya).
- Colisão em 4 camadas de altura (rampas, pontes, escadas): o carro sobe/desce pela camada mais alta que alcança (degrau 0,14); cai com gravidade; câmera acompanha a inclinação.
- Mapa inteiro fica na memória (nada descarrega); carrega do mais perto pro mais longe, com barra de progresso; draw distance 6,5 -> 12 unidades (~144 m) com corte por bloco. Posições em uint16 + uniforms (menos memória).
- Buracos: telhados gerados em todos os prédios (altura da parede mais próxima) + chão escuro sob o mapa todo. Atlas ganhou um slot de cor para isso.

## Mundo aberto — física, hitbox, volante e trânsito (07/11/2026)
- Física: pneu com limite de aderência (subesterço, derrapagem, freio de mão solta a traseira), giro com inércia, ré segurando o freio parado, batida com hitbox (contorno de 16 pontos) e deslize em paredes; chão suave sem "voar" (cai só em degrau grande).
- Chão: alturas interpoladas por triângulo (camadas separadas por 0,03); obstáculos em grade de 0,1 un (postes, caixas, grades); sinais pendurados não bloqueiam. Faces de rua invertidas e frestas pequenas viram chão.
- Botão de volante na tela: arrasta e gira ±95° (190° no total), volta ao centro sozinho; alterna com as setas pelo ícone do volante.
- Trânsito (trafego.js): ruas extraídas do mapa (ferramentas/mapa/extrair_vias.py -> mapa/vias.json); carros 3D simples seguem a mão direita, limite por tipo de via (rua estreita 30, rua 40, avenida 55, via rápida 80 km/h), distância do carro da frente (IDM), semáforos com ciclo de 36 s nos cruzamentos (luz vermelha/amarela/verde desenhada), curvas mais lentas. Colisão com o jogador.
- Pendências conhecidas: faixas ficam no centro do corredor do chão (nem sempre = linha amarela do mapa); jogador não é multado por furar sinal; luz global/dia-noite e luz nos prédios ficam para depois.

## 07/11/2026 (tarde) — escala do mundo, volante de 1,5 volta, trânsito refeito
- Escala: 1 unidade do mapa = 24 m (antes 12). Carro 4,3 m = 0,18 un. Prédios agora ficam bem maiores que o carro (andares ≈ metade da altura do carro antes; agora proporcional). Câmeras, hitbox, passo de degrau, faróis e plano próximo da câmera reescalados.
- Colisão mais fina: grade de altura com célula 0,1 (2,4 m) e obstáculos com célula 0,04 (~1 m), guardados em 1 bit por célula (obs.wav = 1,5 MB).
- Volante: ±270° (1,5 volta), tanto no botão de volante da tela quanto no volante do cockpit.
- Trânsito: faixas validadas contra paredes/obstáculos/degraus (faixa que não passa no teste é descartada ou aproximada do centro), conexões em curva dentro dos cruzamentos (sem esquerda cruzando fluxo contrário), sem retorno em beco, carros param no fim de rua sem saída, cruzamentos vizinhos compartilham o ciclo do semáforo (verde 11 s / amarelo 3 s / 4 s tudo vermelho), semáforo na calçada (~4,3 m), carros do tamanho real.
- Teste automático (Playwright, sem renderizar): 3 min de trânsito simulado + 100 percursos do jogador pelas faixas. Resultado final: ~1 em 100 percursos com toque; carros dentro de parede ~1,7% das amostras (encostão de quina), sobreposição entre carros ~0,04%.
- Ferramentas: extrair_vias.py agora endireita ruas (corda ≤ 0,12) e usa parâmetros em células na nova escala.

## 08/11/2026 — iluminação, colisão com rebote, máscara de estrada, trânsito (v6)
- Colisão: batida agora rebate (BOUNCE .6) e o carro volta pra trás em vez de agarrar; degrau de subida .035 (rampas mais suaves); máscara de estrada (mapa/road.wav, gerada por ferramentas/mapa/mascara_estrada.py) impede entrar onde não há rua.
- Camadas de altura (3) mantidas como chão do carro; queda em rampa não foi reproduzida em teste, só mitigada.
- Luzes do carro: painel (I), teto (O), faróis/lanternas (T), todas liga/desliga por botão e tecla.
- Dia/noite: sol em arco leste→meio→oeste, lua à noite, céu/neblina por hora, janelas acesas à noite, sombras por heightfield (mapa/top.wav, ferramentas/mapa/heightfield_sombra.py; aproximadas, respeitam área iluminada/sombra).
- Qualidade adaptativa: desliga sombras / encurta distância / reduz carros se o FPS cair.
- Trânsito: postes só na calçada, carros menores, cedência preditiva, rede de segurança (despawn de carro preso/sobreposto).
- Limites conhecidos: ~15–25% dos carros encostam em quina; sobreposição residual no cruzamento complexo (x −79..−66, z 93..106); chuva ainda ligada por padrão ao meio-dia; tiles.json precisa regenerar TOP após rodar o conversor.

## 08/11/2026 (noite) — v7: liberdade do jogador, muretas, buracos, a pé, minimapa
- Jogador livre: removida a máscara de estrada da colisão do carro (só vale para o trânsito). Paredes agora = prédio/objeto real ou borda de viaduto (queda > ~2 m, `h < gy-.09`).
- Muretas: ferramentas/mapa/preencher_buracos.py acha bordas de pistas elevadas (>= 5 células seguidas) e gera tiles estáticos f_*.wav (concreto, 1,2 m de altura). Rodar DEPOIS do conversor/máscara/heightfield.
- Buracos: o mesmo script preenche chão vazio de baixo (rio, terrenos, faixa de ~100 m em volta do mapa) com grama no atlas (slot 63) e marca o grid como dirigível (.003).
- Dia/noite automático: 24 h em ~16 min reais; relógio no HUD.
- Trânsito: nasce proporcional ao comprimento das faixas (espalha), no máximo 2 carros por ~60 m; cada carro tem destino à frente e escolhe a conexão que o aproxima (menos giro no quarteirão).
- A pé (tecla F / botão de pessoa): desce do carro parado (< 12 km/h), anda (seta/botão; N corre), volta ao carro perto dele. Boneco de blocos provisório; carro fica estacionado e o trânsito o enxerga.
- Minimapa (tecla M / botão de pino): gira com o carro, ruas/grama/prédios, carros do trânsito em vermelho, carro estacionado em laranja; botão alterna 3 zoom e desliga.
- Pendências: sprites dos NPCs (dele), túneis, postos, mapa mais longo (a combinar), prédios onde falta (a combinar).

## Rodada de qualidade (09/11) - texturas
- Causa dos "buracos/vazios": (1) 79 faces de chao usavam paginas de textura 128/158 que nao existem no zip do mapa (ficavam cinza); (2) ~48 mil vertices de chao usavam o texel azul-acinzentado criado para telhados (retangulos cinza em pracas).
- Correcao: ferramentas/mapa/corrigir_texturas.py (rodar depois de preencher_buracos.py) remapeia essas faces para concreto/grama ja existentes no atlas. Nenhuma imagem original foi alterada.
- Pendente desta rodada: carro em alta resolucao (rig-hires), zoom mais proximo, cores mais vivas/brilho, trecho de expansao do mapa, prompts de sprites.
