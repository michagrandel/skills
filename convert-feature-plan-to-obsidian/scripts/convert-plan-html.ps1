[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string] $SourceDirectory,

    [string] $OutputDirectory,

    [string] $VaultPath,

    [string] $ProjectDirectory,

    [string] $ProjectName,

    [string[]] $HtmlFiles,

    [switch] $Overwrite
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($OutputDirectory) -eq [string]::IsNullOrWhiteSpace($VaultPath)) {
    throw 'Specify exactly one destination mode: -OutputDirectory or -VaultPath.'
}
if (-not [string]::IsNullOrWhiteSpace($OutputDirectory) -and -not [string]::IsNullOrWhiteSpace($ProjectName)) {
    throw '-ProjectName can only be used with -VaultPath.'
}
if (-not [string]::IsNullOrWhiteSpace($SourceDirectory) -and $HtmlFiles.Count -gt 0) {
    throw 'Specify either -SourceDirectory or -HtmlFiles, not both.'
}
if ($HtmlFiles.Count -gt 0 -and [string]::IsNullOrWhiteSpace($OutputDirectory) -and [string]::IsNullOrWhiteSpace($ProjectDirectory) -and [string]::IsNullOrWhiteSpace($ProjectName)) {
    throw 'When using -HtmlFiles, specify -ProjectDirectory or -ProjectName so notes are placed in the correct project.'
}

function Convert-InlineHtml {
    param([Parameter(Mandatory = $true)][string] $Value)

    $Value = [regex]::Replace($Value, '(?is)<(strong|b)\b[^>]*>(.*?)</\1>', '**$2**')
    $Value = [regex]::Replace($Value, '(?is)<(em|i)\b[^>]*>(.*?)</\1>', '*$2*')
    $Value = [regex]::Replace($Value, '(?is)<code\b[^>]*>(.*?)</code>', '`$1`')
    $Value = [regex]::Replace($Value, '(?is)<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', '[$2]($1)')
    $Value = [regex]::Replace($Value, '(?i)<br\s*/?>', ' <br> ')
    $Value = [regex]::Replace($Value, '(?s)<[^>]+>', '')
    $Value = [Net.WebUtility]::HtmlDecode($Value)
    return (($Value -replace '[ \t\r\n]+', ' ').Trim())
}

function Add-PreservedBlock {
    param(
        [Parameter(Mandatory = $true)][string] $Text,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]] $Blocks
    )

    $Index = $Blocks.Count
    $Blocks.Add($Text)
    return "`n`n@@OBSIDIAN_BLOCK_$Index@@`n`n"
}

function Convert-Callout {
    param(
        [Parameter(Mandatory = $true)][string] $Kind,
        [Parameter(Mandatory = $true)][string] $InnerHtml
    )

    $HeadingMatch = [regex]::Match($InnerHtml, '(?is)<h[1-6]\b[^>]*>(.*?)</h[1-6]>')
    $Title = if ($HeadingMatch.Success) { Convert-InlineHtml $HeadingMatch.Groups[1].Value } else { 'Note' }
    $Body = $InnerHtml
    if ($HeadingMatch.Success) {
        $Body = $Body.Remove($HeadingMatch.Index, $HeadingMatch.Length)
    }

    $Lines = [System.Collections.Generic.List[string]]::new()
    foreach ($Item in [regex]::Matches($Body, '(?is)<li\b[^>]*>(.*?)</li>')) {
        $Text = Convert-InlineHtml $Item.Groups[1].Value
        if ($Text) { $Lines.Add("- $Text") }
    }
    foreach ($Paragraph in [regex]::Matches($Body, '(?is)<p\b[^>]*>(.*?)</p>')) {
        $Text = Convert-InlineHtml $Paragraph.Groups[1].Value
        if ($Text) { $Lines.Add($Text) }
    }
    if ($Lines.Count -eq 0) {
        $Text = Convert-InlineHtml $Body
        if ($Text) { $Lines.Add($Text) }
    }

    $Callout = [System.Collections.Generic.List[string]]::new()
    $Callout.Add("> [!$Kind] $Title")
    foreach ($Line in $Lines) {
        foreach ($SubLine in ($Line -split '\r?\n')) {
            $Callout.Add("> $SubLine")
        }
    }
    return ($Callout -join "`n")
}

