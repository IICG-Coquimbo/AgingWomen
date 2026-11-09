param(
  [Parameter(Mandatory = $true)][string]$Documentos,
  [Parameter(Mandatory = $true)][string]$Temporal,
  [Parameter(Mandatory = $true)][string]$SalidaCsv,
  [string[]]$Solo = @(),
  [int]$Limite = 240,
  [double]$UmbralVacia = 0.30
)
# Layout control for the Word documents of phases 38R and 39R. Works only on COPIES placed in -Temporal.
# For each document it exports a PDF next to the copy and reports: pages, paragraphs kept with next that ended on another page,
# tables whose last row or header is alone on a page, almost empty pages, and images larger than the text area.
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $Temporal | Out-Null
$inicioTotal = Get-Date
$filas = @()
foreach ($a in (Get-ChildItem (Join-Path $Documentos '*.docx') | Sort-Object Name)) {
  if ($Solo.Count -and ($Solo -notcontains $a.Name.Substring(0, 2))) { continue }
  $copia = Join-Path $Temporal $a.Name
  Copy-Item $a.FullName $copia -Force
  $j = Start-Job -ArgumentList $copia, $UmbralVacia -ScriptBlock {
    param($c, $umbral)
    $no = [ref]0
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false; $w.DisplayAlerts = 0; $w.AutomationSecurity = 3
    $d = $w.Documents.Open($c, $false, $true, $false)
    $d.ActiveWindow.View.Type = 3
    $d.Repaginate()
    $d.ExportAsFixedFormat(($c -replace '\.docx$', '.pdf'), 17)
    $paginas = [int]$d.ComputeStatistics(2)
    $separados = New-Object System.Collections.ArrayList
    $max = @{}; $alto = @{}
    $prevUnir = $false; $prevPag = 0; $prevTxt = ''
    foreach ($p in $d.Paragraphs) {
      $r = $p.Range
      $enTabla = [bool]$r.Information(12)
      $ini = $r.Duplicate; $ini.Collapse(1)
      $pag = [int]$ini.Information(3)
      if ($prevUnir -and $pag -ne $prevPag) { [void]$separados.Add("p$prevPag`: $prevTxt") }
      $fin = $r.Duplicate; $fin.SetRange($r.End - 1, $r.End - 1)
      $pf = [int]$fin.Information(3); $y = [double]$fin.Information(6)
      if (-not $alto.ContainsKey($pf)) { $alto[$pf] = [double]$r.Sections.Item(1).PageSetup.PageHeight; $max[$pf] = 0.0 }
      if ($y -gt $max[$pf]) { $max[$pf] = $y }
      $prevUnir = ((-not $enTabla) -and ($p.KeepWithNext -eq -1))
      $prevPag = $pf
      $t = $r.Text; if ($t.Length -gt 50) { $t = $t.Substring(0, 50) }
      $prevTxt = ($t -replace '[\r\n\a|]', ' ')
    }
    function PagCelda($t, $f) { $x = $t.Cell($f, 1).Range; $x.Collapse(1); [int]$x.Information(3) }
    $aisladas = New-Object System.Collections.ArrayList
    $cabeceras = 0
    $it = 0
    foreach ($t in $d.Tables) {
      $it++
      $n = $t.Rows.Count
      if ($n -ge 2) {
        if ((PagCelda $t 1) -ne (PagCelda $t 2)) { $cabeceras++ }
        if ($n -ge 3 -and (PagCelda $t $n) -ne (PagCelda $t ($n - 1))) { [void]$aisladas.Add("tabla $it") }
      }
    }
    $fuera = 0
    foreach ($s in $d.InlineShapes) {
      $ps = $s.Range.Sections.Item(1).PageSetup
      if ($s.Width -gt ($ps.PageWidth - $ps.LeftMargin - $ps.RightMargin + 1) -or $s.Height -gt ($ps.PageHeight - $ps.TopMargin - $ps.BottomMargin + 1)) { $fuera++ }
    }
    $vacias = @($max.Keys | Sort-Object | Where-Object { ($max[$_] / $alto[$_]) -lt $umbral } | ForEach-Object { "p$_=" + [math]::Round($max[$_] / $alto[$_], 2) })
    $nimg = $d.InlineShapes.Count; $ntab = $d.Tables.Count
    $d.Close($no); $w.Quit($no)
    [pscustomobject]@{ paginas = $paginas; tablas = $ntab; imagenes = $nimg; separados = ($separados -join ' || '); nsep = $separados.Count; aisladas = ($aisladas -join ', '); naisl = $aisladas.Count; cabeceras = $cabeceras; vacias = ($vacias -join ', '); nvac = $vacias.Count; fuera = $fuera }
  }
  if (Wait-Job $j -Timeout $Limite) {
    $r = Receive-Job $j
    $filas += [pscustomobject]@{ documento = $a.Name; paginas = $r.paginas; tablas = $r.tablas; imagenes = $r.imagenes; unidos_separados = $r.nsep; filas_finales_aisladas = $r.naisl; cabeceras_separadas = $r.cabeceras; paginas_casi_vacias = $r.nvac; imagenes_fuera_de_margen = $r.fuera; detalle_unidos = $r.separados; detalle_aisladas = $r.aisladas; detalle_vacias = $r.vacias }
  } else {
    Stop-Job $j
    $filas += [pscustomobject]@{ documento = $a.Name; paginas = 'SIN RESPUESTA' }
  }
  Remove-Job $j -Force
  Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -ge $inicioTotal } | Stop-Process -Force -Confirm:$false
}
$filas | Export-Csv -Path $SalidaCsv -NoTypeInformation -Encoding UTF8
$filas | Format-Table documento, paginas, unidos_separados, filas_finales_aisladas, cabeceras_separadas, paginas_casi_vacias, imagenes_fuera_de_margen, detalle_vacias -AutoSize | Out-String -Width 200
