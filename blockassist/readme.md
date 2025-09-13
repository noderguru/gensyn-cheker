## Чекер на активность BlockAssist через API дашборда с использованием резидентских прокси
<img width="1281" height="677" alt="image" src="https://github.com/user-attachments/assets/3b5c66f6-bb8e-4154-ba69-40cd0cd2e42b" />

### Качаем только чекер на blockassist
```bash
svn export https://github.com/noderguru/gensyn-cheker/trunk/blockassist /root/blockassist --force && cd /root/blockassist
```
### Создаём сессию
```bash
tmux new -s blockassist-cheker
````
### Ставим вирт. окружение и зависимости
```bash
python3 -m venv venv
source venv/bin/activate
```
```bash
pip install -r requirements.txt
```
### Заполняем своими данными файлы ```account_EOA.txt```  ```.env```   ```proxy.txt``` и стартуем

```bash
python3 blockassist-cheker.py
```

<img width="515" height="115" alt="image" src="https://github.com/user-attachments/assets/14d3df4c-155e-4198-b119-99521125427f" />


<img width="368" height="289" alt="image" src="https://github.com/user-attachments/assets/5b54329a-db89-444c-9a78-8ea0ac31604b" />

