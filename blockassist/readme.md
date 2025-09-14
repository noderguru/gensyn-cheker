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
<img width="589" height="346" alt="image" src="https://github.com/user-attachments/assets/eccb5b28-7dde-454a-881f-88b40302239e" />

<img width="397" height="210" alt="image" src="https://github.com/user-attachments/assets/f8bfdaf7-fd3d-4e7e-8e2a-1b2fd80ed9dc" />


