# Тестовое задание Brandquad

### Комментарии:
* Для управления зависимостями и сокращения команд использовал [pipenv](https://github.com/pypa/pipenv) 
* Для соединения через прокси использовал переменные окружения `http_proxy` и `https_proxy`

### Установка зависимостей:
```
$ pipenv sync
```
или
```
$ pip install scrapy python-dotenv
```
### Запуск парсинга:
```
$ pipenv run crawl <path/to/result/output.jsonlines>
```
или
```
$ scrapy crawl products -O <path/to/result/output.jsonlines>
```
