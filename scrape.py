import json
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Iterable, Optional
import argparse

BASE_URL = "https://www.taiwanlottery.com.tw"
LIST_URL = f"{BASE_URL}/zh-hant/instant/instant_index.aspx"

@dataclass
class PrizeTier:
    amount: int
    total: int
    remaining: int

@dataclass
class ScratchGame:
    name: str
    price: int
    url: str
    prizes: List[PrizeTier] = field(default_factory=list)

    def expected_value(self) -> float:
        total_remaining = sum(t.remaining for t in self.prizes)
        if total_remaining == 0:
            return -self.price
        # total value after taxes
        total_value = sum(_net_amount(t.amount) * t.remaining for t in self.prizes)
        return total_value / total_remaining - self.price

def _net_amount(amount: int) -> float:
    if amount > 5000:
        after_tax = amount * 0.8  # 20% winning tax
        after_tax *= 0.996        # 0.4% stamp tax
        return after_tax
    return float(amount)

def fetch_game_list(session: requests.Session) -> List[ScratchGame]:
    resp = session.get(LIST_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    games = []
    # The structure may change; this is a best guess using common table layout
    for a in soup.select("a[href*='instant_']"):
        name = a.get_text(strip=True)
        href = a.get("href")
        if not href:
            continue
        if not href.startswith("http"):
            href = BASE_URL + href
        # Extract price from sibling element if available
        price_text = a.find_next("span")
        price = 0
        if price_text:
            digits = ''.join(filter(str.isdigit, price_text.get_text()))
            price = int(digits) if digits else 0
        games.append(ScratchGame(name=name, price=price, url=href))
    return games


def load_games_from_json(path: str) -> List[ScratchGame]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    games: List[ScratchGame] = []
    for g in data:
        prizes = [PrizeTier(**p) for p in g.get("prizes", [])]
        games.append(
            ScratchGame(name=g.get("name", ""), price=g.get("price", 0), url="", prizes=prizes)
        )
    return games

def fetch_game_details(session: requests.Session, game: ScratchGame) -> None:
    resp = session.get(game.url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if not table:
        return
    for tr in table.select("tr"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        if len(cells) < 3:
            continue
        try:
            amount = int(cells[0].replace(',', ''))
            total = int(cells[1].replace(',', ''))
            remaining = int(cells[2].replace(',', ''))
        except ValueError:
            continue
        game.prizes.append(PrizeTier(amount, total, remaining))


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Compute scratch card expected value")
    parser.add_argument("--json", dest="json_path", help="Path to local game data in JSON format")
    args = parser.parse_args(argv)

    if args.json_path:
        game_list = load_games_from_json(args.json_path)
    else:
        with requests.Session() as s:
            s.headers.update({"User-Agent": "Mozilla/5.0"})
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
        print(f"{g.name}\tPrice: {g.price}\tEV: {ev:.2f}")

if __name__ == "__main__":
    main()
