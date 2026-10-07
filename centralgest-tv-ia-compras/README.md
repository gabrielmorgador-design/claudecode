# CentralGest · Compras com IA · spot de TV de 20s

Motion gráfico feito em [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP) para anúncio de TV, com música e sound design originais.

## Ficheiros

| Ficheiro | Para quê |
|---|---|
| `CENTRALGEST_IA_COMPRAS_20s_XDCAMHD422_1080i50.mxf` | **Master para a estação.** Não está no git (131 MB, acima do limite do GitHub): é gerado com os comandos abaixo |
| `renders/centralgest-ia-compras-PREVIEW-1080p50-com-musica.mp4` | Pré-visualização leve para ver no telemóvel ou enviar por email |
| `audio/centralgest-musica-sfx-23LUFS.wav` | Música + sound design isolados (48 kHz, 24 bits), para misturar com a locução |
| `vo-guia-locucao.srt` | Tempos de cada frase para o locutor e para a montagem |

## Especificações do master (conforme pedido pela estação)

| Requisito | Entregue | Verificado |
|---|---|---|
| Material | HD | ✓ |
| Formato | XDCAM HD422 | ✓ |
| Aspect ratio | 16:9 | ✓ |
| Container | MXF (OP1a) | ✓ |
| Codec | MPEG-2 4:2:2P@HL | ✓ (profile 4:2:2, level High) |
| Resolução | 1920 × 1080 | ✓ |
| Bit rate | 50 Mbps | ✓ (CBR) |
| Frame frequency | 50i | ✓ (25 frames entrelaçados, top field first) |
| Áudio | 24 bits | ✓ (PCM 24 bits, 48 kHz, 2 faixas mono L/R) |
| Y/C sampling | 4:2:2 | ✓ |
| 2 frames a negro no início e no fim | frames 0–1 e 498–499 | ✓ (Y = 16, negro legal) |
| Som a −23,0 LUFS ± 0,5 LU | −23,0 LUFS | ✓ (true peak −7,4 dBFS) |
| Duração | 20,00 s (500 frames) | ✓ |

O vídeo é renderizado a **50p** e entrelaçado para 50i com filtro vertical anti-cintilação. Assim o movimento fica tão fluido na TV como um spot filmado em 50i.

## Cor: azul #0C5FFB, com abertura clara

O azul da marca domina o spot: destaca-se num intervalo publicitário (a maioria dos spots é escura ou tem imagem real), fica associado à CentralGest e faz sobressair os cartões brancos da interface. Texto branco sobre #0C5FFB tem contraste de 5,2:1.

Os primeiros 3 segundos (o problema, "à mão") são num fundo claro liso. Quando a IA entra, um círculo azul nasce da ✦ e toma conta do ecrã. Esta mudança de cor é o segundo gancho visual.

## Guião da locução e tempos

| Tempo | Locução | No ecrã |
|---|---|---|
| 0,3 – 2,8s | Ainda regista faturas de compra à mão? | Pilha de faturas a cair, "47 faturas por lançar", campo escrito à mão |
| 3,2 – 6,0s | Agora, a IA do CentralGest faz isso por si! | Círculo azul a partir da ✦ da IA, "por si!" destacado |
| 6,3 – 9,2s | Lê linha a linha e preenche tudo no software. | Feixe lê a fatura; cada bloco "voa" para o CentralGest |
| 9,5 – 11,5s | Basta um clique e está pronto! | Zoom no botão, clique, "✓ Compra registada"; o botão transforma-se num visto |
| 12,1 – 15,5s | Menos tempo a registar faturas. Mais tempo para o seu negócio. | "registar faturas" riscado; "o seu negócio." destacado |
| 15,9 – 19,4s | CentralGest, o software de gestão ideal para empresas e contabilistas. | Construção do logótipo (nuvem desenhada, letras a subir) e assinatura |

## Música e sound design

Faixa original, sintetizada em `audio/make_music.py`, sem samples nem bibliotecas de terceiros, por isso sem direitos a pagar. A 120 BPM, com o compasso ancorado no impacto da IA (3,3s), para cada mudança de cena cair no tempo:

- **0–3,3s:** intro contida (sons de papel, teclas, notas espaçadas), com um riser até à entrada da IA
- **3,3s:** "drop" com impacto quando o ecrã fica azul
- **9,3–10,3s:** a batida sai enquanto o cursor viaja e volta exatamente no clique
- **15,8s:** acorde final e brilho no logótipo, a desvanecer até ao negro

O sound design acompanha a animação, como nos vídeos de referência: papel, teclado, pops dos cartões, um "blip" ascendente por cada campo preenchido, clique do rato, sino de confirmação e whooshes nas transições.

**Com a locução:** a versão atual tem só música, a −23 LUFS. Quando a voz estiver gravada, a música entra por baixo (cerca de −12 dB em relação à voz) e **a mistura final volta a ser normalizada a −23 LUFS**.

## Editar e renderizar

```bash
npm run preview   # Studio para editar textos e tempos
npm run check     # lint + validação + contraste
npm run render    # render a 50 fps → renders/centralgest-ia-compras-tv-20s-raw.mp4
npm run music     # gera a música → renders/music_raw.wav
```

Normalizar a música para −23 LUFS (o ganho é linear, sem compressão):

```bash
ffmpeg -i renders/music_raw.wav -af "volume=-6.06dB" -c:a pcm_s24le audio/centralgest-musica-sfx-23LUFS.wav
```

Master XDCAM HD422 1080i50 (negro nos 2 primeiros e 2 últimos frames, áudio em 2 faixas mono PCM 24 bits):

```bash
ffmpeg -i renders/centralgest-ia-compras-tv-20s-raw.mp4 -i audio/centralgest-musica-sfx-23LUFS.wav \
  -filter_complex "[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='lt(n,4)+gte(n,996)',tinterlace=mode=interleave_top:flags=cvlpf,setfield=tff,format=yuv422p[v];[1:a]channelsplit=channel_layout=stereo[aL][aR]" \
  -map "[v]" -map "[aL]" -map "[aR]" -t 20 \
  -c:v mpeg2video -profile:v 0 -level:v 2 -non_linear_quant 1 -flags +ildct+ilme -top 1 -dc 10 -intra_vlc 1 -qmax 3 -lmin "1*QP2LAMBDA" -vtag xd5c \
  -rc_max_vbv_use 1 -rc_min_vbv_use 1 -g 12 -bf 2 -b:v 50000k -minrate 50000k -maxrate 50000k -bufsize 8000k -aspect 16:9 -r 25 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a pcm_s24le -ar 48000 -f mxf renders/CENTRALGEST_IA_COMPRAS_20s_XDCAMHD422_1080i50.mxf
```

Verificar a loudness do master:

```bash
ffmpeg -i renders/CENTRALGEST_IA_COMPRAS_20s_XDCAMHD422_1080i50.mxf -filter_complex "[0:a:0][0:a:1]amerge=inputs=2,ebur128=peak=true" -f null -
```
