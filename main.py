from load import main_load
from database import open_database, close_database
from profession import scrape_profession
from karriere import scrape_karriere
from ams import scrape_ams
from stepstone import scrape_stepstone
from multiprocessing import Process
import asyncio

def profession():

    cursor = open_database()

    scrape_profession(cursor)

    close_database(cursor)

def karriere():

    cursor = open_database()

    asyncio.run(scrape_karriere(cursor))

    close_database(cursor)

def ams():

    cursor = open_database()

    asyncio.run(scrape_ams(cursor))

    close_database(cursor)

def stepstone():

    cursor = open_database()

    asyncio.run(scrape_stepstone(cursor))

    close_database(cursor)

def main_parallel():
    p1 = Process(target=profession)
    p1.start()

    p2 = Process(target=karriere)
    p2.start()

    p3 = Process(target=ams)
    p3.start()

    p4 = Process(target=stepstone)
    p4.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()

    cursor = open_database()

    main_load(cursor)

    close_database(cursor)

def main_linear():
    profession()
    karriere()
    ams()
    stepstone()
    #main_load()

if __name__ == "__main__":
    
    #main_linear(cursor)
    main_parallel()
    #profession(cursor)
    #main_load(cursor)