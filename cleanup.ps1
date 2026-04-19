Write-Host "Cleanup ProManage Repository" -ForegroundColor Cyan

# Files to delete
$files = @(
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

Write-Host "Deleting unnecessary files..." -ForegroundColor Yellow
$count = 0
foreach ($file in $files) {
    $path = Join-Path (Get-Location) $file
    if (Test-Path $path) {
        Remove-Item $path -Force -ErrorAction SilentlyContinue
        Write-Host "  - $file" -ForegroundColor Gray
        $count++
    }
}
Write-Host "Deleted $count files`n" -ForegroundColor Green

Write-Host "Initializing git..." -ForegroundColor Yellow
if (-not (Test-Path '.git')) {
    git init
}

Write-Host "Adding files..." -ForegroundColor Yellow
git add -A

Write-Host "`nGit Status:" -ForegroundColor Cyan
git status --short

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Create repository on GitHub at https://github.com/new" -ForegroundColor Gray
Write-Host "2. Replace USERNAME with your GitHub username:" -ForegroundColor Gray
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git remote add origin https://github.com/USERNAME/ProManage.git" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host "`nDone!" -ForegroundColor Green
