Leaderboard Parser 🚀

This Python script performs the following tasks:

Fetches data from the Gensyn Swarm Leaderboard API.

Filters the results based on a list of IDs provided in the id.txt file. If an ID in the file starts with the prefix "F-", the prefix is removed automatically.

Displays a table in the console with two columns: ID and Score. The score is truncated (not rounded) to four decimal places.

Requirements
Python 3.x

```git glone https://github.com/noderguru/gensyn-cheker.git```

```cd gensyn-cheker```

requests library – Install it with:

```pip install requests```

How to Use

```nano id.txt```

Add your IDs to this file, one per line.
Example:

F-1cXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

F-75XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

Run the script:

```python3 gensyn-perserID_leaderboard.py```

Example Output

![image](https://github.com/user-attachments/assets/e26aed58-043a-41a0-9d33-efa1adea21cd)


ID can be seen in the container logs

```cd rl-swarm && docker-compose logs -f swarm_node```

![image](https://github.com/user-attachments/assets/93bd7518-8822-4f04-9f12-1b5d7b7751c1)



Парсер Leaderboard 🚀
Этот Python-скрипт выполняет следующие задачи:

Получает данные с API таблицы лидеров Gensyn Swarm.

Фильтрует результаты на основе списка ID, указанных в файле id.txt. Если ID в файле начинается с префикса "F-", префикс удаляется автоматически.

Выводит таблицу в консоли с двумя столбцами: ID и Score. Значение score обрезается (без округления) до четырех знаков после запятой.

Требования

Python 3.x

```git clone https://github.com/noderguru/gensyn-cheker.git```

```cd gensyn-cheker```

Библиотека requests – установите её с помощью:

```pip install requests```

Как использовать

Откройте файл id.txt:

```nano id.txt```

Добавьте свои ID в этот файл, по одному в строке.

Пример:

F-1cXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

F-75XXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

Запустите скрипт:

```python3 gensyn-perserID_leaderboard.py```

Пример вывода

![image](https://github.com/user-attachments/assets/e26aed58-043a-41a0-9d33-efa1adea21cd)

ID можно найти в логах контейнера:


```cd rl-swarm && docker-compose logs -f swarm_node```

![image](https://github.com/user-attachments/assets/93bd7518-8822-4f04-9f12-1b5d7b7751c1)
