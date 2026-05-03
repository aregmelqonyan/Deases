# Bottlship — Կոդի Մանրամասն Բացատրություն

---

## Ծրագրի Ֆայլային Կառուցվածք

```
battleship_bot/
├── bot.py                  ← Գործարկման կետ
├── config_reader.py        ← .env կարդացող
├── requirements.txt        ← Կախվածություններ
├── models/                 ← Հիմնական խաղի տրամաբանություն
│   ├── board.py            ← Տախտակ
│   ├── boat.py             ← Նավ
│   ├── player.py           ← Խաղացող
│   ├── session.py          ← Խաղային նիստ
│   └── exces.py            ← Բացառություններ
├── new_models/             ← Բարձր մակարդակի վերացականություն
│   ├── gamer.py            ← Telegram+Խաղ միավոր
│   ├── pair_session.py     ← Զույգի կառավարում
│   └── matches.py          ← Բոլոր ակտիվ խաղերի կառավարիչ
├── handlers/               ← Telegram ինտեգրացիա
│   ├── cmd_handlers.py     ← Հրամանի handler-ներ
│   ├── callbacks.py        ← Callback տվյալների կլաս
│   ├── keyboards.py        ← Inline ստեղնաշարեր
│   └── updates.py          ← Տախտակ թարմացնող ֆունկցիաներ
└── states/
    └── game_state.py       ← FSM վիճակներ
```

---

## bot.py — Գործարկման Կետ

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config_reader import config
from handlers import cmd_handlers
from new_models import matches

async def main():
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    dp.include_router(cmd_handlers.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, matches=matches.Matches())

asyncio.run(main())
```

### `main()` ֆունկցիա
**Նպատակ:** Բոտի ամբողջ ցիկլը գործարկել:

| Քայլ | Գործողություն | Բացատրություն |
|------|--------------|---------------|
| 1 | `Bot(token=...)` | Ստեղծում է Telegram Bot օբյեկտ՝ թոքենով |
| 2 | `Dispatcher()` | Ստեղծում է հաղորդագրություն-ուղղորդիչ |
| 3 | `include_router(...)` | Cmd handler-ները գրանցում է dispatcher-ում |
| 4 | `delete_webhook(...)` | Webhook-ը մաքրում է, որ polling-ն ճիշտ աշխատի |
| 5 | `start_polling(bot, matches=...)` | Սկսում է Telegram-ից հաղորդագրություններ ստանալ; `matches`-ն ներարկվում է handler-ներ |

`asyncio.run(main())` — ամբողջ ծրագիրը ասինխրոն event loop-ի մեջ գործարկելու Python-ի ստանդարտ ձև:

---

## config_reader.py — Կոնֆիգուրացիա

```python
from pydantic import BaseSettings, SecretStr

class Settings(BaseSettings):
    bot_token: SecretStr

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Settings()
```

### `Settings` կլաս
**Նպատակ:** `.env` ֆայլից `BOT_TOKEN` փոփոխականը կարդալ:

- `SecretStr` — պահում է թոքենն անվտանգ (`.get_secret_value()` կանչի ժամանակ հասանելի)
- `BaseSettings` — Pydantic-ի ծնող կլաս, որն ավտոմատ կերպով env ֆայլը վերծանում է
- `config = Settings()` — ֆայլի բեռնման ժամանակ ստեղծվում է global singleton

---

## models/exces.py — Բացառություններ

```python
class BoatOrientationError(Exception): pass
class BoatCollisionError(Exception): pass
class BoardIndexError(Exception): pass
```

| Բացառություն | Երբ է բարձրանում |
|-------------|-----------------|
| `BoatOrientationError` | Նավի կոորդինատները անկյունագծային են (ոչ հորիզոնական, ոչ ուղղաձիգ) |
| `BoatCollisionError` | Նավը տեղադրվում է արդեն զբաղված բջջի վրա |
| `BoardIndexError` | Կոորդինատները տախտակի սահմաններից դուրս են |

---

## models/boat.py — Նավի Կլաս

```python
class Boat:
    def __init__(self, head: tuple, tail: tuple):
        self.head = head
        self.tail = tail
        self.check_valid_coords()
        self.length = self._calc_length()
        self.health = self.length
        self.is_alive = True
