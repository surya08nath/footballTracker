from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
import re
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.configure(timezone='Asia/Kolkata')


# FastAPI app initialization
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
DATABASE_URL = "sqlite:///./matches.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Match Model
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_link = Column(String, unique=True, index=True)
    team1 = Column(String)
    team2 = Column(String)
    date = Column(String)

# Create Database Tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to scrape and store match data
def get_matches(db: Session,request_date):
    print("Function called")
    print(request_date)
    url = "https://sportstrack.sportstag.in/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    today_date = datetime.today().strftime("%Y-%m-%d")
    yesterday_date = (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    matches = []

    articles = soup.find_all("article", class_="blog-post")

    for article in articles:
        time_tag = article.find("time", class_="published")
        if time_tag and time_tag.has_attr("datetime"):
            post_date = time_tag["datetime"].split("T")[0]  

            if post_date == request_date:
                entry_link = article.find("a", class_="entry-title-link")
                if entry_link and entry_link.has_attr("href"):
                    match_link = entry_link["href"]
                    match_title = entry_link.text.strip()

                    teams = re.split(r"\s+Vs\.?\s+|\s+vs\.?\s+|\s+VS\.?\s+", match_title, maxsplit=1)
                    if len(teams) == 2:
                        team1 = teams[0].strip()
                        team2 = teams[1].split(",")[0].strip()

                        # Check if match already exists in the database
                        existing_match = db.query(Match).filter_by(match_link=match_link).first()
                        if not existing_match:
                            new_match = Match(match_link=match_link, team1=team1, team2=team2, date=post_date)
                            db.add(new_match)

                        matches.append({
                            "match_link": match_link,
                            "team1": team1,
                            "team2": team2,
                            "date" : post_date,
                        })

    db.commit()
    return matches

def delete():
    print("Deleteing all records")
    db = SessionLocal()
    db.query(Match).delete()
    db.commit()
    db.close()
scheduler.add_job(delete, trigger='cron', hour='*')

# API Route to Fetch and Store Matches
@app.get("/matches")
def get_matches_api(db: Session = Depends(get_db),date: str=datetime.today().strftime("%Y-%m-%d")):
    print(date)
    matches = db.query(Match).filter(Match.date == f"{date}").all()
    if(matches==[]):
        matches=get_matches(db,date) 
    print(matches)
    return {"matches": matches}

@app.get("/getall")
def get_matches_api(db: Session = Depends(get_db),date: str=datetime.today().strftime("%Y-%m-%d")):
    print(date)
    matches = db.query(Match).all()
    print(matches)
    #return matches
    return {"matches": matches}

@app.get("/delete")
def get_matches_api():
    delete()
    


if __name__ == "__main__":
    import uvicorn
    scheduler.start()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

