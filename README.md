# Приложения для управления проектами

1. Для запуска при помощи docker используйте

```bash
docker compose up -d
```

2. Для запуска вне контейнеров

    1. Запустите базу

    ```bash
    docker compose up -d db
    ```

    2. Измените .env файлы в корне (для бекенда), в папке front

    3. Создайте виртаульное окружение python(3.12), установите зависимости, запустите бекенд

    ```bash
    poetry install
    cd src
    uvicorn app:app --host=0.0.0.0
    ```

    4. В отдельной сесси терминала запустите тестовый сервер фронтенда

    ```bash
    cd front
    npm i
    npm run dev
    ```
