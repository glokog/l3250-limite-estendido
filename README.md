# Epson L3250 e L375 — papel longo e sem margem

Pacotes **experimentais** para ampliar o comprimento do papel definido pelo usuário nos drivers Epson L3250 e L375 e liberar sem margem em qualquer tamanho. Cada pacote tem instalador, verificação e restauração.

**Windows 7 x64 (Intel/AMD) · PowerShell 2.0 ou superior**

## Versões atuais

| Impressora | Versão | O que faz | Downloads |
| --- | --- | --- | --- |
| L3250 (driver 3.80.05.00) | **V8** | Papel até 4624 mm + sem margem em qualquer tamanho | [Correção (driver já instalado)](https://github.com/glokog/l3250-limite-estendido/releases/download/v8-experimental/L3250_CORRECAO_PREFERENCIAS_V8.zip) · [Completo](https://github.com/glokog/l3250-limite-estendido/releases/download/v8-experimental/L3250_4624mm_SEM_MARGEM_TOTAL_WIN7_V8.zip) · [Notas](https://github.com/glokog/l3250-limite-estendido/releases/tag/v8-experimental) |
| L375 (driver 2.60.00.00) | **V3** | Papel até 4624 mm + sem margem (por conta e risco) | [Correção (driver já instalado)](https://github.com/glokog/l3250-limite-estendido/releases/download/l375-v3-experimental/L375_CORRECAO_PREFERENCIAS_V3.zip) · [Completo](https://github.com/glokog/l3250-limite-estendido/releases/download/l375-v3-experimental/L375_4624mm_SEM_MARGEM_WIN7_V3.zip) · [Notas](https://github.com/glokog/l3250-limite-estendido/releases/tag/l375-v3-experimental) |
| L375 sem sem margem | V2 | Só papel até 4624 mm | [Notas](https://github.com/glokog/l3250-limite-estendido/releases/tag/l375-v2-experimental) |

O pacote **completo** inclui o instalador original da Epson; a **correção** usa o driver que já está instalado. Cada release tem um `SHA256SUMS` para conferir os arquivos.

## Situação

| Item | Situação |
| --- | --- |
| L3250 V5 (3276,7 mm) | Impressão de 1350 mm via USB confirmada; 3 m informado pelo responsável |
| L3250 V6 (4624 mm) | **4624 mm aparece nas preferências** do driver; impressão de 3 m e 4,6 m pendente |
| L3250 V7/V8 (sem margem) | Não testadas; o responsável já imprimia sem margem na L3250 com o driver da L4260 |
| L375 V2 (4624 mm) | Não testada |
| L375 V3 (sem margem) | Não testada. A Epson não fez sem margem para a L375; a V3 copia o recurso da L4260 por conta e risco (a tinta pode sujar a base da impressora) |

Mudar o limite nos arquivos não prova, sozinho, que a impressora imprime o comprimento inteiro.

## Instalação rápida

1. Extraia **todo o ZIP** em uma pasta nova.
2. Feche as preferências Epson e os aplicativos que usam a impressora; aguarde a fila ficar vazia.
3. Clique com o botão direito em `instalar.cmd` → **Executar como administrador**.
4. No fim, confira **comprimento máximo informado: 4624 mm**.
5. Use `abrir-preferencias.cmd` e crie o tamanho em **Tamanho do papel → Definido pelo usuário**.
6. Imprima `teste-3000mm.pdf` e depois `teste-4600mm.pdf`, em escala 100%.

`verificar.cmd` só consulta o estado; `restaurar.cmd` volta aos arquivos originais da Epson. Cada versão atualiza por cima da anterior.

## Como funciona

O ajuste muda só os perfis de configuração do driver (arquivos CFX, em XML) e renova o cache CFB, sem alterar DLLs, registro, assinaturas ou DriverStore. O instalador confere as DLLs, o VIF e os perfis pelos hashes conhecidos e para se encontrar algo diferente.

- **4624 mm** é o teto escolhido: o driver guarda a dimensão personalizada em 16 bits sem sinal e o protocolo ESC/P-R tem coordenada vertical de 16 bits a 360 dpi (≈ 4623,9 mm).
- Quando não existem perfis em `C:\ProgramData\EPSON\<modelo> Series`, o driver lê o CFX da pasta do spooler e regenera o cache; o instalador ajusta esse CFX.
- **Sem margem na L3250:** a DLL de configuração da L3250 e a da L4260 são idênticas em código; a diferença está no CFX. A V7 copia as regras de sem margem da L4260 e a V8 as estende a todos os tamanhos.
- **Sem margem na L375:** a tela do driver já tem os controles, mas o CFX não define o recurso; a V3 copia os campos, a tabela de expansão e a origem sem margem do CFX da L4260.

## Histórico de versões

| Tag | Impressora | Resumo |
| --- | --- | --- |
| [`l375-v3-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/l375-v3-experimental) | L375 | 4624 mm + sem margem experimental copiado da L4260 |
| [`v8-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/v8-experimental) | L3250 | 4624 mm + sem margem em qualquer tamanho |
| [`l375-v2-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/l375-v2-experimental) | L375 | 4624 mm; campo "Verificar largura do papel" volta a ficar oculto |
| [`v7-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/v7-experimental) | L3250 | 4624 mm + sem margem como na L4260 (substituída) |
| [`l375-v1-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/l375-v1-experimental) | L375 | 4624 mm (substituída) |
| [`v6-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/v6-experimental) | L3250 | 4624 mm; funciona sem perfis em ProgramData (substituída) |
| [`v5-experimental`](https://github.com/glokog/l3250-limite-estendido/releases/tag/v5-experimental) | L3250 | 3276,7 mm |

Detalhes em [CHANGELOG.md](CHANGELOG.md).

## Pastas

- [`pacote/`](pacote/) — conteúdo da correção L3250 mais recente (scripts, manifests, perfis original e ajustado).
- [`l375/pacote/`](l375/pacote/) — o mesmo para a L375.
- [`ferramentas/`](ferramentas/) — scripts que geraram os pacotes (precisam dos instaladores Epson originais).
- [`docs/`](docs/) — guias e relatórios técnicos (V5, V6/V7 e L375).
- [Componentes e atribuições](THIRD_PARTY_NOTICES.md)

Este é um projeto independente e não oficial. Arquivos Epson mantêm a titularidade e os termos de origem; este projeto não atribui nova licença a eles.