```

### `__init__(head, tail)`
**Նպատակ:** Ստեղծել Boat օբյեկտ՝ head և tail կոորդինատներով:

- `head` — նավի սկզբի բջջի (i, j) կոորդինատ
- `tail` — նավի վերջի բջջի (i, j) կոորդինատ
- `length` — նավի երկարությունը (tail - head + 1)
- `health` — մնացած «կյանքերի» քանակը (սկզբում = length)
- `is_alive` — `True` քանի դեռ health > 0

---

### `check_valid_coords()`
**Նպատակ:** Ստուգել, որ նավը ոչ անկյունագծային է:

```python
def check_valid_coords(self):
    if self.head[0] != self.tail[0] and self.head[1] != self.tail[1]:
        raise BoatOrientationError("Boat must be horizontal or vertical")
```

Եթե և՛ շարքը, և՛ սյունն են տարբեր, ուրեմն անկյունագծային է — սխալ:

---

### `get_all_coords()`
**Նպատակ:** Վերադարձնել նավի բոլոր բջիջների ցուցակը:

```python
def get_all_coords(self) -> list:
    coords = []
    if self.head[0] == self.tail[0]:   # հորիզոնական
        for j in range(self.head[1], self.tail[1] + 1):
            coords.append((self.head[0], j))
    else:                               # ուղղաձիգ
        for i in range(self.head[0], self.tail[0] + 1):
            coords.append((i, self.head[1]))
    return coords
```

---

### `being_hitted()`
**Նպատակ:** Գրանցել, որ նավն հարվածվել է:

```python
def being_hitted(self):
    self.health -= 1
    if self.health == 0:
        self.is_alive = False
```

`health` 0-ի դեպքում `is_alive` դառնում է `False` (նավ խորտակված):

---

## models/board.py — Տախտակի Կլաս

Ներկայացնում է 8×8 ցանց, որտեղ տեղադրվում և հետևվում են նավերը:

```python
class Board:
    EMPTY = 0       # դատարկ ջուր
    BOAT = 1        # նավ
    HIT_WATER = 2   # ջրում բաց կրակ
    HIT_BOAT = 3    # նավ խոցված
    SUNKEN = 4      # նավ խորտակված
    UNKNOWN = 5     # անհայտ (հակառակ կողմ)
```

### `__init__(size=8, ships=None)`
**Նպատակ:** Ստեղծել դատարկ տախտակ:

```python
def __init__(self, size=8, ships=None):
    self.size = size
    self.ships = ships or {4: 1, 3: 2, 2: 3}
    self.grid = [[0] * size for _ in range(size)]
    self.boats = []
    self.free_cells = []
    self.update_free_cells()
```

- `grid` — 8×8 ցուցակ (list of lists), արժեքներ 0-5
- `ships` — կոնֆիգ: {4: 1, 3: 2, 2: 3} = 4-երկ. 1հ., 3-երկ. 2հ., 2-երկ. 3հ.
- `free_cells` — ցուցակ հասանելի (0-արժեք) բջիջների

---

### `_is_valid_pos(i, j)`
**Նպատակ:** Ստուգել, որ (i, j)-ն տախտակի սահմաններում է:

```python
def _is_valid_pos(self, i, j) -> bool:
    return 0 <= i < self.size and 0 <= j < self.size
```

---

### `_is_available_cell(i, j)`
**Նպատակ:** Ստուգել, որ (i, j) և նրա 8 հարևան բջիջները ազատ են (ոչ BOAT):

```python
def _is_available_cell(self, i, j) -> bool:
    for di in [-1, 0, 1]:
        for dj in [-1, 0, 1]:
            ni, nj = i + di, j + dj
            if self._is_valid_pos(ni, nj) and self.grid[ni][nj] == self.BOAT:
                return False
    return True
