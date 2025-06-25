# ============================================================================
# Скрипт автоматической очистки среды разработки Windows
# Автор: Flask Helpdesk Development Team
# Версия: 1.0
# Дата: 2024
# ============================================================================

<#
.SYNOPSIS
    Автоматическая очистка временных файлов и папок в среде разработки Windows

.DESCRIPTION
    Безопасно удаляет временные файлы, кэши, логи и артефакты сборки.
    Поддерживает проекты Python, Node.js, .NET, Visual Studio и Cursor IDE.

.EXAMPLE
    .\cleanup_dev_environment.ps1
    Запуск интерактивной очистки с подтверждением

.EXAMPLE
    .\cleanup_dev_environment.ps1 -Force
    Автоматическая очистка без подтверждения (для CI/CD)
#>

param(
    [switch]$Force,          # Принудительная очистка без подтверждения
    [switch]$DryRun,         # Режим симуляции (только показать что будет удалено)
    [string]$Path = ".",     # Путь для сканирования (по умолчанию текущая папка)
    [switch]$Verbose         # Подробный вывод
)

# ============================================================================
# КОНФИГУРАЦИЯ ОЧИСТКИ
# ============================================================================

# Расширения файлов для удаления
$FileExtensionsToDelete = @(
    # Системные временные файлы Windows
    "*.tmp", "*.temp", "*.bak", "*.backup", "*.old", "*.orig",

    # Логи и отладочная информация
    "*.log", "*.log.*", "*.out", "*.err", "*.debug",

    # Артефакты компиляции
    "*.obj", "*.o", "*.bin", "*.exe.config", "*.pdb", "*.ilk",

    # Python временные файлы
    "*.pyc", "*.pyo", "*.pyd", "*.egg-info",

    # Node.js и JavaScript
    "*.min.js.map", "*.css.map", "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*",

    # .NET артефакты
    "*.cache", "*.suo", "*.sdf", "*.opensdf", "*.user", "*.userosscache", "*.sln.docstates",

    # IDE временные файлы
    "*.swp", "*.swo", "*~", ".DS_Store", "Thumbs.db", "desktop.ini",

    # Специфичные для проекта
    "flask_session_*", "celerybeat-schedule*", "*.sqlite-journal"
)

# Папки для полного удаления
$DirectoriesToDelete = @(
    # Python кэши и сборки
    "__pycache__", "*.egg-info", ".pytest_cache", ".coverage", ".tox",
    ".mypy_cache", ".hypothesis", "build", "dist", ".eggs",

    # Node.js зависимости (осторожно!)
    # "node_modules", # Раскомментировать только если уверены

    # .NET временные папки
    "bin", "obj", ".vs", "packages", "TestResults",

    # IDE конфигурации (осторожно!)
    ".vscode/settings.json.bak", ".idea/workspace.xml",

    # Cursor IDE кэши
    ".cursor", ".cursor-settings",

    # Git временные файлы
    ".git/objects/tmp_*", ".git/COMMIT_EDITMSG.backup",

    # Системные папки
    "$RECYCLE.BIN", "System Volume Information",

    # Специфичные для Flask проекта
    "flask_session", "logs/app_*.log", "migrations/__pycache__"
)

# Крупные файлы (больше указанного размера в MB)
$LargeFileSizeMB = 100
$LargeFileExtensions = @("*.log", "*.dump", "*.dmp", "*.core")

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Format-FileSize {
    param([long]$Size)

    if ($Size -gt 1GB) {
        return "{0:N2} GB" -f ($Size / 1GB)
    } elseif ($Size -gt 1MB) {
        return "{0:N2} MB" -f ($Size / 1MB)
    } elseif ($Size -gt 1KB) {
        return "{0:N2} KB" -f ($Size / 1KB)
    } else {
        return "$Size байт"
    }
}

