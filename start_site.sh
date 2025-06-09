#!/bin/bash

# Переходимо в директорію з сайтом
cd "$(dirname "$0")"

# Запускаємо сайт у фоновому режимі
nohup python3 run_site.py > site_output.log 2>&1 &

# Зберігаємо PID процесу
echo $! > site.pid

echo "🌐 Сайт запущено в фоновому режимі"
echo "📝 Логи зберігаються в site_output.log"
echo "🆔 PID процесу збережено в site.pid" 