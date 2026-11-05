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