```

Սա ապահովում է, որ երկու նավ չեն հպվում (անգամ անկյունով):

---

### `update_free_cells()`
**Նպատակ:** Վերահաշվել ազատ բջիջների ցուցակը:

```python
def update_free_cells(self):
    self.free_cells = [
        (i, j)
        for i in range(self.size)
        for j in range(self.size)
        if self.grid[i][j] == self.EMPTY
    ]
```

---

### `set_value_at(i, j, value)`
**Նպատակ:** Սահմանել grid-ի արժեքն (i, j)-ում՝ ստուգումով:

```python
def set_value_at(self, i, j, value):
    if not self._is_valid_pos(i, j):
        raise BoardIndexError(f"Position ({i},{j}) is out of bounds")
    self.grid[i][j] = value
```

---

### `set_boat(boat)`
**Նպատակ:** Տախտակի վրա Boat օբյեկտ տեղադրել:

```python
def set_boat(self, boat: Boat):
    for (i, j) in boat.get_all_coords():
        if not self._is_available_cell(i, j):
            raise BoatCollisionError(f"Cell ({i},{j}) is not available")
        self.set_value_at(i, j, self.BOAT)
    self.boats.append(boat)
    self.update_free_cells()
```

Ամեն կոորդինատում ստուգվում է հասանելությունը, ապա բջիջը `1`-ի (BOAT) արժեք է ստանում:

---

### `has_boat_at(i, j)`
**Նպատակ:** Ստուգել՝ (i, j)-ում BOAT արժեք կա՞:

```python
def has_boat_at(self, i, j) -> bool:
    return self.grid[i][j] == self.BOAT
```

---

### `being_hitted_at(i, j)`
**Նպատակ:** Գրանցել հարձակում (i, j) կոորդինատում:

```python
def being_hitted_at(self, i, j) -> bool:
    if self.has_boat_at(i, j):
        # Գտնել, թե որ Boat օբյեկտն է
        for boat in self.boats:
            if (i, j) in boat.get_all_coords():
                boat.being_hitted()
                if not boat.is_alive:
                    # Ամբողջ նավը SUNKEN (4)
                    for (bi, bj) in boat.get_all_coords():
                        self.set_value_at(bi, bj, self.SUNKEN)
                else:
                    self.set_value_at(i, j, self.HIT_BOAT)
                return True
    else:
        self.set_value_at(i, j, self.HIT_WATER)
        return False
```

**Վերադարձ:** `True` — եթե հարվածը նավ է, `False` — եթե ջուր:

---

### `get_horizontal_segments()` / `get_vertical_segments()`
**Նպատակ:** Գտնել տախտակի վրա հորիզոնական / ուղղաձիգ հաջորդական ազատ հատվածներ (segments), որտեղ կարելի է նավ տեղադրել:

Օգտագործվում է `random_init()` ֆունկցիայի կողմից:

---

### `random_init()`
**Նպատակ:** Ավտոմատ (պատահական) կերպով ամբողջ տախտակը ճիշտ կոնֆիգուրացիայով լրացնել:

```python
def random_init(self):
    for length, count in self.ships.items():
        for _ in range(count):
            placed = False
            attempts = 0
            while not placed and attempts < 100:
                # Ընտրել ուղղություն (horizontal/vertical)
                # Ընտրել random segment
                # Ընտրել random position within segment
                # Փորձ set_boat(...)
                attempts += 1
            if not placed:
                # Reset and retry
                self.__init__()
                self.random_init()
                return
```

Ռեկուրսիան ապահովում է, որ ձախողման դեպքում ամեն ինչ վերսկսվի:

---

## models/player.py — Խաղացողի Կլաս

```python
class Player:
    def __init__(self, username: str, board: Board = None):
        self.username = username
        self.my_board = board or Board()
        self.other_board = Board()
        self.hit_history = []

        if board is None:
            self.my_board.random_init()
