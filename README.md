# Тестовое задание Brandquad

### Комментарии:
* Для управления зависимостями и сокращения команд использовал [pipenv](https://github.com/pypa/pipenv) 
* Для соединения через прокси использовал переменные окружения `http_proxy` и `https_proxy`

### Установка зависимостей:
```
$ pipenv sync
```

### Запуск парсинга:
```
$ pipenv run crawl <path/to/result/output.jsonlines>
```
