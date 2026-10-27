#!/usr/bin/env python3
"""Build the Epson L375 4624 mm / borderless experimental bundle."""
import hashlib
import json
import re
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'L375_X64_260_LA.exe'
SOURCE_SHA256 = '1d121e1d46dd647303f985eabd563f3d2801273c9e1a4fbd0bbee74d193fd06c'
ANALYSIS = ROOT / 'analysis' / 'l375'
OUT = ROOT / 'dist' / 'L375_4624mm_BORDERLESS_EXPERIMENTAL_V1'
NS = {'e': 'http://schema.epson.net/fusion/business/v150'}
FILES = [
    ('E_JC1N9A.CFX', 'E_TCXN8A.CFX', 'ce34976fee477b08c4c798e11e1761205cbabed352df916420cf99c679cf4ddf'),
    ('E_JC1N9E.CFX', 'E_TCXN8E.CFX', 'bf9bda9c8977bc86d2bc183a07b694ace42f7f2d6a262aed27e3b4403b4f7353'),
]
BINARIES = [
    (['ConfigFile'], 'E_WU1MA0.DLL', 'E_YUICN8E.DLL', '95293390d98319fd8e097a1ba09fd61dcc7bec131cbf05a00abd2c7e79c967c5'),
    (['DriverPath'], 'E_WMAI50.DLL', 'E_YMAIN8E.DLL', '5ad910fc3d4210fa30389da395682eb3ab7801c15ce23bb2cc0cb55861bdf04d'),
    (['DataFile'], 'E_WM1N8E.VIF', 'E_YVIFN8E.VIF', 'f89d1b151c412797255ff4c91b0620baeb641df59e962dafe946f329d6343e46'),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch_config(data):
    """Set 4624 mm limits and unhide L375's existing borderless method."""
    tree = ET.fromstring(data)
    extent = tree.findall("e:f/e:F[@f='7']/e:E[@e='261']", NS)
    metric = tree.findall("e:f/e:F[@f='11']/e:E[@e='0']/e:V", NS)
    imperial = tree.findall("e:f/e:F[@f='13']/e:E[@e='0']/e:V", NS)
    assert len(extent) == len(metric) == len(imperial) == 1
    assert (extent[0].get('J'), extent[0].get('K')) == ('2159', '11176')
    assert (metric[0].get('n'), metric[0].get('x'), metric[0].text) == ('1270', '11176', '2970')
    assert (imperial[0].get('n'), imperial[0].get('x'), imperial[0].text) == ('500', '4400', '1169')
    field_230 = tree.find("e:f/e:F[@f='230']", NS)
    reset_230 = tree.find("e:y/e:F[@f='230']", NS)
    assert field_230 is not None and field_230.get('r') == '20145' and field_230.get('S') == 'f'
    assert reset_230 is not None
    replacements = [(b'K="11176"', b'K="46240"'), (b'x="11176"', b'x="46240"'), (b'x="4400"', b'x="18205"')]
    extent[0].set('K', '46240')
    metric[0].set('x', '46240')
    imperial[0].set('x', '18205')
    result = data
    for before, after in replacements:
        assert data.count(before) == 1
        result = result.replace(before, after)
    marker = b'r="20145" t="0" F="0x0105" S="f"'
    assert result.count(marker) == 1
    result = result.replace(marker, b'r="20145" t="0" F="0x0105"')
    field_230.attrib.pop('S')
    assert ET.tostring(tree) == ET.tostring(ET.fromstring(result))
    patched_tree = ET.fromstring(result)
    assert patched_tree.find("e:f/e:F[@f='230']", NS) is not None
    assert patched_tree.find("e:f/e:F[@f='230']", NS).get('S') is None
    assert patched_tree.find("e:y/e:F[@f='230']", NS) is not None
    return result


def text_file(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8-sig'))


def make_test_pdf(path, length_mm, model='L375'):
    scale = 72 / 25.4
    width, height = 210 * scale, length_mm * scale
    commands = ['0 G', '0.6 w']

    def line(x, y, x2, y2):
        commands.append(f'{x * scale:.3f} {height - y * scale:.3f} m {x2 * scale:.3f} {height - y2 * scale:.3f} l S')

    def label(x, y, message, size=11):
        message = message.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        commands.append(f'BT /F1 {size} Tf {x * scale:.3f} {height - y * scale:.3f} Td ({message}) Tj ET')

    label(15, 18, f'EPSON {model} - TESTE {length_mm} mm', 14)
    label(15, 27, f'Uma pagina de 210 x {length_mm} mm. Escala 100%. Papel com margens.', 10)
    label(15, 35, 'Nao usar Poster, Mosaico, Ajustar pagina ou varias paginas por folha.', 10)
    line(15, 50, 15, length_mm - 15)
    for mm in range(100, length_mm, 100):
        line(15, mm, 40 if mm != 1100 else 180, mm)
        label(45, mm + 4, f'{mm} mm' + (' - perto do antigo limite (1117 mm)' if mm == 1100 else ''))
        if mm in (1300, 1500, 2000, 2500, 3000, 3500, 4000, 4500):
            label(90, mm + 4, f'MARCA ALEM DO ANTIGO LIMITE: {mm / 1000:.1f} m', 10)
    label(40, length_mm - 18, f'FIM - {length_mm} mm; medir a folha, sem reducao de escala.', 11)
    stream = ('\n'.join(commands) + '\n').encode('ascii')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.5f} {height:.5f}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>'.encode(),
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'endstream',
    ]
    output = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output += f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(output)
    output += b'xref\n0 6\n0000000000 65535 f \n'
    output += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    output += f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    path.write_bytes(output)


