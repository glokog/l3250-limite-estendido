# Histórico

## L3250 V6 experimental — 27/10/2026

- Limite do papel definido pelo usuário de 1200 para **4624 mm** (182,05 pol.).
- Sem perfis em ProgramData, ajusta os CFX do driver no spooler; o driver regenera o cache (confirmado com REA + Ghidra).
- Atualiza por cima da V5; réguas de teste de 1500, 3000 e 4600 mm.
- 4624 mm confirmado nas preferências do driver pelo responsável.
- Acrescentava o campo 230, que é "Verificar largura do papel antes de imprimir" (não sem margem); retirado na V7.

## 23/10/2026 — marco físico de 3 metros (documentação)

- Usuário confirmou que a Epson L3250 realmente imprimiu **3000 mm**.
- Mantido o marco anterior de 1350 mm (cerca de 1,3 m) via USB; o limite original do perfil era 1200 mm.
- Documentados os obstáculos para 4000 mm e o plano de comprimento configurável, ambos ainda não validados.
- Nenhuma alteração em driver, perfis, limites, scripts, manifests ou pacotes de release.

## V5 experimental

- Aplicação em perfis CFX reconhecidos do spooler e da pasta de dados Epson.
- Backup verificado e renovação seletiva do cache E_TCXYWE.CFB.
- Preservação das correções de elevação e retorno introduzidas na V4.
- Limites métricos de 3276,7 mm e equivalente de 129,00 polegadas.
- Restauração com backup V5 e rollback em falhas.
- Impressão manual de 1350 mm informada pelo responsável.

As revisões V1–V4 foram etapas anteriores da investigação. Esta publicação distribui a V5.
