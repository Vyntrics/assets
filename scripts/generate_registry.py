import requests
import json
import time
import os
import sys

OUTPUT_DIR = 'data'
OUTPUT_FILE = 'token_registry.json'
ICONS_BASE_URL = 'https://raw.githubusercontent.com/Vyntrics/assets/main/icons/'
MIN_TOKEN_THRESHOLD = 1000 

BLACKLIST = {
    '0x0000000000000000000000000000000000000000',
    '0xbadcontractaddress',
}

CHAIN_MAP = {
    'ethereum': 'ethereum',
    'solana': 'solana',
    'binance-smart-chain': 'binance-smart-chain',
    'polygon-pos': 'polygon-pos',
    'avalanche': 'avalanche',
    'arbitrum-one': 'arbitrum-one',
    'base': 'base',
    'optimistic-ethereum': 'optimistic-ethereum',
    'zksync': 'zksync',
    'tron': 'tron',
    'stellar': 'stellar',
    'world-chain': 'world-chain',
}

GAS_TOKENS = {
    'bitcoin':              {'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin', 'decimals': 8, 'icon': 'btc.png'},
    'ethereum':             {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'icon': 'eth.png'},
    'solana':               {'id': 'solana', 'symbol': 'SOL', 'name': 'Solana', 'decimals': 9, 'icon': 'sol.png'},
    'binance-smart-chain':  {'id': 'binancecoin', 'symbol': 'BNB', 'name': 'BNB', 'decimals': 18, 'icon': 'bnb.png'},
    'polygon-pos':          {'id': 'polygon-ecosystem-token', 'symbol': 'POL', 'name': 'Polygon', 'decimals': 18, 'icon': 'pol.png'},
    'avalanche':            {'id': 'avalanche-2', 'symbol': 'AVAX', 'name': 'Avalanche', 'decimals': 18, 'icon': 'avax.png'},
    'tron':                 {'id': 'tron', 'symbol': 'TRX', 'name': 'TRON', 'decimals': 6, 'icon': 'trx.png'},
    'stellar':              {'id': 'stellar', 'symbol': 'XLM', 'name': 'Stellar', 'decimals': 7, 'icon': 'xlm.png'},
    'arbitrum-one':         {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'icon': 'eth.png'},
    'base':                 {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'icon': 'eth.png'},
    'optimistic-ethereum':  {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'icon': 'eth.png'},
    'zksync':               {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'icon': 'eth.png'},
    'world-chain':          {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18, 'icon': 'eth.png'},
}

API_KEY = os.getenv('COINGECKO_API_KEY')

def fetch_json(url, retries=3):
    headers = {"accept": "application/json"}
    if API_KEY:
        headers["x-cg-demo-api-key"] = API_KEY
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                if not data: return None 
                return data
            except json.JSONDecodeError:
                if retries > 0:
                    time.sleep(5)
                    return fetch_json(url, retries - 1)
                return None

        if resp.status_code == 429:
            if retries > 0:
                time.sleep(65)
                return fetch_json(url, retries - 1)
            return None

        if resp.status_code >= 500 and retries > 0:
            time.sleep(5)
            return fetch_json(url, retries - 1)
            
        return None
    except Exception:
        if retries > 0:
            time.sleep(5)
            return fetch_json(url, retries - 1)
        return None

def main():
    final_token_list = []
    
    id_map = fetch_json("https://api.coingecko.com/api/v3/coins/list?include_platform=true")
    if not id_map or not isinstance(id_map, list):
        sys.exit(1)

    address_lookup = {}
    for coin in id_map:
        if not isinstance(coin, dict): continue
        platforms = coin.get('platforms', {})
        for plat, addr in platforms.items():
            if addr:
                key = f"{plat}:{addr.lower()}"
                address_lookup[key] = coin.get('id')

    for chain_key, platform_id in CHAIN_MAP.items():
        if chain_key in GAS_TOKENS:
            gt = GAS_TOKENS[chain_key]
            final_token_list.append({
                "id": gt['id'],
                "symbol": gt['symbol'],
                "name": gt['name'],
                "address": "native",
                "platform_id": platform_id,
                "image_url": f"{ICONS_BASE_URL}{gt['icon']}",
                "decimals": gt['decimals']
            })

        data = fetch_json(f"https://api.coingecko.com/api/v3/token_lists/{platform_id}/all.json")
        if not data or not isinstance(data, dict) or 'tokens' not in data:
            continue

        for t in data['tokens']:
            address = t.get('address', '').lower()
            if not address or address in BLACKLIST: 
                continue

            lookup_key = f"{platform_id}:{address}"
            canonical_id = address_lookup.get(lookup_key) or t.get('id')
            
            symbol = t.get('symbol')
            name = t.get('name')
            
            if not canonical_id or not symbol or not name:
                continue

            try:
                decimals = int(t.get('decimals', 18))
            except (ValueError, TypeError):
                decimals = 18

            img = t.get('logoURI', '')
            if img:
                img = img.replace('/thumb/', '/small/').replace('/large/', '/small/')

            final_token_list.append({
                "id": canonical_id,
                "symbol": symbol,
                "name": name,
                "address": address,
                "platform_id": platform_id,
                "image_url": img,
                "decimals": decimals
            })
        
        time.sleep(0.2 if API_KEY else 1.5)

    if 'bitcoin' in GAS_TOKENS:
        btc = GAS_TOKENS['bitcoin']
        final_token_list.insert(0, {
            "id": btc['id'],
            "symbol": btc['symbol'],
            "name": btc['name'],
            "address": "native",
            "platform_id": "bitcoin",
            "image_url": f"{ICONS_BASE_URL}{btc['icon']}",
            "decimals": btc['decimals']
        })

    if len(final_token_list) < MIN_TOKEN_THRESHOLD:
        sys.exit(1)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    full_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(final_token_list, f, separators=(',', ':'))

if __name__ == "__main__":
    main()