from playwright.sync_api import sync_playwright
import json
import time
import sys

PRECIO_MIN = 2000
PRECIO_MAX = 21000

EXCLUIR = [
    "Tシャツ",
    "半袖",
    "カットソー",
    "oversea",
    "OVERSEA",
]

KEYWORDS = [
    "ミュウミュウ バッグ",
    "ミュウミュウ ショルダーバッグ",
    "ミュウミュウ トートバッグ",
    "ミュウミュウ クラッチ",
    "ミュウミュウ マテラッセ",
    "ミュウミュウ 財布",
    "ミュウミュウ 長財布",
    "ミュウミュウ 小銭入れ",
    "ミュウミュウ キーケース",
    "ミュウミュウ パーカー",
    "ミュウミュウ ニット",
    "ミュウミュウ パンツ",
    "ミュウミュウ スカート",
    "ミュウミュウ ハンドバッグ",
    "ミュウミュウ チェーンバッグ",
    "ミュウミュウ リュック",
    "ミュウミュウ ポーチ",
    "ミュウミュウ コインケース",
    "miu miu バッグ",
    "miu miu 財布",
    "ミュウミュウ アクセサリー",
    "ミュウミュウ サンダル",
    "ミュウミュウ ブーツ",
    "ミュウミュウ スニーカー",
]

def animacion_carga(pagina, segundos, mensaje="Cargando"):
    ciclos = int(segundos / 0.5)
    for i in range(ciclos):
        puntos = "." * ((i % 3) + 1)
        sys.stdout.write(f"\r  {mensaje}{puntos}   ")
        sys.stdout.flush()
        pagina.wait_for_timeout(500)
    sys.stdout.write("\r" + " " * 40 + "\r")

def debe_excluir(nombre):
    return any(palabra in nombre for palabra in EXCLUIR)

def scrape_keyword(pagina, keyword, vistos, resultados):
    url = (
        f"https://jp.mercari.com/search?keyword={keyword}"
        f"&price_min={PRECIO_MIN}&price_max={PRECIO_MAX}"
        f"&sort=created_time&order=desc&status=on_sale"
    )
    print(f"🔍 Buscando: {keyword}")
    try:
        pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
        pagina.wait_for_selector('li[data-testid="item-cell"]', timeout=30000)
    except Exception as e:
        print(f"  ⚠️ No cargó: {e}")
        return

    for _ in range(13):
        pagina.mouse.wheel(0, 3000)
        animacion_carga(pagina, 0.7, "Cargando productos")

    items = pagina.query_selector_all('li[data-testid="item-cell"]')
    nuevos = 0
    excluidos = 0
    for item in items:
        try:
            link_el = item.query_selector('a')
            url_producto = link_el.get_attribute('href') if link_el else None
            if url_producto and not url_producto.startswith('http'):
                url_producto = "https://jp.mercari.com" + url_producto
            if not url_producto or url_producto in vistos:
                continue

            nombre_el = item.query_selector('span[data-testid="thumbnail-item-name"]')
            nombre = nombre_el.inner_text() if nombre_el else "Sin nombre"

            if debe_excluir(nombre):
                excluidos += 1
                vistos.add(url_producto)
                continue

            vistos.add(url_producto)

            precio_el = item.query_selector('span.number__6b270ca7')
            precio_texto = precio_el.inner_text() if precio_el else "0"
            precio = precio_texto.replace(",", "").replace(".", "").strip()

            img_el = item.query_selector('img')
            imagen = img_el.get_attribute('src') if img_el else None

            resultados.append({
                "nombre": nombre,
                "precio_yen": precio,
                "url": url_producto,
                "imagen": imagen,
                "keyword_origen": keyword,
            })
            nuevos += 1
        except Exception:
            continue

    print(f"  ✅ Agregados: {nuevos}  ❌ Excluidos: {excluidos}  (Total: {len(resultados)})")

def buscar_mercari(keywords):
    resultados = []
    vistos = set()
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        pagina = navegador.new_page()
        for kw in keywords:
            scrape_keyword(pagina, kw, vistos, resultados)
            time.sleep(2)
        navegador.close()
    return resultados

if __name__ == "__main__":
    print("=" * 50)
    print("DIGGER LÉ SANG — Scraper Miu Miu")
    print(f"Rango de compra: ¥{PRECIO_MIN} – ¥{PRECIO_MAX}")
    print("=" * 50)

    data = buscar_mercari(KEYWORDS)

    with open("resultados.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print(f"✅ LISTO — {len(data)} productos únicos")
    print(f"📁 Guardados en: resultados.json")
    print("=" * 50)
