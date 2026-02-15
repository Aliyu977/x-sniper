import os, asyncio, requests, json, sqlite3, random
from datetime import datetime, timezone
from playwright.async_api import async_playwright

# Configuration
DB_FILE = "database.db"
QUERIES = [
    "(from:@KanikaBK OR from:@maxwellcopy OR from:@TaylinSimmonds OR from:@SwizzyOnChain OR from:@AlexHormozi OR from:@Laraacostar OR from:@growthghosts OR from:@beehiiv OR from:@ItsKieranDrew OR from:@dickiebush) min_faves:10",
    "(from:@businessbarista OR from:@alexgarcia_atx OR from:@cruzcontrol660 OR from:@KateBour OR from:@kylascan OR from:@GrammarHippy OR from:@MollyJZuckerman OR from:@JMatthewMcGarry OR from:@stephsmithio OR from:@Nicolascole77) min_faves:10",
    "(from:@N_Sportelli OR from:@SahilBloom OR from:@matt_gray_ OR from:@Codie_Sanchez OR from:@thedankoe OR from:@htsfhickey OR from:@ShaanVP OR from:@ItsKyleAdams OR from:@LanceRoberts OR from:@binghott) min_faves:10",
    "(from:@jappleby OR from:@markwschaefer OR from:@ashleyrcummings OR from:@mattragland OR from:@gregisenberg OR from:@jboitnott OR from:@JoePulizzi OR from:@MarketingProfs OR from:@garyvee OR from:@neilpatel) min_faves:10",

    '"newsletter" OR "email marketing" min_faves:15'
]

def notify(url, likes, velocity):
    webhook = os.getenv("DISCORD_WEBHOOK")
    payload = {"content": f"🔥 **High Velocity Tweet**\nURL: {url}\nLikes: {likes}\nVelocity: {velocity:.2f}/min"}
    requests.post(webhook, json=payload)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS tweets (id TEXT PRIMARY KEY, score REAL)')
    conn.commit()
    return conn

async def run_sniper():
    async with async_playwright() as p:
        # Optimization: Stealth Launch
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Load Session if exists
        if os.path.exists("state.json"):
            context = await browser.new_context(storage_state="state.json")
            
        page = await context.new_page()
        conn = init_db()

        for query in QUERIES:
            search_url = f"https://twitter.com/search?q={query}&f=live"
            await page.goto(search_url)
            await page.wait_for_timeout(random.randint(2000, 5000)) # Human delay
            
            tweets = await page.query_selector_all("article")
            print(f"Found {len(tweets)} tweets for query: {query}")
            for tweet in tweets:
                try:
                    # Extract Data
                    link = await (await tweet.query_selector("a[href*='/status/']")).get_attribute("href")
                    t_id = link.split("/")[-1]
                    
                    # Check DB for duplicates
                    if conn.execute("SELECT id FROM tweets WHERE id=?", (t_id,)).fetchone(): continue

                    like_text = await (await tweet.query_selector("div[data-testid='like']")).inner_text()
                    likes = int(like_text.replace(',', '')) if like_text.isdigit() else 0
                    
                    # Velocity Calculation
                    t_time = datetime.fromisoformat((await (await tweet.query_selector("time")).get_attribute("datetime")).replace("Z", "+00:00"))
                    mins = max((datetime.now(timezone.utc) - t_time).total_seconds() / 60, 1)
                    velocity = likes / mins

                    if velocity >= 1.5: # Threshold
                        notify(f"https://x.com{link}", likes, velocity)
                        conn.execute("INSERT INTO tweets VALUES (?, ?)", (t_id, velocity))
                        conn.commit()
                        print(f"Tweet {t_id} → Likes: {likes}, Velocity: {velocity}")
                except Exception as e:
    print("Error:", e)
    continue

        await context.storage_state(path="state.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_sniper())
