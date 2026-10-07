# CentralGest · Compras com IA · spot de TV de 20s

Motion gráfico feito em [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP) para anúncio de TV.

- **Master:** `renders/centralgest-ia-compras-TV-1080p25-20s.mp4`
- **Formato:** 1920×1080 · 16:9 · 25 fps progressivo (padrão PAL, usado pelas TVs portuguesas) · H.264 High · BT.709 · gama limitada (broadcast-legal)
- **Duração:** 20,00 s (500 frames)
- **Áudio:** faixa estéreo 48 kHz **em silêncio**, que a produtora substitui pela locução e pela música
- **Área de segurança:** todos os textos ficam dentro dos 90% centrais do ecrã (graphics-safe da EBU)

## Cor: azul #0C5FFB ou branco?

**Recomendação: azul #0C5FFB como cor dominante, com um arranque em branco nos primeiros 3 segundos.**

| | Fundo azul #0C5FFB | Fundo branco |
|---|---|---|
| Destaque no intervalo publicitário | Alto. Cor saturada e própria da marca, que se distingue da maioria dos spots (escuros ou com imagem real) | Alto no primeiro segundo (flash de luz), mas cansa e encandeia numa sala escura |
| Reconhecimento da marca | Máximo. Ao fim de 20s fica "o anúncio azul da CentralGest" | Baixo. O branco é genérico |
| Leitura na TV | Texto branco sobre #0C5FFB tem contraste de 5,2:1, ótimo para títulos grandes | Bom, mas os cartões brancos da interface perdem-se no fundo |
| Cartões da interface (fatura, software) | Os cartões brancos destacam-se muito sobre o azul | Precisam de sombra pesada para se separarem do fundo |

A narrativa usa as duas cores: o **problema** (registar à mão) aparece num fundo claro de "papel", e quando **a IA entra** um círculo azul toma conta do ecrã. Essa mudança de cor aos 3s funciona como um segundo gancho visual e mantém a pessoa a ver. A partir daí fica tudo no azul da marca até ao end card.

## Guião da locução (adaptado) e tempos

Correções ao texto original:

- "registrar" → **"registar"** (forma de Portugal; a 1ª frase já usa "regista")
- "lê linha a linha" → **"Lê linha a linha e preenche…"** (maiúscula no início)
- "Basta um clique, e está pronto!" → **"Basta um clique e está pronto!"** (sem vírgula antes do "e")
- "CentralGest, software de gestão…" → **"CentralGest, o software de gestão…"** (soa mais natural lido em voz alta)

| Tempo | Locução | No ecrã |
|---|---|---|
| 0,3 – 2,8s | Ainda regista faturas de compra à mão? | Fundo claro, pilha de faturas a cair, contador "47 faturas por lançar", campo a ser escrito devagar |
| 3,2 – 6,0s | Agora, a IA do CentralGest faz isso por si. | Wipe azul a partir da ✦ da IA, título com "por si." destacado |
| 6,3 – 9,2s | Lê linha a linha e preenche tudo no software. | A fatura é lida por um feixe; cada bloco "voa" para o formulário do CentralGest |
| 9,5 – 11,5s | Basta um clique e está pronto! | Zoom no botão, o cursor clica, "✓ Compra registada" |
| 12,1 – 15,5s | Menos tempo a registar faturas. Mais tempo para o seu negócio. | "registar faturas" riscado; "o seu negócio." destacado |
| 15,9 – 19,4s | CentralGest, o software de gestão ideal para empresas e contabilistas. | Logótipo, assinatura e centralgestcloud.com |

São cerca de 50 palavras em ~17s, um ritmo de anúncio enérgico mas confortável. O ficheiro `vo-guia-locucao.srt` tem estes tempos para o locutor e para a montagem. Se a gravação ficar mais longa, o mais fácil é cortar "de compra" na 1ª frase.

## Editar e renderizar

```bash
npm run preview   # abre o Studio para editar textos e tempos
npm run check     # lint + validação + contraste
npm run render    # render 25 fps (gera o raw em renders/)
```

O master de TV é gerado a partir do raw com áudio estéreo 48 kHz em silêncio (o raw do HyperFrames já sai em BT.709 com gama limitada, por isso não se converte a gama):

```bash
ffmpeg -i renders/centralgest-ia-compras-tv-20s-raw.mp4 -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -map 0:v -map 1:a -t 20 -c:v libx264 -profile:v high -level 4.2 -preset slow -crf 14 -maxrate 40M -bufsize 80M \
  -pix_fmt yuv420p -r 25 -g 12 -bf 2 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart renders/centralgest-ia-compras-TV-1080p25-20s.mp4
```

## Notas

- **Logótipo:** foi extraído do vídeo anterior (352px de largura) porque o site estava inacessível a partir deste ambiente. No end card aparece com 560px, ligeiramente suave. Para a versão final, substituir `assets/centralgest-logo-white.png` pelo logótipo oficial em SVG ou num PNG grande.
- **Especificações do canal:** confirmar com a estação (RTP/SIC/TVI ou a agência de meios) o formato pedido. Algumas pedem MXF XDCAM HD50 ou ProRes 422 HQ, 1080i50, e loudness EBU R128 a −23 LUFS na mistura final. A conversão a partir deste master é direta.
