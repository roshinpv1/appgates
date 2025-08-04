@echo off
setlocal enabledelayedexpansion

REM CodeGates Repository Scanner for Windows
REM This script makes a scan API call to the CodeGates server, waits for completion,
REM and saves the results (HTML and JSON reports) to the current directory.
REM
REM Usage:
REM     scan_repository.bat <api_endpoint> <repository_url> <branch> [git_token]
REM
REM Example:
REM     scan_repository.bat http://localhost:8000 https://github.com/owner/repo main
REM     scan_repository.bat http://localhost:8000 https://github.com/owner/repo main your_github_token

REM Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell available'" >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: PowerShell is required for this script to work
    echo Please ensure PowerShell is installed and available
    exit /b 1
)

REM Parse command line arguments
if "%~1"=="" (
    echo ❌ Error: Missing API endpoint
    echo Usage: %0 ^<api_endpoint^> ^<repository_url^> ^<branch^> [git_token]
    echo Example: %0 http://localhost:8000 https://github.com/owner/repo main
    exit /b 1
)

if "%~2"=="" (
    echo ❌ Error: Missing repository URL
    echo Usage: %0 ^<api_endpoint^> ^<repository_url^> ^<branch^> [git_token]
    echo Example: %0 http://localhost:8000 https://github.com/owner/repo main
    exit /b 1
)

if "%~3"=="" (
    echo ❌ Error: Missing branch
    echo Usage: %0 ^<api_endpoint^> ^<repository_url^> ^<branch^> [git_token]
    echo Example: %0 http://localhost:8000 https://github.com/owner/repo main
    exit /b 1
)

set "API_ENDPOINT=%~1"
set "REPOSITORY_URL=%~2"
set "BRANCH=%~3"
set "GIT_TOKEN=%~4"

REM Remove trailing slash from API endpoint
set "API_ENDPOINT=%API_ENDPOINT:/=%"
if "%API_ENDPOINT:~-1%"=="\" set "API_ENDPOINT=%API_ENDPOINT:~0,-1%"

REM Validate inputs
echo %API_ENDPOINT% | findstr /i "^http://" >nul
if errorlevel 1 (
    echo %API_ENDPOINT% | findstr /i "^https://" >nul
    if errorlevel 1 (
        echo ❌ Error: API endpoint must start with http:// or https://
        exit /b 1
    )
)

echo %REPOSITORY_URL% | findstr /i "^http://" >nul
if errorlevel 1 (
    echo %REPOSITORY_URL% | findstr /i "^https://" >nul
    if errorlevel 1 (
        echo ❌ Error: Repository URL must start with http:// or https://
        exit /b 1
    )
)

echo 🚀 CodeGates Repository Scanner
echo ==================================================
echo 🔗 API Endpoint: %API_ENDPOINT%
echo 📁 Repository: %REPOSITORY_URL%
echo 🌿 Branch: %BRANCH%
echo 🔑 Token provided: %GIT_TOKEN%
if "%GIT_TOKEN%"=="" echo 🔑 Token provided: No
echo ==================================================

REM Test connection to API server
echo 🔍 Testing connection to API server...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/health' -Method GET -TimeoutSec 10; Write-Host '✅ Connected to CodeGates API server' } catch { Write-Host '❌ Failed to connect to API server:' $_.Exception.Message; exit 1 }"
if errorlevel 1 (
    echo ❌ Connection test failed
    exit /b 1
)

REM Start scan
echo 🚀 Starting scan for repository: %REPOSITORY_URL%
echo 📋 Branch: %BRANCH%

REM Prepare JSON payload
set "PAYLOAD={\"repository_url\":\"%REPOSITORY_URL%\",\"branch\":\"%BRANCH%\",\"report_format\":\"both\"}"
if not "%GIT_TOKEN%"=="" (
    set "PAYLOAD={\"repository_url\":\"%REPOSITORY_URL%\",\"branch\":\"%BRANCH%\",\"report_format\":\"both\",\"github_token\":\"%GIT_TOKEN%\"}"
)

REM Start scan using PowerShell
echo 🔍 Starting scan...
powershell -Command "try { $payload = '%PAYLOAD%' | ConvertFrom-Json; $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/scan' -Method POST -Body ($payload | ConvertTo-Json -Depth 10) -ContentType 'application/json' -TimeoutSec 30; $scanId = $response.scan_id; Write-Host '✅ Scan started successfully'; Write-Host '🆔 Scan ID:' $scanId; $scanId } catch { Write-Host '❌ Failed to start scan:' $_.Exception.Message; exit 1 }" > temp_scan_id.txt
if errorlevel 1 (
    echo ❌ Failed to start scan
    exit /b 1
)

REM Read scan ID from temp file
set /p SCAN_ID=<temp_scan_id.txt
del temp_scan_id.txt

echo ✅ Scan started successfully
echo 🆔 Scan ID: %SCAN_ID%

REM Wait for scan completion
echo ⏳ Waiting for scan completion (timeout: 15 minutes)...
set /a TIMEOUT_SECONDS=900
set /a ELAPSED_SECONDS=0
set /a CHECK_INTERVAL=5

:wait_loop
REM Get scan status
powershell -Command "try { $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/scan/%SCAN_ID%' -Method GET -TimeoutSec 10; $status = $response.status; $progress = $response.progress_percentage; $currentStep = $response.current_step; $stepDetails = $response.step_details; Write-Host $status; Write-Host $progress; Write-Host $currentStep; Write-Host $stepDetails; if ($response.errors) { $errors -join '; ' } } catch { Write-Host 'ERROR'; Write-Host $_.Exception.Message }" > temp_status.txt