```

### `__init__(username, board)`
**Նպատակ:** Ստեղծել խաղացող:

- `my_board` — սեփական տախտակ (ամբողջ ճշմարտությամբ)
- `other_board` — հակառակ կողմի մոդել (ի սկզբանե ամբողջ UNKNOWN)
- `hit_history` — արդեն հարձակված կոորդինատների ցուցակ

---

### `hit_at(i, j)`
**Նպատակ:** Գրանցել, որ խաղացողը (i, j)-ին է հարձակվել:

```python
def hit_at(self, i, j):
    self.hit_history.append((i, j))
```

---

### `count_alive_boats()`
**Նպատակ:** Հաշվել, թե քանի կենդանի նավ կա տախտակում:

```python
def count_alive_boats(self) -> int:
    return sum(1 for boat in self.my_board.boats if boat.is_alive)
```

---

### `alive_boat_count` (property)
Ուղղակի կարճ ձև `count_alive_boats()`-ի՝

```python
@property
def alive_boat_count(self) -> int:
    return self.count_alive_boats()
```

---

## models/session.py — Խաղային Նիստ

```python
class GameSession:
    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.to_move = player1       # Ով ունի հերթ
        self.winner = None
        
        # Cross-reference boards
        player1.other_board = player2.my_board
        player2.other_board = player1.my_board
```

### `__init__(player1, player2)`
**Նպատակ:** Ստեղծել մրցաշարային նիստ:

`player1.other_board = player2.my_board` — Սա կենտրոնական linkage-ն է. Player1-ի «թշնամու» տախտակն ուղղակիորեն player2-ի «սեփական» տախտակն է:

---

### `check_game_over()`
**Նպատակ:** Ստուգել՝ խաղն ավա՞rti է:

```python
def check_game_over(self) -> bool:
    if self.player1.alive_boat_count == 0:
        self.winner = self.player2
        return True
    if self.player2.alive_boat_count == 0:
        self.winner = self.player1
        return True
    return False
```

---

### `move(i, j)`
**Նպատակ:** Կատարել հերթ՝ (i, j)-ին հարձակում:

```python
def move(self, i, j) -> bool:
    current = self.to_move
    opponent = self.player2 if current == self.player1 else self.player1
    
    hit = opponent.my_board.being_hitted_at(i, j)
    current.hit_at(i, j)
    
    if not hit:
        self.to_move = opponent    # Բաց — հերթ փոխանցում
    # Հաջողված հարձակման ժամ. հերթ ՉԻ փոխում
    
    return hit
```

**Վերադարձ:** `True` — հաջողված հարձակում, `False` — բաց:

---

## new_models/gamer.py — Telegram + Խաղ Միավոր

```python
class Gamer:
    EMOJI = {0: '🌊', 1: '🚢', 2: '❌', 3: '💥', 4: '🔥', 5: '▫️'}
    
    def __init__(self, user):
        self.user = user               # Aiogram User օբյեկտ
        self.player = Player(user.username)
        self.my_message = None         # Telegram message-ի reference
        self.other_message = None
```

### `__init__(user)`
**Նպատակ:** Telegram User-ի համար Gamer ստեղծել:

Ավտոմատ ստեղծում է `Player` օբյեկտ (random board-ով):

---

### `get_my_keyboard()`
**Նպատակ:** Վերադարձնել inline keyboard, որը ցուցադրում է **սեփական** տախտակը:

```python
def get_my_keyboard(self) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(8):
        for j in range(8):
            val = self.player.my_board.grid[i][j]
            emoji = self.EMOJI[val]
            builder.button(
                text=emoji,
                callback_data=MyCellCallback(row=i, col=j).pack()
            )
    builder.adjust(8)
    return builder.as_markup()