function Get-SafePath {
    param([string]$Path)

    # Защита от удаления системных папок
    $DangerousPaths = @(
        "C:\Windows", "C:\Program Files", "C:\Program Files (x86)",
        "C:\Users\Public", "C:\ProgramData", "C:\System32"
    )

    $FullPath = (Resolve-Path -Path $Path -ErrorAction SilentlyContinue).Path

    foreach ($DangerousPath in $DangerousPaths) {
        if ($FullPath -like "$DangerousPath*") {
            Write-ColorOutput "⚠️  ПРЕДУПРЕЖДЕНИЕ: Сканирование системной папки $FullPath отклонено!" "Red"
            return $null
        }
    }

    return $FullPath
}

# ============================================================================
# ОСНОВНЫЕ ФУНКЦИИ СКАНИРОВАНИЯ
# ============================================================================

function Find-TemporaryFiles {
    param([string]$SearchPath)

    Write-ColorOutput "🔍 Сканирование временных файлов в: $SearchPath" "Cyan"

    $FilesToDelete = @()
    $TotalSize = 0

    # Поиск файлов по расширениям
    foreach ($Extension in $FileExtensionsToDelete) {
        try {
            $Files = Get-ChildItem -Path $SearchPath -Filter $Extension -Recurse -File -ErrorAction SilentlyContinue

            foreach ($File in $Files) {
                # Пропускаем файлы в системных папках
                if ($File.FullName -notlike "*\Windows\*" -and $File.FullName -notlike "*\Program Files*") {
                    $FilesToDelete += $File
                    $TotalSize += $File.Length

                    if ($Verbose) {
                        Write-ColorOutput "  📄 $($File.FullName) ($(Format-FileSize $File.Length))" "Gray"
                    }
                }
            }
        }
        catch {
            Write-ColorOutput "⚠️  Ошибка поиска $Extension : $($_.Exception.Message)" "Yellow"
        }
    }

    # Поиск крупных лог-файлов
    foreach ($Extension in $LargeFileExtensions) {
        try {
            $LargeFiles = Get-ChildItem -Path $SearchPath -Filter $Extension -Recurse -File -ErrorAction SilentlyContinue |
                         Where-Object { ($_.Length / 1MB) -gt $LargeFileSizeMB }

            foreach ($File in $LargeFiles) {
                if ($File -notin $FilesToDelete) {
                    $FilesToDelete += $File
                    $TotalSize += $File.Length

                    Write-ColorOutput "  📊 КРУПНЫЙ ФАЙЛ: $($File.FullName) ($(Format-FileSize $File.Length))" "Magenta"
                }
            }
        }
        catch {
            Write-ColorOutput "⚠️  Ошибка поиска крупных файлов: $($_.Exception.Message)" "Yellow"
        }
    }

    return @{
        Files = $FilesToDelete
        TotalSize = $TotalSize
        Count = $FilesToDelete.Count
    }
}

