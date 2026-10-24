# Epson L3250 — limite de comprimento estendido

Pacote **V5 experimental** para ampliar o comprimento de papel configurável no driver Epson L3250, com instalador, verificação e restauração.

**Windows 7 x64 (Intel/AMD) · PowerShell 2.0 ou superior · Driver base 3.80.05.00**

[Baixar a V5](https://github.com/glokog/l3250-limite-estendido/releases/tag/v5-experimental) · [Instalação](docs/INSTALACAO.md) · [Funcionamento](docs/FUNCIONAMENTO.md) · [Validação](docs/VALIDACAO.md)

## O que foi confirmado

| Item | Situação |
| --- | --- |
| Limite original dos perfis | 1.200 mm |
| Limite configurado pela V5 | 3.276,7 mm; 129,00 polegadas no perfil equivalente |
| Marco físico anterior | **1.350 mm (cerca de 1,3 m), via USB**, após aplicar a V5 |
| Impressão física de 3.000 mm | **Confirmada pelo usuário em 23/10/2026**; relato de teste físico, não teste automatizado |
| Página de 4.000 mm | Próximo objetivo de investigação; **não validada** e acima do teto atual |
| Comprimento arbitrário / rolo de 30 metros | Hipótese para pesquisa futura, sem garantia de suporte |

O aumento do limite nos arquivos ou a resposta do driver não comprova, sozinho, a impressão de todo o comprimento. O novo marco de **3 metros realmente impressos** é uma confirmação humana, informada pelo usuário; não foram recebidos novos parâmetros do teste para atribuir aplicativo, resolução, conexão ou método a esse resultado. Os pacotes V5 existentes permanecem preservados.

**Próximo passo:** investigar a barreira de 3276,7 mm antes de preparar um teste de 4 m. Trocar apenas o número do perfil não basta para garantir suporte. Veja o [plano técnico de 4 m e comprimento configurável](docs/ROADMAP-COMPRIMENTO.md).

## Downloads

| Arquivo | Uso | Tamanho aproximado |
| --- | --- | --- |
| [Pacote completo V5](https://github.com/glokog/l3250-limite-estendido/releases/download/v5-experimental/L3250_3m_WIN7_PS2_EXPERIMENTAL_V5.zip) | Inclui o instalador Epson original e o ajuste | 69 MiB |
| [Correção de preferências V5](https://github.com/glokog/l3250-limite-estendido/releases/download/v5-experimental/L3250_CORRECAO_PREFERENCIAS_V5.zip) | Usa o driver compatível já instalado | 52 KiB |
| [SHA256SUMS](https://github.com/glokog/l3250-limite-estendido/releases/download/v5-experimental/SHA256SUMS) | Conferir os arquivos baixados | — |

Se o driver compatível já está instalado, use a correção menor. O script confere hashes antes de aplicar o ajuste.

## Instalação rápida

1. Extraia **todo o ZIP** em uma pasta nova.
2. Feche as preferências Epson e os aplicativos que usam a impressora; aguarde a fila ficar vazia.
3. Execute `instalar.cmd` como administrador.
4. Confira o comprimento máximo informado e execute `abrir-preferencias.cmd`.
5. Em **Tamanho do papel → Definido pelo usuário**, tente salvar **210 × 3000 mm**.
6. Use `verificar.cmd` para consultar o estado; `restaurar.cmd` desfaz o ajuste usando o backup V5.

Veja [o guia completo](docs/INSTALACAO.md), incluindo os códigos de saída e a restauração.

## Como funciona

A V5 modifica três atributos de comprimento nos dois perfis CFX conhecidos. Aplica os perfis reconhecidos no spooler e na pasta de dados Epson, preserva backup e renova o cache CFB específico para que o driver possa regenerá-lo.

O pacote confere duas DLLs, o VIF e os perfis pelos hashes registrados. Interrompe se encontrar identidade desconhecida ou perfil necessário ausente. Leia [o funcionamento e os arquivos envolvidos](docs/FUNCIONAMENTO.md).

## Documentação e scripts

- [Instalação, uso, restauração e solução de problemas](docs/INSTALACAO.md)
- [Funcionamento do ajuste V5](docs/FUNCIONAMENTO.md)
- [Validação e resultados conhecidos](docs/VALIDACAO.md)
- [Plano técnico: 4 m e comprimento configurável](docs/ROADMAP-COMPRIMENTO.md)
- [Relatório técnico original V5](docs/RELATORIO-V5.md)
- [Histórico](CHANGELOG.md)
- [Scripts, manifests e perfis do pacote menor](pacote/)
- [Componentes e atribuições](THIRD_PARTY_NOTICES.md)

Este é um pacote independente e não oficial. Arquivos Epson mantêm a titularidade e os termos de origem; este projeto não atribui nova licença a eles.