REM Read status from temp file
set /p STATUS=<temp_status.txt
set /p PROGRESS=<temp_status.txt
set /p CURRENT_STEP=<temp_status.txt
set /p STEP_DETAILS=<temp_status.txt
set /p ERRORS=<temp_status.txt
del temp_status.txt

REM Check for errors
echo %ERRORS% | findstr /i "ERROR" >nul
if not errorlevel 1 (
    echo ❌ Error getting scan status: %ERRORS%
    exit /b 1
)

REM Display progress
if not "%PROGRESS%"=="" (
    echo 📊 Progress: %PROGRESS%%% - %CURRENT_STEP%
)
if not "%STEP_DETAILS%"=="" (
    echo    📋 %STEP_DETAILS%
)

REM Check scan status
if "%STATUS%"=="completed" (
    echo ✅ Scan completed successfully!
    goto download_reports
) else if "%STATUS%"=="failed" (
    echo ❌ Scan failed: %ERRORS%
    exit /b 1
) else if "%STATUS%"=="running" (
    REM Wait before next check
    timeout /t %CHECK_INTERVAL% /nobreak >nul
    set /a ELAPSED_SECONDS+=%CHECK_INTERVAL%
    
    REM Check timeout
    if %ELAPSED_SECONDS% gtr %TIMEOUT_SECONDS% (
        echo ❌ Scan timed out after 15 minutes
        exit /b 1
    )
    
    goto wait_loop
) else (
    echo ❌ Unexpected scan status: %STATUS%
    exit /b 1
)

:download_reports
REM Get scan results
echo 📊 Getting scan results...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/scan/%SCAN_ID%' -Method GET -TimeoutSec 10; $overallScore = $response.overall_score; $totalFiles = $response.total_files; $totalLines = $response.total_lines; $passedGates = $response.passed_gates; $failedGates = $response.failed_gates; $totalGates = $response.total_gates; Write-Host 'SUMMARY'; Write-Host $overallScore; Write-Host $totalFiles; Write-Host $totalLines; Write-Host $passedGates; Write-Host $failedGates; Write-Host $totalGates; ($response | ConvertTo-Json -Depth 10) } catch { Write-Host 'ERROR'; Write-Host $_.Exception.Message }" > temp_results.txt

REM Read summary from temp file
set /p SUMMARY_LINE=<temp_results.txt
if "%SUMMARY_LINE%"=="SUMMARY" (
    set /p OVERALL_SCORE=<temp_results.txt
    set /p TOTAL_FILES=<temp_results.txt
    set /p TOTAL_LINES=<temp_results.txt
    set /p PASSED_GATES=<temp_results.txt
    set /p FAILED_GATES=<temp_results.txt
    set /p TOTAL_GATES=<temp_results.txt
)

REM Display summary
echo.
echo 📊 Scan Summary:
echo    Overall Score: %OVERALL_SCORE%%%
echo    Total Files: %TOTAL_FILES%
echo    Total Lines: %TOTAL_LINES%
echo    Passed Gates: %PASSED_GATES%
echo    Failed Gates: %FAILED_GATES%
echo    Total Gates: %TOTAL_GATES%

REM Generate timestamp for unique filenames
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~2,2%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "Min=%dt:~10,2%"
set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
set "SCAN_ID_SHORT=%SCAN_ID:~0,8%"

REM Download HTML report
echo 📄 Downloading HTML report...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/scan/%SCAN_ID%/report/html' -Method GET -TimeoutSec 30; $response | Out-File -FilePath 'codegates_report_%SCAN_ID_SHORT%_%TIMESTAMP%.html' -Encoding UTF8; Write-Host '✅ HTML report saved' } catch { Write-Host '⚠️ Failed to download HTML report:' $_.Exception.Message }"

REM Download JSON report
echo 📄 Downloading JSON report...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/scan/%SCAN_ID%/report/json' -Method GET -TimeoutSec 30; $response | Out-File -FilePath 'codegates_report_%SCAN_ID_SHORT%_%TIMESTAMP%.json' -Encoding UTF8; Write-Host '✅ JSON report saved' } catch { Write-Host '⚠️ Failed to download JSON report:' $_.Exception.Message }"

REM Save scan summary
echo 📄 Saving scan summary...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%API_ENDPOINT%/api/v1/scan/%SCAN_ID%' -Method GET -TimeoutSec 10; ($response | ConvertTo-Json -Depth 10) | Out-File -FilePath 'codegates_summary_%SCAN_ID_SHORT%_%TIMESTAMP%.json' -Encoding UTF8; Write-Host '✅ Summary saved' } catch { Write-Host '⚠️ Failed to save summary:' $_.Exception.Message }"

echo.
echo ✅ All reports saved successfully!
echo    📄 HTML Report: codegates_report_%SCAN_ID_SHORT%_%TIMESTAMP%.html
echo    📄 JSON Report: codegates_report_%SCAN_ID_SHORT%_%TIMESTAMP%.json
echo    📄 Summary: codegates_summary_%SCAN_ID_SHORT%_%TIMESTAMP%.json
echo.
echo 🎉 Scan completed successfully!
exit /b 0 