function Convert-Table {
    param(
        [Parameter(Mandatory = $true)][string] $TableHtml,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][System.Collections.Generic.List[string]] $Blocks
    )

    $Rows = [System.Collections.Generic.List[string]]::new()
    foreach ($Row in [regex]::Matches($TableHtml, '(?is)<tr\b[^>]*>(.*?)</tr>')) {
        $Cells = [System.Collections.Generic.List[string]]::new()
        foreach ($Cell in [regex]::Matches($Row.Groups[1].Value, '(?is)<t[hd]\b[^>]*>(.*?)</t[hd]>')) {
            $Text = Convert-InlineHtml $Cell.Groups[1].Value
            $Text = $Text.Replace('|', '\|')
            $Cells.Add($Text)
        }
        if ($Cells.Count -gt 0) {
            $Rows.Add('| ' + ($Cells -join ' | ') + ' |')
        }
    }

    if ($Rows.Count -eq 0) { return '' }
    $ColumnCount = [regex]::Matches($Rows[0], '\|').Count - 1
    $Separator = '| ' + ((1..$ColumnCount | ForEach-Object { '---' }) -join ' | ') + ' |'
    $Rows.Insert(1, $Separator)
    return Add-PreservedBlock -Text ($Rows -join "`n") -Blocks $Blocks
}

$ProjectDirectory = if ([string]::IsNullOrWhiteSpace($ProjectDirectory)) { '' } else { [IO.Path]::GetFullPath($ProjectDirectory) }
if ($ProjectDirectory -and -not (Test-Path -LiteralPath $ProjectDirectory -PathType Container)) {
    throw "Project directory does not exist: '$ProjectDirectory'."
}
if ($SourceDirectory) {
    $SourceDirectory = [IO.Path]::GetFullPath($SourceDirectory)
    if (-not (Test-Path -LiteralPath $SourceDirectory -PathType Container)) {
        throw "Source directory does not exist: '$SourceDirectory'."
    }
}
elseif ($HtmlFiles.Count -eq 0) {
    if (-not $ProjectDirectory) {
        throw 'Specify -ProjectDirectory to use the default <project>\doc\plans source, or specify -SourceDirectory / -HtmlFiles.'
    }
    $SourceDirectory = Join-Path $ProjectDirectory 'doc\plans'
    if (-not (Test-Path -LiteralPath $SourceDirectory -PathType Container)) {
        throw "Default plan source directory '$SourceDirectory' does not exist. Ask the user which HTML files should be transferred, then pass their exact paths with -HtmlFiles, or ask for a different source directory."
    }
}
if ($SourceDirectory) {
    $SourceDirectory = [IO.Path]::GetFullPath($SourceDirectory)
}
if ($HtmlFiles.Count -gt 0) {
    $Files = @(
        foreach ($HtmlFile in $HtmlFiles) {
            $FilePath = [IO.Path]::GetFullPath($HtmlFile)
            if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
                throw "Selected HTML file does not exist: '$HtmlFile'."
            }
            if ([IO.Path]::GetExtension($FilePath) -ine '.html') {
                throw "Selected file is not an HTML document: '$HtmlFile'."
            }
            Get-Item -LiteralPath $FilePath
        }
    ) | Sort-Object FullName -Unique
}
else {
    $Files = @(Get-ChildItem -LiteralPath $SourceDirectory -File -Filter '*.html' -Recurse | Sort-Object FullName)
}
if ($Files.Count -eq 0) {
    throw "No HTML files were found in '$SourceDirectory'."
}