```

Ստեղծում է 8×8 Grid inline կոճակներ՝ grid-ի արժեքների հիման վրա emoji-ներով:

---

### `get_other_keyboard()`
**Նպատակ:** Վերադարձնել inline keyboard, որը ցուցադրում է **հակառակ կողմի** տախտակը (ծածկված անհայտ բջիջներով):

```python
def get_other_keyboard(self) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(8):
        for j in range(8):
            val = self.player.other_board.grid[i][j]
            # Եթե BOAT (1) — ծածկել (▫️)
            if val == Board.BOAT:
                emoji = self.EMOJI[Board.UNKNOWN]
            else:
                emoji = self.EMOJI[val]
            builder.button(
                text=emoji,
                callback_data=HitCellCallback(row=i, col=j).pack()
            )
    builder.adjust(8)
    return builder.as_markup()
```

Հակառակ կողմի `BOAT` (1) արժեքները ծածկված են `▫️`-ով, որ խաղացողն ամեն ինչ չտեսնի:

---

## new_models/pair_session.py — Զույգի Կառավարում

```python
import secrets
import string

class PairSession:
    def __init__(self, gamer1: Gamer):
        self.gamer1 = gamer1
        self.gamer2 = None
        self.session = None
        self.code = self._generate_code()
    
    def _generate_code(self) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))
```

### `_generate_code()`
**Նպատակ:** Ստեղծել 8-նիշ կրիptographically secure կոդ:

`secrets.choice` — ոչ կանոնավոր (cryptographically secure) random ֆունկցիա, ավելի ապահով `random.choice`-ից:

---

### `to_pair(gamer2)`
**Նպատակ:** Երկրորդ Gamer-ին ավելացնել և GameSession ստեղծել:

```python
def to_pair(self, gamer2: Gamer):
    self.gamer2 = gamer2
    self.session = GameSession(
        self.gamer1.player,
        self.gamer2.player
    )
```

---

### `__contains__(gamer)`
**Նպատակ:** Ստուգել՝ Gamer-ն այս session-ո՞ւம է:

```python
def __contains__(self, gamer: Gamer) -> bool:
    return gamer == self.gamer1 or gamer == self.gamer2
```

Թույլ է տալիս գրել `if gamer in pair_session:` Python-ական ոճով:

---

### `get_opponent(gamer)`
**Նպատակ:** Վերադարձնել գտնված gamer-ի հակառակ կողմը:

```python
def get_opponent(self, gamer: Gamer) -> Gamer:
    return self.gamer2 if gamer == self.gamer1 else self.gamer1
```

---

## new_models/matches.py — Ամբողջ Խաղերի Կառավարիչ

```python
class Matches:
    def __init__(self):
        self.data: dict = {}       # {(id1, id2): PairSession}
        self.gamers: list = []     # Բոլոր ակտիվ Gamer-ներ
        self.sessions: list = []   # Չկապված PairSession-ներ
```

### `add_session(session)`
**Նպատակ:** Չկապված (waiting) PairSession-ն ավելացնել:

```python
def add_session(self, session: PairSession):
    self.sessions.append(session)
```

---

### `add_match(session)`
**Նպատակ:** Կապված PairSession-ն sessions-ից data-ի (ակտիվ) տեղափոխել:

```python
def add_match(self, session: PairSession):
    key = (session.gamer1.user.id, session.gamer2.user.id)
    self.data[key] = session
    self.sessions.remove(session)
```

`key`-ն tuple է երկու Telegram user ID-ներից:

---

### `add_gamer(gamer)` / `delete_gamer(gamer)`
**Նպատակ:** Gamer ավելացնել / հեռացնել global ցուցակից:

```python
def add_gamer(self, gamer: Gamer):
    self.gamers.append(gamer)

def delete_gamer(self, gamer: Gamer):
    if gamer in self.gamers:
        self.gamers.remove(gamer)
```

---

### `get_gamer_by_id(id)`
**Նպատակ:** Telegram user ID-ով Gamer-ն գտնել:

```python
def get_gamer_by_id(self, id: int) -> Gamer | None:
    for gamer in self.gamers:
        if gamer.user.id == id:
            return gamer
    return None
```

---

### `get_session_by_code(code)`
**Նպատակ:** Կոդով waiting PairSession-ն գտնել:

```python
def get_session_by_code(self, code: str) -> PairSession | None:
    for session in self.sessions:
        if session.code == code:
            return session
    return None
