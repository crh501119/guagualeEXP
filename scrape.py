import argparse
import json
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.taiwanlottery.com"
LIST_URL = f"{BASE_URL}/Instant/RWD/GetGameList?channel=M"
INFO_URL = f"{BASE_URL}/Instant/RWD/GetGameInfo?gameId={{}}"


def create_session() -> requests.Session:
    """Return a requests session with retry strategy."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        }
    )
    return session

@dataclass
class PrizeTier:
    amount: int
    total: int
    remaining: int

@dataclass
class ScratchGame:
    game_id: int
    name: str
    price: int
    prizes: List[PrizeTier] = field(default_factory=list)
    remain_total: int = 0

    def expected_value(self) -> float:
        total_remaining = self.remain_total or sum(t.remaining for t in self.prizes)
        if total_remaining == 0:
            return -self.price
        total_value = sum(_net_amount(t.amount) * t.remaining for t in self.prizes)
        return total_value / total_remaining - self.price

def _net_amount(amount: int) -> float:
    if amount > 5000:
        after_tax = amount * 0.8  # 20% winning tax
        after_tax *= 0.996        # 0.4% stamp tax
        return after_tax
    return float(amount)

def fetch_game_list(session: requests.Session) -> List[ScratchGame]:
    resp = session.get(LIST_URL, timeout=(3, 10))
    resp.raise_for_status()
    data = resp.json()
    games = []
    for g in data.get("GameList", []):
        if g.get("RemainTotal", 0) == 0:
            continue
        games.append(
            ScratchGame(
                game_id=g["GameID"],
                name=g["GameName"],
                price=g["Price"],
                remain_total=g.get("RemainTotal", 0),
            )
        )
    return games


def load_games_from_json(path: str) -> List[ScratchGame]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    games: List[ScratchGame] = []
    for g in data:
        prizes = [PrizeTier(**p) for p in g.get("prizes", [])]
        games.append(
            ScratchGame(
                game_id=g.get("game_id", 0),
                name=g.get("name", ""),
                price=g.get("price", 0),
                prizes=prizes,
                remain_total=sum(p.remaining for p in prizes),
            )
        )
    return games

def fetch_game_details(session: requests.Session, game: ScratchGame) -> None:
    resp = session.get(INFO_URL.format(game.game_id), timeout=(3, 10))
    resp.raise_for_status()
    data = resp.json()
    game.remain_total = data.get("RemainTotal", 0)
    game.prizes = [
        PrizeTier(
            amount=p["PrizeAmount"],
            total=p["PrizeCount"],
            remaining=p["RemainCount"],
        )
        for p in data.get("PrizeInfoList", [])
    ]


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Compute scratch card expected value")
    parser.add_argument("--json", dest="json_path", help="Path to local game data in JSON format")
    args = parser.parse_args(argv)

    if args.json_path:
        game_list = load_games_from_json(args.json_path)
    else:
        with create_session() as s:
            try:
                game_list = fetch_game_list(s)
            except Exception as e:
                print(f"Failed to fetch game list: {e}")
                return
            for game in game_list:
                try:
                    fetch_game_details(s, game)
                except Exception as e:
                    print(f"Failed to fetch {game.name}: {e}")

    game_list.sort(key=lambda g: g.expected_value(), reverse=True)
    for g in game_list:
        ev = g.expected_value()
        print(f"{g.game_id} {g.name}\tPrice: {g.price}\tEV: {ev:.2f}")

if __name__ == "__main__":
    main()