$OutputDirectoryHandled = $false
if (-not [string]::IsNullOrWhiteSpace($VaultPath)) {
    $VaultPath = [IO.Path]::GetFullPath($VaultPath)
    if (-not (Test-Path -LiteralPath $VaultPath -PathType Container)) {
        throw "Obsidian vault does not exist: '$VaultPath'."
    }

    if ([string]::IsNullOrWhiteSpace($ProjectName)) {
        if ($ProjectDirectory) {
            $ProjectName = Split-Path -Leaf $ProjectDirectory
        }
        elseif ($SourceDirectory -match '(?i)[\\/]doc[\\/]plans$') {
            $ProjectName = Split-Path -Leaf (Split-Path -Parent (Split-Path -Parent $SourceDirectory))
        }
        else {
            $ProjectName = Split-Path -Leaf (Split-Path -Parent $SourceDirectory)
        }
    }
    if ([string]::IsNullOrWhiteSpace($ProjectName) -or $ProjectName -in @('.', '..')) {
        throw "Could not determine a valid project name from source directory '$SourceDirectory'. Pass -ProjectName."
    }
    if ($ProjectName.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0 -or $ProjectName -match '[<>:"/\\|?*]') {
        throw "Invalid project folder name: '$ProjectName'."
    }

    $ProjectsRoots = @(Get-ChildItem -LiteralPath $VaultPath -Directory | Where-Object { $_.Name -ieq 'Projekte' })
    if ($ProjectsRoots.Count -gt 1) {
        throw "Multiple folders named 'Projekte' were found in '$VaultPath'; resolve the vault structure before importing."
    }
    if ($ProjectsRoots.Count -eq 0) {
        throw "The Obsidian vault '$VaultPath' has no 'Projekte' folder."
    }
    $ProjectsRoot = $ProjectsRoots[0].FullName

    $ProjectFolders = @(Get-ChildItem -LiteralPath $ProjectsRoot -Directory | Where-Object { $_.Name -ieq $ProjectName })
    if ($ProjectFolders.Count -gt 1) {
        throw "Multiple project folders match '$ProjectName' in '$ProjectsRoot'; choose the correct project explicitly."
    }
    if ($ProjectFolders.Count -eq 0) {
        $ProjectDirectory = Join-Path $ProjectsRoot $ProjectName
        if ($PSCmdlet.ShouldProcess($ProjectDirectory, 'Create project folder under Projekte')) {
            [IO.Directory]::CreateDirectory($ProjectDirectory) | Out-Null
        }
    }
    else {
        $ProjectDirectory = $ProjectFolders[0].FullName
    }

    $PlanDirectories = @(Get-ChildItem -LiteralPath $ProjectDirectory -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq 'Planing' })
    if ($PlanDirectories.Count -gt 1) {
        throw "Multiple Planing folders were found in '$ProjectDirectory'; resolve them before importing."
    }
    if ($PlanDirectories.Count -eq 0) {
        $OutputDirectory = Join-Path $ProjectDirectory 'Planing'
        if ($PSCmdlet.ShouldProcess($OutputDirectory, 'Create project Planing folder')) {
            [IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
        }
        $OutputDirectoryHandled = $true
    }
    else {
        $OutputDirectory = $PlanDirectories[0].FullName
    }
}
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
if (-not $OutputDirectoryHandled -and -not (Test-Path -LiteralPath $OutputDirectory -PathType Container)) {
    if ($PSCmdlet.ShouldProcess($OutputDirectory, 'Create destination directory')) {
        [IO.Directory]::CreateDirectory($OutputDirectory) | Out-Null
    }
}