```

Օգտագործվում է `/connect` հրամանով երկրորդ խաղացողի կողմից:

---

### `get_gamer_opponent_by_id(id)`
**Նպատակ:** Ըստ Telegram user ID-ի՝ գտնել հակառակ կողմի Gamer-ը:

```python
def get_gamer_opponent_by_id(self, id: int) -> Gamer | None:
    for key, session in self.data.items():
        if id in key:
            return session.get_opponent(self.get_gamer_by_id(id))
    return None
```

---

### `get_game_session_by_gamer(gamer)`
**Նպատակ:** Gamer-ի GameSession-ն գտնել:

```python
def get_game_session_by_gamer(self, gamer: Gamer) -> GameSession | None:
    gamer_id = gamer.user.id
    for key, pair_session in self.data.items():
        if gamer_id in key:
            return pair_session.session
    return None
```

---

### `delete_match_by_gamer_id(id)`
**Նպատակ:** Խաղ հեռացնել data-ից՝ ըստ user ID-ի:

```python
def delete_match_by_gamer_id(self, id: int):
    for key in list(self.data.keys()):
        if id in key:
            del self.data[key]
            break
```

---

## states/game_state.py — FSM Վիճակներ

```python
from aiogram.fsm.state import State, StatesGroup

class GameState(StatesGroup):
    new_game_state  = State()   # /start-ից հետո
    ready_state     = State()   # Կապված, բայց դեռ սկսված չէ
    gameplay_state  = State()   # Ակտիվ խաղ
    end_state       = State()   # Խաղ ավարտ
```

### Վիճակների Անցման Դիագրամ

```
[new_game_state]
      |
      | /new_game կամ /connect
      ↓
[ready_state]
      |
      | OK կոճակ (ReadyCallback)
      ↓
[gameplay_state]
      |
      | Հաղթող + EndCallback կամ /exit
      ↓
[end_state]
```

Aiogram FSM-ն ապահովում է, որ handler-ները կատարվեն **միայն** ճիշտ վիճակում:

---

## handlers/callbacks.py — Callback Տվյալների Կլաս

```python
from aiogram.filters.callback_data import CallbackData

class ReadyCallback(CallbackData, prefix="ready"):
    pass

class HitCellCallback(CallbackData, prefix="hit"):
    row: int
    col: int

class MyCellCallback(CallbackData, prefix="my"):
    row: int
    col: int

class ExitCallback(CallbackData, prefix="exit"):
    pass

class EndCallback(CallbackData, prefix="end"):
    pass
```

### Callback Data-ի Մեխանիկ
Aiogram-ն callback data-ն serialize/deserialize է string տեսքով:

`HitCellCallback(row=3, col=5).pack()` → `"hit:3:5"`

Երբ օգտատերն սեղմում է կոճակ, բոտն ստանում է `"hit:3:5"` string, Aiogram-ն ապա deserialize-ում և վերականգնում `HitCellCallback(row=3, col=5)`:

---

## handlers/keyboards.py — Inline Ստեղնաշարեր

```python
def get_ready_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="OK", callback_data=ReadyCallback().pack())
    return builder.as_markup()

def get_exit_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="OK", callback_data=ExitCallback().pack())
    return builder.as_markup()

def get_finish_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="OK", callback_data=EndCallback().pack())
    return builder.as_markup()
```

Յուրաքանչյուր ֆունկցիա ստեղծում է մեկ կոճակ ունեցող ստեղնաշար՝ տարբեր callback type-ի:

---

## handlers/updates.py — Տախտակ Թարմացնող Ֆունկցիաներ

```python
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

async def update_other_board(gamer: Gamer, session: GameSession):
    with suppress(TelegramBadRequest):
        await gamer.other_message.edit_reply_markup(
            reply_markup=gamer.get_other_keyboard()
        )

async def update_my_board(gamer: Gamer, session: GameSession):
    with suppress(TelegramBadRequest):
        await gamer.my_message.edit_reply_markup(
            reply_markup=gamer.get_my_keyboard()
        )