def main():
    assert digest(SOURCE.read_bytes()) == SOURCE_SHA256, 'Unexpected L375 installer'
    inf = (ANALYSIS / 'windows64' / 'WINX64' / 'E_WF1N8E.INF').read_text(encoding='utf-16le')
    assert '"EPSON L375 Series"' in inf
    assert 'DriverVer=10/09/2025,2.60.00.00' in inf
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'patch').mkdir(exist_ok=True)
    (OUT / 'originais').mkdir(exist_ok=True)
    entries = []
    for source_name, installed_name, expected in FILES:
        assert installed_name + ',' + source_name in inf
        original = (ANALYSIS / 'unpacked' / source_name).read_bytes()
        assert digest(original) == expected, source_name
        patched = patch_config(original)
        (OUT / 'patch' / installed_name).write_bytes(patched)
        (OUT / 'originais' / installed_name).write_bytes(original)
        entries.append({
            'source_name': source_name, 'installed_name': installed_name,
            'original_sha256': expected, 'patched_sha256': digest(patched),
            'previous_sha256': expected,
            'changed_attributes': ['F[f=7]/E[e=261]@K', 'F[f=11]/E[e=0]/V@x', 'F[f=13]/E[e=0]/V@x', 'F[f=230]/@S'],
        })
    binaries = []
    for properties, source_name, installed_name, expected in BINARIES:
        assert installed_name + ',' + source_name in inf
        data = (ANALYSIS / 'unpacked' / source_name).read_bytes()
        assert digest(data) == expected, source_name
        if source_name.endswith('.DLL'):
            pe_offset = struct.unpack_from('<I', data, 0x3c)[0]
            assert data[pe_offset:pe_offset + 4] == b'PE\0\0'
            assert struct.unpack_from('<H', data, pe_offset + 4)[0] == 0x8664, 'Non-AMD64 DLL'
        binaries.append({'properties': properties, 'source_name': source_name, 'installed_name': installed_name, 'sha256': expected})
    manifest = {
        'format': 1, 'release': 1, 'status': 'experimental-not-tested-on-windows-or-printer',
        'driver': 'EPSON L375 Series', 'driver_version': '2.60.00.00',
        'architecture': 'amd64', 'minimum_powershell': '2.0',
        'target_os': 'Windows 7 x64', 'legacy_inf': 'E_WF1N8E.INF',
        'original_installer_sha256': SOURCE_SHA256,
        'original_max_length_tenths_mm': 11176, 'patched_max_length_tenths_mm': 46240,
        'patched_max_length_hundredths_inch': 18205,
        'borderless_method_field': 230, 'borderless_change': 'remove S=f from existing field',
        'binaries': binaries, 'files': entries,
    }
    text_file(OUT / 'manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    document = ET.Element('l375', {'format': '1', 'driver': manifest['driver'], 'original_installer_sha256': SOURCE_SHA256})
    files_xml = ET.SubElement(document, 'files')
    for entry in entries:
        ET.SubElement(files_xml, 'file', {key: entry[key] for key in ['installed_name', 'original_sha256', 'previous_sha256', 'patched_sha256']})
    binaries_xml = ET.SubElement(document, 'binaries')
    for binary in binaries:
        ET.SubElement(binaries_xml, 'binary', {
            'properties': ','.join(binary['properties']), 'source_name': binary['source_name'], 'sha256': binary['sha256'],
        })
    (OUT / 'manifest.xml').write_bytes(ET.tostring(document, encoding='utf-8', xml_declaration=True))
    shutil.copyfile(SOURCE, OUT / 'DriverOriginal.exe')
    script = (ROOT / 'tools' / 'Install-L375-Win7.ps1').read_text()
    assert not re.search(r'(?i)-(shr|shl|in|notin)\b', script), 'PS3+ operator in PS2 installer'
    for incompatible in ['Get-Printer', 'Get-PrintJob', 'Get-FileHash', 'ConvertFrom-Json', 'ConvertTo-Json', '-Raw', '[pscustomobject]', '$PSScriptRoot', '$PSCommandPath', 'IsNullOrWhiteSpace', 'Is64BitProcess', 'Is64BitOperatingSystem']:
        assert incompatible not in script, 'Unexpected installer dependency: ' + incompatible
    text_file(OUT / 'Install-L375.ps1', script)
    text_file(OUT / 'L375-Process.cs', (ROOT / 'tools' / 'L375-Process.cs').read_text())
    text_file(OUT / 'L375-Spooler.cs', (ROOT / 'tools' / 'L375-Spooler.cs').read_text())
    for name, action in [('instalar', 'Install'), ('restaurar', 'Restore'), ('verificar', 'Verify'), ('abrir-preferencias', 'Preferences')]:
        cmd = rf'''@echo off
setlocal
cd /d "%~dp0"
set "L375_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "L375_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%L375_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-L375.ps1" -Action {action}
set "L375_RESULT=0"
if errorlevel 1 set "L375_RESULT=1"
if errorlevel 2 set "L375_RESULT=2"
if errorlevel 3 set "L375_RESULT=1"
if not errorlevel 0 set "L375_RESULT=1"
echo.
echo Codigo %L375_RESULT%: 0 = concluido; 1 = erro; 2 = verificacao pendente ou limite nao confirmado.
pause
exit /b %L375_RESULT%
'''
        (OUT / (name + '.cmd')).write_bytes(cmd.replace('\n', '\r\n').encode('ascii'))
    for length in (1500, 3000, 4600):
        make_test_pdf(OUT / f'teste-{length}mm.pdf', length, model='L375')
    text_file(OUT / 'LEIA-ME.txt', r"""EPSON L375 V1 - CAMPO SEM BORDA E PAPEL ATE 4624 mm
Windows 7 x64 Intel/AMD, PowerShell 2.0 ou superior

1. Extraia TODO o ZIP em uma pasta nova.
2. Feche as preferencias Epson e os aplicativos que usam a impressora.
   Aguarde as filas de impressao terminarem.
3. Clique com o botao direito em instalar.cmd > Executar como administrador.
4. Ao terminar, confira "comprimento maximo informado". O esperado e
   aproximadamente 4624 mm. Codigo 2 significa limite nao confirmado.
5. Execute abrir-preferencias.cmd e tente salvar 210 x 4624 mm em
   Tamanho do papel > Definido pelo usuario.
6. Se o limite nao mudar, envie o log indicado na janela. Nao imprima
   durante a aplicacao.
7. Teste de impressao, um de cada vez: primeiro teste-3000mm.pdf, depois
   teste-4600mm.pdf. Tamanho do papel = Definido pelo usuario com a mesma
   largura e comprimento do PDF; escala 100%, sem Ajustar pagina.
   Mande foto ou diga a ultima marca que saiu no papel.

O driver de origem e Epson L375 2.60.00.00, x64. O limite original nos
dois CFX era 1117,6 mm. O VIF e a INF relacionam os perfis ativos:
  %ProgramData%\EPSON\EPSON L375 Series\E_TCXN8E.CFX
  %ProgramData%\EPSON\EPSON L375 Series\E_TCXN8A.CFX
  %ProgramData%\EPSON\EPSON L375 Series\ConvBinData\E_TCXN8E.CFB

Os dois perfis passam para 4624 mm / 182,05 polegadas. O campo CFX 230,
"Metodos de expansao sem margens", ja existia na L375 com S="f". A V1
remove esse marcador, seguindo a definicao ativa da L4260. A DLL da L375
ja contem a classe de selecao por radio para papel personalizado sem
borda. Os campos 213-215 da L3250 nao existem neste driver e nao foram
importados.

O instalador verifica os hashes dos binarios originais, atualiza os CFX
reconhecidos no spooler e na pasta de dados, faz backup e renova o CFB
com o spooler parado. Nao modifica DLLs, registro, permissoes, assinaturas
ou DriverStore. Nao imprime. Se encontrar arquivos desconhecidos,
interrompe antes de aplicar.

restaurar.cmd recupera os dois CFX originais de 1117,6 mm e renova o CFB.
verificar.cmd consulta arquivos e DC_MAXEXTENT sem aplicar o ajuste.
Logs e backups: C:\ProgramData\L375-Comprimento-Experimental-Win7

Codigo 0 confirma arquivos/limite anunciado, nao uma impressao de 4624 mm.
Codigo 1: erro. Codigo 2: limite nao confirmado.
O ZIP pequeno usa o driver L375 2.60.00.00 ja instalado; o completo inclui
o instalador original Epson.

Pacote experimental. O painel e a impressao longa nao foram testados no
Windows. O manual oficial da L375 documenta tamanhos definidos pelo
usuario, mas nao confirma sem borda em papel personalizado ou com 4624 mm.
A alteracao do campo 230 e uma inferencia estatica a partir do CFX da L4260
e precisa ser confirmada no painel da L375.
""")
    sums = ''.join(f'{digest(path.read_bytes())}  {path.relative_to(OUT).as_posix()}\n' for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS.txt')
    (OUT / 'SHA256SUMS.txt').write_text(sums)
    archive = OUT.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file():
                z.write(path, Path(OUT.name) / path.relative_to(OUT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert digest(z.read(OUT.name + '/DriverOriginal.exe')) == SOURCE_SHA256
        for entry in entries:
            assert digest(z.read(OUT.name + '/patch/' + entry['installed_name'])) == entry['patched_sha256']
    result = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': digest(archive.read_bytes()), 'manifest': manifest}
    repair = ROOT / 'dist' / 'L375_CORRECAO_PREFERENCIAS_V1.zip'
    repair_files = [path for path in sorted(OUT.rglob('*')) if path.is_file() and path.name not in ['DriverOriginal.exe', 'SHA256SUMS.txt']]
    repair_sums = ''.join(f'{digest(path.read_bytes())}  {path.relative_to(OUT).as_posix()}\n' for path in repair_files)
    with zipfile.ZipFile(repair, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in repair_files:
            z.write(path, Path('L375_CORRECAO_PREFERENCIAS_V1') / path.relative_to(OUT))
        z.writestr('L375_CORRECAO_PREFERENCIAS_V1/SHA256SUMS.txt', repair_sums)
    with zipfile.ZipFile(repair) as z:
        assert z.testzip() is None
    result['repair'] = {'archive': str(repair), 'bytes': repair.stat().st_size, 'sha256': digest(repair.read_bytes())}
    (ANALYSIS / 'package-build-v1.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['archive', 'bytes', 'sha256']}, indent=2))
    print(json.dumps(result['repair'], indent=2))


if __name__ == '__main__':
    main()
