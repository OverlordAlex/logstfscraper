import sys
from bs4 import BeautifulSoup
import requests
import pickle
import os
import matplotlib.pyplot as plt
import numpy as np

class player:
    team = None
    class_played = None
    kills, assists, deaths = 0, 0, 0
    damage, damagepm = 0, 0
    damagetaken = 0
    airshots = 0
    caps = 0

    def __str__(self):
        return self.team + "-" + self.class_played + " : " + str(self.kills) + "+" + str(self.assists) + "/" + str(self.deaths)


def load(profile):
    # ensure that the profile points to a link
    if len(profile.split('/')) == 1:
        # assume that the number has been given
        profile = "logs.tf/profile/" + profile


    if os.path.isfile("saved." + profile.split('/')[-1]):
        if 'y' in raw_input("Old data detected, use this? y/n (n): ").lower():
            return pickle.load(open("saved." + profile.split('/')[-1], "rb"))


    profile_url = requests.get("http://" + profile)
    profile_page = BeautifulSoup(profile_url.text)

    # get all the links to the games
    num_games = int(profile_page.find_all("p")[0].string.split()[0])

    games = []

    # there are 25 games per page,
    # +1 because start from 1
    # +1 for the last page
    for i in range(1, (num_games / 25) + 2):
        # get the next list of games
        page = BeautifulSoup(requests.get("http://" + profile + "?p=" + str(i)).text)

        loglist = page.find("table")
        links = loglist.find_all('a')

        for link in links:
            games.append("http://logs.tf" + link.get('href'))

        # progress
        sys.stdout.write('.')
        sys.stdout.flush()


    games_played = []
    print "scraping done"

    for game in games:
        page = BeautifulSoup(requests.get(game).text)
        table =  page.find("tbody")
        for tr in table.find_all('tr'):
            if tr.get("class") == ['highlight']:
                info =  tr.find_all('td')
                play = player()

                if len(info) == 11:
                    # pass on games like MvM and surf
                    #print tr
                    #print game
                    #print "-"*25
                    continue

                play.team = info[0].text
                play.class_played = info[2].i["data-title"]
                play.kills, play.assists, play.deaths = float(info[3].text), float(info[4].text), int(info[5].text)
                play.damage, play.damagepm = float(info[6].text), float(info[7].text)
                play.damagetaken, play.damagetakenpm = float(info[10].text), float(info[11].text)
                #backstabs
                #headshots
                #who knows what
                #airshots = int(info[13].text)
                play.caps = float(info[-1].text)
                games_played.append(play)

        # progress
        sys.stdout.write('.')
        sys.stdout.flush()

    print "loading done"

    pickle.dump(games_played, open("saved." + profile.split('/')[-1], "wb"))
    return games_played


def main():
    profile = sys.argv[1] if len(sys.argv) == 2 else raw_input("Enter profile number or link: ")

    # load the profile
    games = load(profile)

    kills = np.array([game.kills for game in games if game.class_played != "Medic"])
    assists = np.array([game.assists for game in games if game.class_played != "Medic"])
    ka = kills + assists

    deaths = np.array([game.deaths for game in games if game.class_played != "Medic"])

    gamenum = range(len(deaths))

    team = [0 if game.team == "Blu" else 1 for game in games ]
    print "Red:", sum(team), "/", len(team)

    classes = {}
    for game in games:
        cl = game.team + game.class_played
        if cl in classes:
            classes[cl] += 1
        else:
            classes[cl] = 1


    dam = np.array([game.damage for game in games if game.class_played != "Medic"])
    damtaken = np.array([game.damagetaken for game in games if game.class_played != "Medic"])
    damv = [np.average(damtaken)*(dam[i]/damtaken[i]) for i in range(len(dam)) if damtaken[i] > 0]
    print damv

    fit = np.polyfit(range(len(damv)), damv, 1, full=True)
    slope = fit[0][0]
    intercept = fit[0][1]
    xl = [0, gamenum[-1]]
    yl = [slope*xx + intercept for xx in xl]
    plt.plot(xl, yl)

    plt.plot(gamenum, dam[::-1], label="damage done")
    plt.plot(gamenum, damtaken[::-1], label="damage taken")
    #plt.plot(gamenum, damv[::-1], label="dam/taken")
    plt.legend()
    plt.show()

    X = np.arange(len(classes))
    plt.bar(X, classes.values(), align="center", width=0.5)
    plt.xticks(X, classes.keys())
    #plt.show()


    plt.plot(gamenum, kills[::-1], label="kills")
    plt.plot(gamenum, ka[::-1], label="kills+assists")
    plt.plot(gamenum, deaths[::-1], label="deaths")
    plt.legend()
    #plt.show()

    kpd = kills[::-1]/deaths[::-1]
    kapd = ka[::-1]/deaths[::-1]

    fit = np.polyfit(gamenum, kapd, 1, full=True)
    slope = fit[0][0]
    intercept = fit[0][1]
    xl = [0, gamenum[-1]]
    yl = [slope*xx + intercept for xx in xl]
    plt.plot(xl, yl)

    plt.plot(gamenum, kpd, label="k/d")
    plt.plot(gamenum, kapd, label="ka/d")
    #plt.plot([0, gamenum[-1]], [kpd[0], kpd[-1]])
    plt.legend()
    #plt.show()


if __name__ == "__main__":
    main()