```

**`suppress(TelegramBadRequest)`** — Telegram-ն error է վերադարձնում, եթե հաղորդագրությունն արդեն նույն ինլայն keyboard-ն ունի: `suppress` ֆունկցիան ապահովում է, որ ծրագիրը crash չի անում:

---

## handlers/cmd_handlers.py — Հրամանի Handler-ներ

### `/start` Handler

```python
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(GameState.new_game_state)
    await message.answer(
        "Բարի գալուստ Bottlship-ում!\n"
        "/new_game - Նոր խաղ\n"
        "/connect <code> - Միանալ"
    )
```

**Նպատակ:** FSM վիճակ `new_game_state` սահմանել, ողջույնի հաղորդ. ուղարկել:

---

### `/new_game` Handler

```python
@router.message(Command("new_game"), StateFilter(GameState.new_game_state))
async def cmd_new_game(message: Message, state: FSMContext, matches: Matches):
    gamer = Gamer(message.from_user)
    session = PairSession(gamer)
    
    matches.add_gamer(gamer)
    matches.add_session(session)
    
    await state.set_state(GameState.ready_state)
    await message.answer(f"Ձեր կոդն է: {session.code}\nՈւղարկեք ընկերոջը!")
```

**Նպատակ:** Gamer + PairSession ստեղծել, matches-ում գրանցել, կոդ ուղարկել:

---

### `/connect` Handler

```python
@router.message(Command("connect"), StateFilter(GameState.new_game_state))
async def cmd_connect(message: Message, state: FSMContext, matches: Matches):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Կոդ նշեք: /connect <code>")
        return
    
    code = parts[1]
    session = matches.get_session_by_code(code)
    
    if session is None:
        await message.answer("Կոդ չի գտնվել")
        return
    
    gamer2 = Gamer(message.from_user)
    session.to_pair(gamer2)
    matches.add_gamer(gamer2)
    matches.add_match(session)
    
    await state.set_state(GameState.ready_state)
    
    # Ուղարկել OK կոճակ երկուսին
    await message.answer("Կապ հաստատված! Սեղմեք OK", reply_markup=get_ready_kb())
    await session.gamer1.user.send_message("Ընկեր միացավ! Սեղմեք OK", reply_markup=get_ready_kb())
```

**Նպատակ:** Կոդով session-ն գտնել, երկրորդ gamer-ին ավելացնել, match-ն ակտիվացնել:

---

### ReadyCallback Handler

```python
@router.callback_query(ReadyCallback.filter(), StateFilter(GameState.ready_state))
async def ready_handler(callback: CallbackQuery, state: FSMContext, matches: Matches):
    gamer = matches.get_gamer_by_id(callback.from_user.id)
    opponent = matches.get_gamer_opponent_by_id(callback.from_user.id)
    
    # Ուղարկել սեփական տախտակ
    gamer.my_message = await callback.message.answer(
        "Ձեր տախտակը:", reply_markup=gamer.get_my_keyboard()
    )
    # Ուղարկել հակ. կողմի տախտակ
    gamer.other_message = await callback.message.answer(
        "Հակ. կողմ:", reply_markup=gamer.get_other_keyboard()
    )
    
    await state.set_state(GameState.gameplay_state)
    await callback.answer()
```

---

### HitCellCallback Handler

```python
@router.callback_query(HitCellCallback.filter(), StateFilter(GameState.gameplay_state))
async def hit_handler(callback: CallbackQuery, callback_data: HitCellCallback,
                      state: FSMContext, matches: Matches):
    gamer = matches.get_gamer_by_id(callback.from_user.id)
    session = matches.get_game_session_by_gamer(gamer)
    
    # Ստուգել հերթ
    if session.to_move.username != gamer.player.username:
        await callback.answer("Ձեր հերթը չէ!")
        return
    
    i, j = callback_data.row, callback_data.col
    
    # Արդեն հարձակված?
    if (i, j) in gamer.player.hit_history:
        await callback.answer("Այս բջջն արդեն հարձակված է!")
        return
    
    hit = session.move(i, j)
    opponent = matches.get_gamer_opponent_by_id(callback.from_user.id)
    
    # Թարմացնել երկու կողմերի տախտակները
    await update_other_board(gamer, session)
    await update_my_board(opponent, session)
    
    # Ստուգել հաղթող
    if session.check_game_over():
        winner_name = session.winner.username
        await callback.message.answer(
            f"Խաղն ավարտ! Հաղթող՝ {winner_name}", reply_markup=get_finish_kb()
        )
    
    await callback.answer("Հիթ! 💥" if hit else "Բաց ❌")
