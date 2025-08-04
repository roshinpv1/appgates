@echo off
setlocal enabledelayedexpansion

REM CodeGates File Scanner for Windows
REM This script scans a local directory and extracts file information
REM similar to what the Python system does for repository analysis.
REM
REM Usage:
REM     file_scanner.bat <directory_path> [output_file]
REM
REM Example:
REM     file_scanner.bat C:\my-project
REM     file_scanner.bat C:\my-project scan_results.json

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell available'" >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: PowerShell is required for this script to work
    echo Please ensure PowerShell is installed and available
    exit /b 1
)

REM Parse command line arguments
if "%~1"=="" (
    echo ❌ Error: Missing directory path
    echo Usage: %0 ^<directory_path^> [output_file]
    echo Example: %0 C:\my-project
    echo Example: %0 C:\my-project scan_results.json
    exit /b 1
)

set "SCAN_DIR=%~1"
set "OUTPUT_FILE=%~2"

REM Check if directory exists
if not exist "%SCAN_DIR%" (
    echo ❌ Error: Directory does not exist: %SCAN_DIR%
    exit /b 1
)

REM Set default output file if not provided
if "%OUTPUT_FILE%"=="" (
    set "OUTPUT_FILE=file_scan_results.json"
)

echo 🚀 CodeGates File Scanner for Windows
echo ==================================================
echo 📁 Scan Directory: %SCAN_DIR%
echo 📄 Output File: %OUTPUT_FILE%
echo ==================================================