$Created = 0
$Skipped = 0
foreach ($File in $Files) {
    $Html = [IO.File]::ReadAllText($File.FullName)
    $Html = [regex]::Replace($Html, '(?s)<!--.*?-->', '')
    $Main = [regex]::Match($Html, '(?is)<main\b[^>]*>(.*?)</main>')
    if (-not $Main.Success) {
        throw "The HTML page '$($File.Name)' has no <main> element."
    }

    $Content = $Main.Groups[1].Value
    $TitleMatch = [regex]::Match($Content, '(?is)<h1\b[^>]*>(.*?)</h1>')
    if (-not $TitleMatch.Success) {
        throw "The HTML page '$($File.Name)' has no title <h1>."
    }
    $Title = Convert-InlineHtml $TitleMatch.Groups[1].Value
    if (-not $Title) {
        throw "The HTML page '$($File.Name)' has an empty title."
    }
    $SummaryMatch = [regex]::Match($Content, '(?is)<p\b[^>]*class="[^"]*\bhero-sub\b[^"]*"[^>]*>(.*?)</p>')
    $Summary = if ($SummaryMatch.Success) { Convert-InlineHtml $SummaryMatch.Groups[1].Value } else { '' }

    $Content = [regex]::Replace($Content, '(?is)<div\b[^>]*class="[^"]*\bhero\b[^"]*"[^>]*>.*?</div>', '')
    $Content = [regex]::Replace($Content, '(?is)<button\b[^>]*>.*?</button>', '')
    $Content = [regex]::Replace($Content, '(?is)<svg\b[^>]*>.*?</svg>', '')
    $Content = [regex]::Replace($Content, '(?is)<pre\b[^>]*class="[^"]*\bmermaid\b[^"]*"[^>]*>.*?</pre>', '')

    $Blocks = [System.Collections.Generic.List[string]]::new()
    $Content = [regex]::Replace($Content, '(?is)<div\b[^>]*class="[^"]*\b(pro|con|reco)\b[^"]*"[^>]*>(.*?)</div>', {
        param($Match)
        $Kind = switch ($Match.Groups[1].Value.ToLowerInvariant()) {
            'pro' { 'success' }
            'con' { 'failure' }
            'reco' { 'info' }
        }
        $Callout = Convert-Callout -Kind $Kind -InnerHtml $Match.Groups[2].Value
        return Add-PreservedBlock -Text $Callout -Blocks $Blocks
    })

    $Content = [regex]::Replace($Content, '(?is)<pre\b([^>]*)>(.*?)</pre>', {
        param($Match)
        $Attributes = $Match.Groups[1].Value
        $Inner = $Match.Groups[2].Value
        $Language = ''
        if ($Attributes -match '(?i)\bmm-src\b') {
            $Language = 'mermaid'
        }
        elseif ($Inner -match '(?i)\blanguage-([\w+#.-]+)') {
            $Language = $Matches[1]
        }
        $Code = [regex]::Replace($Inner, '(?i)<br\s*/?>', "`n")
        $Code = [regex]::Replace($Code, '(?s)<[^>]+>', '')
        $Code = [Net.WebUtility]::HtmlDecode($Code).Trim("`r", "`n")
        $Fence = [string]::Concat('```', $Language, "`n", $Code, "`n", '```')
        return Add-PreservedBlock -Text $Fence -Blocks $Blocks
    })

    $Content = [regex]::Replace($Content, '(?is)<table\b[^>]*>.*?</table>', {
        param($Match)
        return Convert-Table -TableHtml $Match.Value -Blocks $Blocks
    })
    $Content = [regex]::Replace($Content, '(?is)<summary\b[^>]*>(.*?)</summary>', {
        param($Match)
        $Text = Convert-InlineHtml $Match.Groups[1].Value
        if ($Text -match '^Mermaid source') { return "`n*$Text*`n`n" }
        if ($Text) { return "`n**$Text**`n`n" }
        return ''
    })
    $Content = [regex]::Replace($Content, '(?is)<blockquote\b[^>]*>(.*?)</blockquote>', {
        param($Match)
        $Text = Convert-InlineHtml $Match.Groups[1].Value
        if ($Text) { return "`n> $Text`n`n" }
        return ''
    })
    $Content = [regex]::Replace($Content, '(?is)<(strong|b)\b[^>]*>(.*?)</\1>', '**$2**')
    $Content = [regex]::Replace($Content, '(?is)<(em|i)\b[^>]*>(.*?)</\1>', '*$2*')
    $Content = [regex]::Replace($Content, '(?is)<code\b[^>]*>(.*?)</code>', '`$1`')
    $Content = [regex]::Replace($Content, '(?is)<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', '[$2]($1)')
    $Content = [regex]::Replace($Content, '(?is)<span\b[^>]*>(.*?)</span>', '$1 ')
    $Content = [regex]::Replace($Content, '(?is)<h1\b[^>]*>.*?</h1>', '')
    for ($Level = 2; $Level -le 6; $Level++) {
        $Tag = "h$Level"
        $Prefix = '#' * $Level
        $Content = [regex]::Replace($Content, "(?is)<$Tag\b[^>]*>(.*?)</$Tag>", {
            param($Match)
            $Heading = Convert-InlineHtml $Match.Groups[1].Value
            if ($Heading -match '^(\d+)([^.\s])') {
                $Heading = $Matches[1] + ' ' + $Heading.Substring($Matches[1].Length)
            }
            if ($Heading) { return "`n$Prefix $Heading`n`n" }
            return ''
        })
    }
    $Content = [regex]::Replace($Content, '(?is)<p\b[^>]*>', "`n")
    $Content = [regex]::Replace($Content, '(?is)</p>', "`n`n")
    $Content = [regex]::Replace($Content, '(?is)<li\b[^>]*>', "`n- ")
    $Content = [regex]::Replace($Content, '(?is)</li>', '')
    $Content = [regex]::Replace($Content, '(?is)<(ul|ol)\b[^>]*>', "`n")
    $Content = [regex]::Replace($Content, '(?is)</(ul|ol)>', "`n")
    $Content = [regex]::Replace($Content, '(?i)<br\s*/?>', "`n")
    $Content = [regex]::Replace($Content, '(?i)<hr\s*/?>', "`n---`n")
    $Content = [regex]::Replace($Content, '(?is)</?(section|div|details|article|header|footer|tbody|thead|tr)\b[^>]*>', "`n")
    $Content = [regex]::Replace($Content, '(?is)<[^>]+>', '')
    $Content = [Net.WebUtility]::HtmlDecode($Content)
    $Content = [regex]::Replace($Content, '\[(ASSUMPTION|OPEN QUESTION): ([^\]]+)\]', '*$1: $2*')
    $Content = [regex]::Replace($Content, '[ \t]+', ' ')
    $Content = [regex]::Replace($Content, " *`n *", "`n")
    $Content = [regex]::Replace($Content, '(?m)^(- .*)\r?\n(?:\r?\n)+(?=- )', "`$1`n")
    $Content = [regex]::Replace($Content, "`n{3,}", "`n`n").Trim()
    if ($Summary) {
        $Content = "*Feature Plan*`n`n$Summary`n`n$Content"
    }

    for ($Index = 0; $Index -lt $Blocks.Count; $Index++) {
        $Content = $Content.Replace("@@OBSIDIAN_BLOCK_$Index@@", $Blocks[$Index])
    }
    if ([regex]::IsMatch($Content, '@@OBSIDIAN_BLOCK_\d+@@')) {
        throw "Internal Markdown block marker remained while converting '$($File.Name)'."
    }

    $PrefixMatch = [regex]::Match($File.BaseName, '^(\d+)')
    $Prefix = if ($PrefixMatch.Success) { $PrefixMatch.Groups[1].Value + ' - ' } else { '' }
    $SafeTitle = [regex]::Replace($Title, '[<>:"/\\|?*]', '-').Trim().TrimEnd('.')
    $Destination = Join-Path $OutputDirectory ($Prefix + $SafeTitle + '.md')
    if ((Test-Path -LiteralPath $Destination -PathType Leaf) -and -not $Overwrite) {
        Write-Output "SKIPPED (exists): $Destination"
        $Skipped++
        continue
    }

    $Action = if (Test-Path -LiteralPath $Destination) { 'Replace Markdown note' } else { 'Create Markdown note' }
    if ($PSCmdlet.ShouldProcess($Destination, $Action)) {
        [IO.File]::WriteAllText($Destination, $Content, [Text.UTF8Encoding]::new($false))
        Write-Output "CREATED: $Destination"
        $Created++
    }
}

Write-Output "Finished. Created or updated: $Created; skipped existing: $Skipped."
