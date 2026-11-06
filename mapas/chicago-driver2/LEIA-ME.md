# Mapa Chicago (Driver 2, PSX) — protótipo
- Origem: Sketchfab, "Chicago - full map from Driver 2 (PSX)" por pancakesbassoondonut, licença CC Attribution (dar crédito ao autor).
- Uso: SOMENTE protótipo interno do Samuel (não será publicado nem vendido). O mapa vem de um jogo comercial.
- `original/` guarda o zip enviado por ele, sem alterações. O modelo cru (obj de 108 MB) não é commitado: sai de dentro do zip.
- Conversão: `ferramentas/mapa/converter_mapa.py` gera blocos leves + atlas + grade de colisão em `demos/mundo-aberto/mapa/`.
- Futuro: trocar as texturas (PAGE_*.png, são atlas de 256x256) por fotos de prédios de Tóquio mantendo as mesmas áreas de UV.