REM Create PowerShell script for file scanning
echo Creating file scanner...
powershell -Command "& {
    param($scanDir, $outputFile)
    
    try {
        # Initialize results
        $results = @{
            scan_directory = $scanDir
            scan_timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            total_files = 0
            total_lines = 0
            file_list = @()
            language_stats = @{}
            file_types = @{}
            extensions = @{}
        }
        
        # Define file type mappings
        $fileTypeMap = @{
            '.py' = 'Python'
            '.js' = 'JavaScript'
            '.ts' = 'TypeScript'
            '.java' = 'Java'
            '.cpp' = 'C++'
            '.c' = 'C'
            '.cs' = 'C#'
            '.php' = 'PHP'
            '.rb' = 'Ruby'
            '.go' = 'Go'
            '.rs' = 'Rust'
            '.swift' = 'Swift'
            '.kt' = 'Kotlin'
            '.scala' = 'Scala'
            '.html' = 'HTML'
            '.css' = 'CSS'
            '.scss' = 'SCSS'
            '.sass' = 'Sass'
            '.xml' = 'XML'
            '.json' = 'JSON'
            '.yaml' = 'YAML'
            '.yml' = 'YAML'
            '.toml' = 'TOML'
            '.ini' = 'INI'
            '.cfg' = 'Config'
            '.conf' = 'Config'
            '.md' = 'Markdown'
            '.txt' = 'Text'
            '.sql' = 'SQL'
            '.sh' = 'Shell'
            '.bat' = 'Batch'
            '.ps1' = 'PowerShell'
            '.dockerfile' = 'Dockerfile'
            '.dockerignore' = 'Dockerignore'
            '.gitignore' = 'Gitignore'
            '.gitattributes' = 'Gitattributes'
        }
        
        # Define file context mappings
        $fileContextMap = @{
            'Source Code' = @('.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala')
            'Configuration' = @('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.dockerfile', '.dockerignore', '.gitignore', '.gitattributes')
            'Documentation' = @('.md', '.txt', '.rst', '.adoc')
            'Web' = @('.html', '.css', '.scss', '.sass', '.xml')
            'Database' = @('.sql')
            'Scripts' = @('.sh', '.bat', '.ps1')
        }
        
        # Get all files recursively
        Write-Host '🔍 Scanning directory...'
        $files = Get-ChildItem -Path $scanDir -Recurse -File | Where-Object { $_.FullName -notmatch '\\\.git\\' -and $_.FullName -notmatch '\\node_modules\\' -and $_.FullName -notmatch '\\\.venv\\' -and $_.FullName -notmatch '\\venv\\' -and $_.FullName -notmatch '\\__pycache__\\' }
        
        Write-Host "📊 Found $($files.Count) files"
        
        foreach ($file in $files) {
            $extension = $file.Extension.ToLower()
            $relativePath = $file.FullName.Substring($scanDir.Length + 1).Replace('\', '/')
            
            # Determine file type
            $fileType = if ($fileTypeMap.ContainsKey($extension)) { $fileTypeMap[$extension] } else { 'Unknown' }
            
            # Determine file context
            $fileContext = 'Other'
            foreach ($context in $fileContextMap.Keys) {
                if ($fileContextMap[$context] -contains $extension) {
                    $fileContext = $context
                    break
                }
            }
            
            # Count lines
            $lineCount = 0
            try {
                $content = Get-Content -Path $file.FullName -Raw -ErrorAction SilentlyContinue
                if ($content) {
                    $lineCount = ($content -split "`n").Count
                }
            } catch {
                $lineCount = 0
            }
            
            # Check if binary
            $isBinary = $false
            try {
                $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
                $nullCount = ($bytes | Where-Object { $_ -eq 0 }).Count
                $isBinary = $nullCount -gt ($bytes.Count * 0.1) -or $extension -in @('.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.zip', '.tar', '.gz', '.rar', '.7z', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')
            } catch {
                $isBinary = $false
            }
            
            # Create file info
            $fileInfo = @{
                path = $relativePath
                name = $file.Name
                extension = $extension
                size = $file.Length
                lines = $lineCount
                language = $fileType
                type = $fileContext
                is_binary = $isBinary
                relative_path = $relativePath
                created = $file.CreationTime.ToString('yyyy-MM-dd HH:mm:ss')
                modified = $file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
            }
            
            $results.file_list += $fileInfo
            $results.total_files++
            $results.total_lines += $lineCount
            
            # Update language stats
            if (-not $results.language_stats.ContainsKey($fileType)) {
                $results.language_stats[$fileType] = @{ files = 0; lines = 0 }
            }
            $results.language_stats[$fileType].files++
            $results.language_stats[$fileType].lines += $lineCount
            
            # Update file type stats
            if (-not $results.file_types.ContainsKey($fileContext)) {
                $results.file_types[$fileContext] = 0
            }
            $results.file_types[$fileContext]++
            
            # Update extension stats
            if (-not $results.extensions.ContainsKey($extension)) {
                $results.extensions[$extension] = 0
            }
            $results.extensions[$extension]++
        }
        
        # Calculate additional statistics
        $results.average_file_size = if ($results.total_files -gt 0) { [math]::Round($results.file_list | Measure-Object -Property size -Average).Average, 2) } else { 0 }
        $results.average_lines_per_file = if ($results.total_files -gt 0) { [math]::Round($results.total_lines / $results.total_files, 2) } else { 0 }
        
        # Get top languages by file count
        $results.top_languages = $results.language_stats.GetEnumerator() | Sort-Object { $_.Value.files } -Descending | Select-Object -First 10 | ForEach-Object { @{ language = $_.Key; files = $_.Value.files; lines = $_.Value.lines } }
        
        # Get top file types
        $results.top_file_types = $results.file_types.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10 | ForEach-Object { @{ type = $_.Key; count = $_.Value } }
        
        # Get top extensions
        $results.top_extensions = $results.extensions.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10 | ForEach-Object { @{ extension = $_.Key; count = $_.Value } }
        
        # Save results to JSON
        $results | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputFile -Encoding UTF8
        
        Write-Host '✅ File scan completed successfully!'
        Write-Host "📊 Total files: $($results.total_files)"
        Write-Host "📊 Total lines: $($results.total_lines)"
        Write-Host "📊 Average file size: $($results.average_file_size) bytes"
        Write-Host "📊 Average lines per file: $($results.average_lines_per_file)"
        Write-Host "📄 Results saved to: $outputFile"
        
        # Display top languages
        Write-Host '🏆 Top Languages:'
        foreach ($lang in $results.top_languages) {
            Write-Host "   $($lang.language): $($lang.files) files, $($lang.lines) lines"
        }
        
        # Display top file types
        Write-Host '📁 Top File Types:'
        foreach ($type in $results.top_file_types) {
            Write-Host "   $($type.type): $($type.count) files"
        }
        
    } catch {
        Write-Host '❌ Error during file scan:' $_.Exception.Message
        exit 1
    }
}" "%SCAN_DIR%" "%OUTPUT_FILE%"

if errorlevel 1 (
    echo ❌ File scan failed
    exit /b 1
)

echo.
echo 🎉 File scan completed successfully!
echo 📄 Results saved to: %OUTPUT_FILE%
echo.
echo 💡 You can now use this file with the CodeGates API for analysis
exit /b 0 