```

---

### `/exit` Handler

```python
@router.message(Command("exit"))
async def cmd_exit(message: Message, state: FSMContext, matches: Matches):
    gamer = matches.get_gamer_by_id(message.from_user.id)
    opponent = matches.get_gamer_opponent_by_id(message.from_user.id)
    
    await state.clear()
    
    if gamer:
        matches.delete_match_by_gamer_id(gamer.user.id)
        matches.delete_gamer(gamer)
    
    if opponent:
        await opponent.user.send_message("Հակ. կողմը լքեց խաղը")
        matches.delete_gamer(opponent)
    
    await message.answer("Խաղն ավարտ", reply_markup=get_exit_kb())
```

---

## Ամբողջ Տվյալների Հոսքը

```
Telegram User-ը սեղմում է "hit" կոճակ
         ↓
Aiogram-ն callback data-ն ստանում է ("hit:3:5")
         ↓
HitCellCallback.filter()-ն ըndanishes ճանաչում
         ↓
hit_handler() կոչվում է
         ↓
matches.get_game_session_by_gamer() → GameSession
         ↓
session.move(3, 5) → Board.being_hitted_at(3, 5)
         ↓
Boat.being_hitted() կանչ (եթե BOAT-ն է)
         ↓
Board.grid թարմացվում
         ↓
update_other_board() + update_my_board()
         ↓
Gamer.get_other_keyboard() → 8x8 emoji grid
         ↓
message.edit_reply_markup() → Telegram UI թարմ.
```

---

## Emoji-Արժեք Կատու

| Emoji | int արժեք | Կոնստ. | Նկարագրություն |
|-------|-----------|---------|---------------|
| 🌊 | 0 | EMPTY | Ջուր (հարձակված չէ) |
| 🚢 | 1 | BOAT | Նավ (սեփ. տախ-ում միայն) |
| ❌ | 2 | HIT_WATER | Ջրում բաց կրակ |
| 💥 | 3 | HIT_BOAT | Նավ խոցված |
| 🔥 | 4 | SUNKEN | Նավ ամբողջ խորտ. |
| ▫️ | 5 | UNKNOWN | Անհայտ (հակ. կողմ) |

---

## Ամփոփ Դիագրամ

```
bot.py
  └── Dispatcher (Aiogram)
        └── cmd_handlers.router
              ├── /start → GameState.new_game_state
              ├── /new_game → Gamer + PairSession → Matches.add_session()
              ├── /connect → PairSession.to_pair() → Matches.add_match()
              ├── ReadyCallback → Gamer.get_my_keyboard() / get_other_keyboard()
              ├── HitCellCallback → GameSession.move() → Board.being_hitted_at()
              ├── EndCallback → Matches.delete_match_by_gamer_id()
              └── /exit → State.clear() + cleanup

Matches (global state)
  ├── data: {(id1,id2): PairSession}
  ├── gamers: [Gamer, ...]
  └── sessions: [PairSession, ...]  ← waiting

PairSession
  ├── gamer1: Gamer
  ├── gamer2: Gamer
  ├── code: "xBpkMfHA"
  └── session: GameSession
        ├── player1: Player
        │     ├── my_board: Board (grid 8x8, boats[])
        │     └── other_board: → player2.my_board (same reference)
        └── player2: Player
              ├── my_board: Board (grid 8x8, boats[])
              └── other_board: → player1.my_board (same reference)
```
