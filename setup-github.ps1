#!/usr/bin/env powershell
<#
.SYNOPSIS
    Clean unnecessary files dan prepare untuk GitHub
#>

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ProManage GitHub Setup & Cleanup      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan

# Files yang perlu dihapus
$filesToDelete = @(
    'deploy.tar.gz',
    'deploy.zip',
    'promanage_build.base64',
    'promanage_build.zip',
    'apply_final_protocol_fix.sh',
    'apply_ssl_fix.js',
    'auto_deploy_promanage.js',
    'check_db.js',
    'debug_deploy.js',
    'diagnose_login.js',
    'final_deploy.js',
    'fix_nginx.js',
    'fix_permissions.js',
    'fix_promanage_vps.sh',
    'inspect_ssl.js',
    'inspect_vps.js',
    'refine_diagnose.js',
    'reset-db-users.bat',
    'reset-db.js',
    'reset-users.py',
    'test-login.py',
    'test_results_detailed.json',
    'backend_test.py',
    'business_rule_test.py',
    'contracts.md',
    'DEPLOY_RDP_WINDOWS.md',
    'DEPLOY_VPS.md',
    'fix-login.ps1',
    'fix_login.py',
    'deploy-to-vps.ps1',
    'update-deployment.ps1',
    'update-deployment.js',
    'verify-deployment.js'
)

# Step 1: Delete files
Write-Host "`n[1] Deleting unnecessary files..." -ForegroundColor Yellow
$count = 0
foreach ($file in $filesToDelete) {
    $path = Join-Path (Get-Location) $file
    if (Test-Path $path) {
        Remove-Item $path -Force -ErrorAction SilentlyContinue
        Write-Host "  - Deleted: $file" -ForegroundColor Gray
        $count++
    }
}
Write-Host "  Deleted: $count files" -ForegroundColor Green

# Step 2: Git status
Write-Host "`n[2] Checking git..." -ForegroundColor Yellow
if (Test-Path '.git') {
    Write-Host "  Git repository found" -ForegroundColor Green
} else {
    Write-Host "  Initializing git..." -ForegroundColor Yellow
    git init
}

# Step 3: Add files
Write-Host "`n[3] Adding files to git..." -ForegroundColor Yellow
git add -A
Write-Host "  Files added" -ForegroundColor Green

# Step 4: Status
Write-Host "`n[4] Git status:" -ForegroundColor Yellow
git status --short

Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Create repo on GitHub (https://github.com/new)" -ForegroundColor Gray
Write-Host "  2. Get your username" -ForegroundColor Gray
Write-Host "  3. Run: git branch -M main" -ForegroundColor Cyan
Write-Host "  4. Run: git remote add origin https://github.com/USERNAME/ProManage.git" -ForegroundColor Cyan
Write-Host "  5. Run: git push -u origin main" -ForegroundColor Cyan