function Find-TemporaryDirectories {
    param([string]$SearchPath)

    Write-ColorOutput "📁 Сканирование временных папок в: $SearchPath" "Cyan"

    $DirectoriesToDeleteFound = @()
    $TotalSize = 0

    foreach ($DirPattern in $DirectoriesToDelete) {
        try {
            # Поиск точных совпадений папок
            $Directories = Get-ChildItem -Path $SearchPath -Filter $DirPattern -Recurse -Directory -ErrorAction SilentlyContinue

            foreach ($Directory in $Directories) {
                # Безопасность: не удаляем папки в системных путях
                if ($Directory.FullName -notlike "*\Windows\*" -and
                    $Directory.FullName -notlike "*\Program Files*" -and
                    $Directory.FullName -notlike "*\.git\objects\pack*") {  # Сохраняем важные git объекты

                    try {
                        $DirSize = (Get-ChildItem -Path $Directory.FullName -Recurse -File -ErrorAction SilentlyContinue |
                                   Measure-Object -Property Length -Sum).Sum

                        if ($DirSize -eq $null) { $DirSize = 0 }

                        $DirectoriesToDeleteFound += @{
                            Path = $Directory.FullName
                            Size = $DirSize
                            FileCount = (Get-ChildItem -Path $Directory.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
                        }

                        $TotalSize += $DirSize

                        if ($Verbose) {
                            Write-ColorOutput "  📂 $($Directory.FullName) ($(Format-FileSize $DirSize))" "Gray"
                        }
                    }
                    catch {
                        Write-ColorOutput "⚠️  Ошибка оценки размера $($Directory.FullName): $($_.Exception.Message)" "Yellow"
                    }
                }
            }
        }
        catch {
            Write-ColorOutput "⚠️  Ошибка поиска папок $DirPattern : $($_.Exception.Message)" "Yellow"
        }
    }

    return @{
        Directories = $DirectoriesToDeleteFound
        TotalSize = $TotalSize
        Count = $DirectoriesToDeleteFound.Count
    }
}

# ============================================================================
# ФУНКЦИИ ОТОБРАЖЕНИЯ И ПОДТВЕРЖДЕНИЯ
# ============================================================================

function Show-CleanupSummary {
    param(
        [hashtable]$FilesResult,
        [hashtable]$DirectoriesResult
    )

    Write-ColorOutput "`n" "White"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"
    Write-ColorOutput "           📋 ОТЧЕТ О НАЙДЕННЫХ ФАЙЛАХ ДЛЯ ОЧИСТКИ" "Blue"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"

    # Статистика файлов
    Write-ColorOutput "`n📄 ВРЕМЕННЫЕ ФАЙЛЫ:" "Green"
    Write-ColorOutput "   Количество: $($FilesResult.Count) файлов" "White"
    Write-ColorOutput "   Общий размер: $(Format-FileSize $FilesResult.TotalSize)" "White"

    if ($FilesResult.Count -gt 0 -and $Verbose) {
        Write-ColorOutput "`n   Примеры файлов:" "Gray"
        $FilesResult.Files | Select-Object -First 10 | ForEach-Object {
            Write-ColorOutput "   • $($_.Name) ($(Format-FileSize $_.Length))" "Gray"
        }
        if ($FilesResult.Count -gt 10) {
            Write-ColorOutput "   ... и еще $($FilesResult.Count - 10) файлов" "Gray"
        }
    }

    # Статистика папок
    Write-ColorOutput "`n📁 ВРЕМЕННЫЕ ПАПКИ:" "Green"
    Write-ColorOutput "   Количество: $($DirectoriesResult.Count) папок" "White"
    Write-ColorOutput "   Общий размер: $(Format-FileSize $DirectoriesResult.TotalSize)" "White"

    if ($DirectoriesResult.Count -gt 0 -and $Verbose) {
        Write-ColorOutput "`n   Найденные папки:" "Gray"
        $DirectoriesResult.Directories | Select-Object -First 10 | ForEach-Object {
            Write-ColorOutput "   • $($_.Path) ($(Format-FileSize $_.Size), $($_.FileCount) файлов)" "Gray"
        }
        if ($DirectoriesResult.Count -gt 10) {
            Write-ColorOutput "   ... и еще $($DirectoriesResult.Count - 10) папок" "Gray"
        }
    }

    # Общая статистика
    $TotalSize = $FilesResult.TotalSize + $DirectoriesResult.TotalSize
    $TotalItems = $FilesResult.Count + $DirectoriesResult.Count

    Write-ColorOutput "`n💾 ОБЩИЙ ИТОГ:" "Yellow"
    Write-ColorOutput "   Всего элементов: $TotalItems" "White"
    Write-ColorOutput "   Будет освобождено: $(Format-FileSize $TotalSize)" "White"

    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"

    return $TotalSize -gt 0
}

function Confirm-Cleanup {
    param([hashtable]$FilesResult, [hashtable]$DirectoriesResult)

    if ($Force) {
        Write-ColorOutput "🚀 Принудительный режим: очистка без подтверждения" "Yellow"
        return $true
    }

    if ($DryRun) {
        Write-ColorOutput "🔍 Режим симуляции: файлы НЕ будут удалены" "Blue"
        return $false
    }

    $TotalItems = $FilesResult.Count + $DirectoriesResult.Count
    if ($TotalItems -eq 0) {
        Write-ColorOutput "✨ Временные файлы не найдены! Среда разработки уже чистая." "Green"
        return $false
    }

    Write-ColorOutput "`n❓ Подтверждение очистки:" "Yellow"
    Write-ColorOutput "   Будет удалено $TotalItems элементов" "White"
    Write-ColorOutput "   Освобождено $(Format-FileSize ($FilesResult.TotalSize + $DirectoriesResult.TotalSize))" "White"
    Write-ColorOutput "`n⚠️  ВНИМАНИЕ: Это действие необратимо!" "Red"

    do {
        $Response = Read-Host "`n💬 Продолжить очистку? [Y/Да/N/Нет]"
        $Response = $Response.Trim().ToLower()
    } while ($Response -notin @("y", "yes", "да", "д", "n", "no", "нет", "н", ""))

    return $Response -in @("y", "yes", "да", "д")
}

# ============================================================================
# ФУНКЦИИ БЕЗОПАСНОГО УДАЛЕНИЯ
# ============================================================================

function Remove-TemporaryFiles {
    param([array]$Files)

    if ($Files.Count -eq 0) {
        return @{ Success = 0; Failed = 0; Size = 0 }
    }

    Write-ColorOutput "`n🗑️  Удаление временных файлов..." "Green"

    $SuccessCount = 0
    $FailedCount = 0
    $DeletedSize = 0

    foreach ($File in $Files) {
        try {
            $FileSize = $File.Length

            if ($DryRun) {
                Write-ColorOutput "   [СИМУЛЯЦИЯ] Удален: $($File.FullName)" "Blue"
            } else {
                Remove-Item -Path $File.FullName -Force -ErrorAction Stop
                Write-ColorOutput "   ✅ Удален: $($File.Name)" "Green"
            }

            $SuccessCount++
            $DeletedSize += $FileSize
        }
        catch {
            Write-ColorOutput "   ❌ ОШИБКА при удалении $($File.Name): $($_.Exception.Message)" "Red"
            $FailedCount++
        }
    }

    return @{
        Success = $SuccessCount
        Failed = $FailedCount
        Size = $DeletedSize
    }
}

function Remove-TemporaryDirectories {
    param([array]$Directories)

    if ($Directories.Count -eq 0) {
        return @{ Success = 0; Failed = 0; Size = 0 }
    }

    Write-ColorOutput "`n📁 Удаление временных папок..." "Green"

    $SuccessCount = 0
    $FailedCount = 0
    $DeletedSize = 0

    foreach ($Directory in $Directories) {
        try {
            $DirPath = $Directory.Path
            $DirSize = $Directory.Size

            if ($DryRun) {
                Write-ColorOutput "   [СИМУЛЯЦИЯ] Удалена папка: $DirPath" "Blue"
            } else {
                Remove-Item -Path $DirPath -Recurse -Force -ErrorAction Stop
                Write-ColorOutput "   ✅ Удалена папка: $(Split-Path $DirPath -Leaf)" "Green"
            }

            $SuccessCount++
            $DeletedSize += $DirSize
        }
        catch {
            Write-ColorOutput "   ❌ ОШИБКА при удалении папки $(Split-Path $Directory.Path -Leaf): $($_.Exception.Message)" "Red"
            $FailedCount++
        }
    }

    return @{
        Success = $SuccessCount
        Failed = $FailedCount
        Size = $DeletedSize
    }
}

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

function Start-DevelopmentCleanup {
    param([string]$TargetPath)

    $StartTime = Get-Date

    Write-ColorOutput "🚀 НАЧАЛО ОЧИСТКИ СРЕДЫ РАЗРАБОТКИ" "Green"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"
    Write-ColorOutput "Время запуска: $(Get-Date -Format 'dd.MM.yyyy HH:mm:ss')" "Gray"
    Write-ColorOutput "Целевой путь: $TargetPath" "Gray"
    Write-ColorOutput "Режим: $(if ($DryRun) { 'Симуляция' } elseif ($Force) { 'Принудительный' } else { 'Интерактивный' })" "Gray"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"

    # Проверка безопасности пути
    $SafePath = Get-SafePath -Path $TargetPath
    if (-not $SafePath) {
        Write-ColorOutput "❌ Очистка отменена из соображений безопасности." "Red"
        return
    }

    # Сканирование файлов и папок
    try {
        $FilesResult = Find-TemporaryFiles -SearchPath $SafePath
        $DirectoriesResult = Find-TemporaryDirectories -SearchPath $SafePath
    }
    catch {
        Write-ColorOutput "❌ Критическая ошибка при сканировании: $($_.Exception.Message)" "Red"
        return
    }

    # Отображение результатов
    $HasItemsToDelete = Show-CleanupSummary -FilesResult $FilesResult -DirectoriesResult $DirectoriesResult

    if (-not $HasItemsToDelete) {
        Write-ColorOutput "`n✨ Очистка не требуется!" "Green"
        return
    }

    # Подтверждение очистки
    $ConfirmCleanup = Confirm-Cleanup -FilesResult $FilesResult -DirectoriesResult $DirectoriesResult

    if (-not $ConfirmCleanup) {
        Write-ColorOutput "`n❌ Очистка отменена пользователем." "Yellow"
        return
    }

    # Выполнение очистки
    Write-ColorOutput "`n🔄 ВЫПОЛНЕНИЕ ОЧИСТКИ..." "Green"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"

    $FileCleanupResult = Remove-TemporaryFiles -Files $FilesResult.Files
    $DirectoryCleanupResult = Remove-TemporaryDirectories -Directories $DirectoriesResult.Directories

    # Финальный отчет
    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime

    Write-ColorOutput "`n📊 ФИНАЛЬНЫЙ ОТЧЕТ" "Green"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"
    Write-ColorOutput "Файлов удалено: $($FileCleanupResult.Success)/$($FilesResult.Count)" "White"
    Write-ColorOutput "Папок удалено: $($DirectoryCleanupResult.Success)/$($DirectoriesResult.Count)" "White"
    Write-ColorOutput "Ошибок: $($FileCleanupResult.Failed + $DirectoryCleanupResult.Failed)" "$(if ($FileCleanupResult.Failed + $DirectoryCleanupResult.Failed -gt 0) { 'Red' } else { 'Green' })"
    Write-ColorOutput "Освобождено места: $(Format-FileSize ($FileCleanupResult.Size + $DirectoryCleanupResult.Size))" "Green"
    Write-ColorOutput "Время выполнения: $($Duration.TotalSeconds.ToString('F2')) сек" "Gray"
    Write-ColorOutput "═══════════════════════════════════════════════════════════" "Blue"

    if ($FileCleanupResult.Failed + $DirectoryCleanupResult.Failed -eq 0) {
        Write-ColorOutput "✅ Очистка среды разработки завершена успешно!" "Green"
    } else {
        Write-ColorOutput "⚠️  Очистка завершена с ошибками. Проверьте права доступа." "Yellow"
    }
}

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

try {
    # Проверка версии PowerShell
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        Write-ColorOutput "❌ Требуется PowerShell 5.0 или выше!" "Red"
        exit 1
    }

    # Проверка прав администратора (рекомендуется)
    $IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

    if (-not $IsAdmin -and -not $DryRun) {
        Write-ColorOutput "⚠️  РЕКОМЕНДАЦИЯ: Запустите скрипт от имени администратора для лучших результатов." "Yellow"
        Write-ColorOutput "   Некоторые файлы могут быть недоступны для удаления." "Yellow"

        if (-not $Force) {
            $Response = Read-Host "`n❓ Продолжить без прав администратора? [Y/Да/N/Нет]"
            if ($Response.ToLower() -notin @("y", "yes", "да", "д")) {
                Write-ColorOutput "❌ Выполнение отменено." "Red"
                exit 0
            }
        }
    }

    # Запуск основной логики
    Start-DevelopmentCleanup -TargetPath $Path
}
catch {
    Write-ColorOutput "💥 КРИТИЧЕСКАЯ ОШИБКА: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Стек вызовов: $($_.ScriptStackTrace)" "Red"
    exit 1
}

Write-ColorOutput "`n🎯 Скрипт завершен. Нажмите любую клавишу для выхода..." "Gray"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
