# Instalação, verificação e restauração

## Ambiente

O pacote foi preparado para **Epson L3250**, Windows 7 x64 Intel/AMD e PowerShell 2.0 ou superior, com driver base **3.80.05.00**. O teste físico registrado usou conexão USB. Outros modelos, arquiteturas e versões do driver não foram validados.

A identificação do instalador é `L3250_L3251_X64_38005_LA.exe`, mas o ajuste e os hashes deste projeto são específicos do driver **EPSON L3250 Series**.

## Escolher e instalar

Baixe a [release V5](https://github.com/glokog/l3250-limite-estendido/releases/tag/v5-experimental). A correção de preferências usa o driver compatível existente; o pacote completo também traz `DriverOriginal.exe`.

1. Extraia todos os arquivos do ZIP em uma pasta nova.
2. Feche preferências e aplicativos de impressão; aguarde as filas terminarem.
3. Clique com o botão direito em `instalar.cmd` e selecione **Executar como administrador**.
4. Ao terminar, confira **comprimento máximo informado**. O valor esperado é aproximadamente **3276,7 mm**.
5. Execute `abrir-preferencias.cmd`, abra **Tamanho do papel → Definido pelo usuário** e tente salvar **210 × 3000 mm**.
6. Execute `verificar.cmd` para consultar arquivos e capacidade anunciada.

O instalador pausa o spooler durante a aplicação e não envia trabalhos de impressão. Guarde a pasta de estado/backup em:

```text
C:\ProgramData\L3250-Comprimento-Experimental-Win7
```

## Comandos

| Arquivo | Ação |
| --- | --- |
| instalar.cmd | Confere o driver, salva backup e aplica a V5 |
| verificar.cmd | Consulta arquivos e limite informado |
| abrir-preferencias.cmd | Abre as preferências da fila L3250 selecionada |
| restaurar.cmd | Restaura os perfis originais usando o backup V5 |

| Código | Significado |
| --- | --- |
| 0 | Arquivos e limite anunciado confirmados; a impressão física ainda precisa ser medida |
| 1 | Erro na operação |
| 2 | Limite ou verificação pendente/não confirmado |

## Imprimir um teste

O pacote oferece `teste-1500mm.pdf` e `teste-3000mm.pdf`, ambos com uma página de 210 mm de largura e marcas de comprimento.

Selecione o tamanho de papel correspondente e use escala **100%**, com margens. Desative ajuste automático de página, pôster/mosaico e várias páginas por folha. Meça o resultado físico: o arquivo ou a aceitação pelo spooler não comprova a escala e o comprimento impressos.

O marco anterior foi uma impressão de **1350 mm**. Em **23/10/2026**, o usuário confirmou a impressão física de **3000 mm**. Os PDFs continuam sendo instrumentos de teste, não evidência documental do teste realizado; aplicativo, resolução, conexão e método desse novo teste não foram informados. **Não tente tratar 4000 mm como tamanho suportado pela V5**: está acima do teto atual e exige investigação prévia, descrita no [plano técnico](ROADMAP-COMPRIMENTO.md).

## Restaurar

Feche aplicativos e preferências, aguarde a fila ficar vazia e execute `restaurar.cmd` como administrador. A restauração exige o backup V5, devolve os CFX de 1200 mm e preserva/retira o cache corrente para regeneração. Backups de versões anteriores permanecem em suas pastas.

## Conferir o download

Compare o SHA-256 do ZIP com `SHA256SUMS` na release. No Windows 7:

```bat
certutil -hashfile L3250_3m_WIN7_PS2_EXPERIMENTAL_V5.zip SHA256
```

No Linux:

```bash
sha256sum L3250_3m_WIN7_PS2_EXPERIMENTAL_V5.zip
```

## Problemas

| Situação | Próximo passo |
| --- | --- |
| Ainda aparece 1200 mm | Confira a saída de verificar.cmd e o log V5 |
| Hash desconhecido | Confira a versão do driver; o pacote só aplica em identidades reconhecidas |
| Fila ocupada | Aguarde os trabalhos concluírem e feche os aplicativos antes de repetir |
| Código 2 | Leia o limite retornado e o log; a confirmação ainda está pendente |
| Preferências não salvam 3000 mm | Registre o valor mostrado, o erro e o log V5 |
| Impressão termina antes do esperado | Confira escala e tamanho de papel e informe a última marca medida |

Para relatar um problema, use [Issues](https://github.com/glokog/l3250-limite-estendido/issues) com versão do Windows/driver, pacote, código retornado e comprimento medido. Revise nomes de computador, caminhos e documentos antes de publicar um log.
