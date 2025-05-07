# Log Analyzer
## Анализатор логов для создания отчета в HTML
## Для запуска 
### 1. Склонировать и перейти в репозиторий
```
https://github.com/dmitryeskov/log_analyzer_homework.git
```
### 2. Установить необходимые зависимости
```
pip install -r requirements.txt
```
### 3. Создать в репозитории каталог log и добавить логи для обработки
```
mkdir log
```

### 4. Запустить
### По умолчанию скрипт ищет последний (по дате в названии файла) лог в папке log
### Отчеты сохраняет в папку reports
### Отчеты формируются по шаблону report.html из templates
```
python log_analyzer.py
```

### 5. Чтобы запустить с другой конфигурацией, нужно указать путь к файлу через --config
```
python log_analyzer.py --config config.json
```

