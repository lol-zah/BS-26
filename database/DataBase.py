from Logic.Player import Players
import json
import datetime
import sqlite3 as sql
import threading

PLAYER_DB = "database/Player/plr.db"
CLUB_DB = "database/Club/clubs.db"
CHAT_DB = "database/Club/chats.db"

_wal_mode_dbs = set()
_wal_lock = threading.Lock()
_db_lock = threading.RLock()


def db_locked(func):
    def wrapper(*args, **kwargs):
        with _db_lock:
            return func(*args, **kwargs)
    return wrapper


def _ensure_schema(conn, path):
    if path == PLAYER_DB:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS plrs ("
            "token TEXT, lowID INT, name TEXT, trophies INT, gold INT, gems INT, "
            "starpoints INT, tickets INT, Troproad INT, profile_icon INT, name_color INT,"
            "clubID INT, clubRole INT, brawlerData JSON, brawlerID INT, skinID INT, roomID INT, "
            "box INT, bigbox INT, online INT, vip INT, playerExp INT, friends JSON, SCC TEXT,"
            "trioWINS INT, sdWINS INT, theme INT)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plrs_token ON plrs(token)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plrs_lowid ON plrs(lowID)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plrs_trophies ON plrs(trophies)")
        conn.commit()
    elif path == CLUB_DB:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS clubs ("
            "clubID INT, name TEXT, desc TEXT, region TEXT, badgeID INT, type INT, "
            "trophiesneeded INT, friendlyfamily INT, trophies INT, members JSON, notif JSON)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_clubs_clubid ON clubs(clubID)")
        conn.commit()
    elif path == CHAT_DB:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chats ("
            "clubID INT, Event INT, Tick INT, plrid INT, plrname TEXT, plrrole INT, Msg TEXT)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chats_clubid ON chats(clubID)")
        conn.commit()


def _connect(path):
    conn = sql.connect(path, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout=5000")
    with _wal_lock:
        if path not in _wal_mode_dbs:
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                _wal_mode_dbs.add(path)
            except sql.OperationalError:
                pass
    _ensure_schema(conn, path)
    conn.row_factory = sql.Row
    return conn


def _safe_column(name):
    if not name or not name.replace("_", "").isalnum():
        raise ValueError(f"unsafe column name: {name!r}")
    return name


class DataBase:
    @db_locked
    def loadAccount(self):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        user_data = None
        try:
            cur.execute("SELECT * FROM plrs WHERE token=?", (self.player.token,))
            user_data = cur.fetchone()
        except sql.OperationalError:
            user_data = None

        if user_data is not None:
            self.player.low_id = user_data[1]
            self.player.name = user_data[2]
            self.player.trophies = user_data[3]
            self.player.gold = user_data[4]
            self.player.gems = user_data[5]
            self.player.starpoints = user_data[6]
            self.player.tickets = user_data[7]
            self.player.Troproad = user_data[8]
            self.player.profile_icon = user_data[9]
            self.player.name_color = user_data[10]
            self.player.club_low_id = user_data[11]
            self.player.club_role = user_data[12]
            self.player.brawler_id = user_data[14]
            self.player.skin_id = user_data[15]
            self.player.room_id = user_data[16]
            self.player.box = user_data[17]
            self.player.bigbox = user_data[18]
            self.player.online = user_data[19]
            self.player.vip = user_data[20]
            self.player.player_experience = user_data[21]
            self.player.ccc = user_data[23]
            self.player.trioWINS = user_data[24]
            self.player.sdWINS = user_data[25]
            self.player.theme = user_data[26]
            self.player.friends = json.loads(user_data[22])
            brawler_data = json.loads(user_data[13])
            self.player.highest_trophies = brawler_data["highest_trophies"]
            self.player.brawlers_trophies = brawler_data["brawlersTrophies"]
            self.player.UnlockedBrawlers = brawler_data["UnlockedBrawlers"]
            self.player.UnlockedSkins = brawler_data["UnlockedSkins"]
            self.player.brawlerPowerLevel = brawler_data["brawlerPowerLevel"]
            self.player.brawlerPoints = brawler_data["brawlerPoints"]

            player_total_trophies = sum(self.player.brawlers_trophies.values())
            self.player.trophies = player_total_trophies
            DataBase.replaceValue(self, "trophies", self.player.trophies)
            DataBase.replaceValue(self, "highest_trophies", player_total_trophies)

        conn.close()

    @db_locked
    def createAccount(self):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS plrs ("
            "token TEXT, lowID INT, name TEXT, trophies INT, gold INT, gems INT, "
            "starpoints INT, tickets INT, Troproad INT, profile_icon INT, name_color INT,"
            "clubID INT, clubRole INT, brawlerData JSON, brawlerID INT, skinID INT, roomID INT, "
            "box INT, bigbox INT, online INT, vip INT, playerExp INT, friends JSON, SCC TEXT,"
            "trioWINS INT, sdWINS INT, theme INT)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_plrs_token ON plrs(token)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_plrs_lowid ON plrs(lowID)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_plrs_trophies ON plrs(trophies)")
        conn.commit()

        brawler_data = {
            "highest_trophies": self.player.highest_trophies,
            "brawlersTrophies": self.player.brawlers_trophies,
            "UnlockedBrawlers": self.player.UnlockedBrawlers,
            "UnlockedSkins": self.player.UnlockedSkins,
            "brawlerPowerLevel": self.player.brawlerPowerLevel,
            "brawlerPoints": self.player.brawlerPoints,
        }
        var = (
            self.player.token, self.player.low_id, self.player.name, self.player.trophies,
            self.player.gold, self.player.gems, self.player.starpoints, self.player.tickets,
            self.player.Troproad, self.player.profile_icon, self.player.name_color,
            self.player.club_low_id, self.player.club_role,
            json.dumps(brawler_data), self.player.brawler_id, self.player.skin_id,
            self.player.room_id, self.player.box, self.player.bigbox, self.player.online,
            self.player.vip, self.player.player_experience, json.dumps([]), self.player.ccc,
            self.player.trioWINS, self.player.sdWINS, self.player.theme,
        )
        cur.execute(
            "INSERT INTO plrs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            var,
        )
        conn.commit()
        conn.close()

    @db_locked
    @db_locked
    def getLeaders(self):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute(
            "SELECT lowID,name,trophies,profile_icon,name_color FROM plrs "
            "ORDER BY trophies DESC LIMIT 150"
        )
        result = cur.fetchall()
        conn.close()
        return result

    @db_locked
    @db_locked
    def getAll(self):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM plrs")
        result = cur.fetchall()
        conn.close()
        return result

    @db_locked
    def GetLeaderboardByBrawler(self, ID):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute(
            "SELECT lowID,name,brawlerData,profile_icon,name_color FROM plrs LIMIT 200"
        )
        result = cur.fetchall()
        conn.close()
        return result

    @db_locked
    def setImmediateValue(self, db, table, var, val, sqlsin=""):
        conn = _connect(f"database/{db}.db")
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {_safe_column(table)} SET {_safe_column(var)}=? {sqlsin}", (val,)
        )
        conn.commit()
        conn.close()

    @db_locked
    def getSpecifiedValue(self, value_name):
        return None

    @db_locked
    def loadbyID(self, ID):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute("SELECT * FROM plrs WHERE lowID=?", (ID,))
        result = cur.fetchone()
        conn.close()
        return result

    @db_locked
    def set2All(self, var, val):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute(f"UPDATE plrs SET {_safe_column(var)}=?", (val,))
        conn.commit()
        conn.close()

    @db_locked
    def callbackSQLQ(self, sqlcallback):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute(sqlcallback)
        conn.commit()
        conn.close()

    @db_locked
    def replaceValue(self, value_name, new_value):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        if value_name == "3vs3Wins":
            value_name = "TvsTWins"
        if value_name == "tranim":
            conn.close()
            return
        if value_name in [
            "UnlockedSkins", "UnlockedPins", "StarPowerUnlocked", "brawlersTrophies",
            "brawlersTrophiesForRank", "brawlersSkins", "brawlerPoints", "UnlockedBrawlers",
            "brawlerPowerLevel", "chwins", "highest_trophies",
        ]:
            cur.execute("SELECT brawlerData FROM plrs WHERE token=?", (self.player.token,))
            row = cur.fetchone()
            if row is None:
                conn.close()
                return
            data = json.loads(row[0])
            data[value_name] = new_value
            cur.execute(
                "UPDATE plrs SET brawlerData=? WHERE token=?",
                (json.dumps(data), self.player.token),
            )
        elif value_name == "Skins":
            try:
                cur.execute(
                    "SELECT skinsData FROM plrs WHERE token=?", (self.player.token,)
                )
                row = cur.fetchone()
                if row is None:
                    conn.close()
                    return
                data = json.loads(row[0])
                data[value_name] = new_value
                cur.execute(
                    "UPDATE plrs SET skinsData=? WHERE token=?",
                    (json.dumps(data), self.player.token),
                )
            except sql.OperationalError:
                pass
        else:
            cur.execute(
                f"UPDATE plrs SET {_safe_column(value_name)}=? WHERE token=?",
                (new_value, self.player.token),
            )
        conn.commit()
        conn.close()

    @db_locked
    def loadByToken(self, token):
        return None

    @db_locked
    def replaceOtherValue(self, ID, value_name, new_value):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        if value_name in [
            "UnlockedSkins", "UnlockedPins", "brawlersTrophies",
            "brawlersTrophiesForRank", "brawlersSkins",
        ]:
            cur.execute("SELECT brawlerData FROM plrs WHERE lowID=?", (ID,))
            row = cur.fetchone()
            if row is None:
                conn.close()
                return
            data = json.loads(row[0])
            data[value_name] = new_value
            cur.execute(
                "UPDATE plrs SET brawlerData=? WHERE lowID=?",
                (json.dumps(data), ID),
            )
        elif value_name == "Skins":
            try:
                cur.execute(
                    "SELECT skinsData FROM plrs WHERE lowID=?", (ID,)
                )
                row = cur.fetchone()
                if row is None:
                    conn.close()
                    return
                data = json.loads(row[0])
                data[value_name] = new_value
                cur.execute(
                    "UPDATE plrs SET skinsData=? WHERE lowID=?",
                    (json.dumps(data), ID),
                )
            except sql.OperationalError:
                pass
        else:
            cur.execute(
                f"UPDATE plrs SET {_safe_column(value_name)}=? WHERE lowID=?",
                (new_value, ID),
            )
        conn.commit()
        conn.close()

    @db_locked
    def UpdateValue(self, var, new):
        conn = _connect(PLAYER_DB)
        cur = conn.cursor()
        cur.execute(f"SELECT {_safe_column(var)} FROM plrs WHERE token=?", (self.player.token,))
        row = cur.fetchone()
        if row is not None:
            cur.execute(
                f"UPDATE plrs SET {_safe_column(var)}=? WHERE token=?",
                (row[0] + new, self.player.token),
            )
        conn.commit()
        conn.close()

    @db_locked
    def createClub(self, clubid):
        conn = _connect(CLUB_DB)
        con = _connect(CHAT_DB)
        cur = conn.cursor()
        c = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS clubs ("
            "clubID INT, name TEXT, desc TEXT, region TEXT, badgeID INT, type INT, "
            "trophiesneeded INT, friendlyfamily INT, trophies INT, members JSON, notif JSON)"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clubs_clubid ON clubs(clubID)")
        c.execute(
            "CREATE TABLE IF NOT EXISTS chats ("
            "clubID INT, Event INT, Tick INT, plrid INT, plrname TEXT, plrrole INT, Msg TEXT)"
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_chats_clubid ON chats(clubID)")
        conn.commit()
        con.commit()

        data = {"members": {self.player.low_id: self.player.name}}
        notif = {}
        var = (
            clubid, str(self.clubName), str(self.clubdescription), "RU", self.clubbadgeID,
            self.clubtype, self.clubtrophiesneeded, self.clubfriendlyfamily,
            self.player.trophies, json.dumps(data), json.dumps(notif),
        )
        cur.execute("INSERT INTO clubs VALUES (?,?,?,?,?,?,?,?,?,?,?)", var)
        conn.commit()

        sss = "INSERT INTO chats VALUES (?, ?, ?,?,?,?,?)"
        var = (clubid, 2, 1, self.player.low_id, str(self.player.name), 2, "Привет")
        c.execute(sss, var)
        con.commit()
        conn.close()
        con.close()

    @db_locked
    def setNotifData(self, text, by):
        conn = _connect(CLUB_DB)
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM clubs WHERE clubID=?", (self.player.club_low_id,)
            )
            row = cur.fetchone()
            if row is not None:
                notif_data = json.loads(row[10])
                l = str(len(notif_data))
                notif_data[l] = {}
                notif_data[l]["text"] = text
                notif_data[l]["by"] = by
                notif_data[l]["timer"] = datetime.datetime.timestamp(
                    datetime.datetime.now()
                )
                cur.execute(
                    "UPDATE clubs SET notif=? WHERE clubID=?",
                    (json.dumps(notif_data), self.player.club_low_id),
                )
                conn.commit()
        finally:
            conn.close()

    @db_locked
    def CountClub(self):
        self.AllianceCount = 0
        self.club_list = []
        conn = _connect(CLUB_DB)
        con = _connect(CHAT_DB)
        cur = conn.cursor()
        c = con.cursor()
        try:
            cur.execute("SELECT * FROM clubs")
            fetch = cur.fetchall()
            if len(fetch) > 0:
                for i in fetch:
                    self.club_list.append(int(i[0]))
                    self.AllianceCount += 1
        finally:
            conn.close()
            con.close()

    @db_locked
    def LeaderClub(self):
        self.AllianceCount = 0
        self.club_list = []
        conn = _connect(CLUB_DB)
        con = _connect(CHAT_DB)
        cur = conn.cursor()
        c = con.cursor()
        try:
            cur.execute("SELECT * FROM clubs ORDER BY trophies DESC LIMIT 200")
            fetch = cur.fetchall()
            if len(fetch) > 0:
                for i in fetch:
                    self.club_list.append(int(i[0]))
                    self.AllianceCount += 1
        finally:
            conn.close()
            con.close()

    @db_locked
    def loadClub(self, clubid):
        conn = _connect(CLUB_DB)
        con = _connect(CHAT_DB)
        cur = conn.cursor()
        c = con.cursor()
        cur.execute("SELECT * FROM clubs WHERE clubID=?", (clubid,))
        fetch = cur.fetchall()
        if len(fetch) > 0:
            for i in fetch:
                self.clubmembercount = 0
                self.plrids = []
                self.clubName = i[1]
                self.clubdescription = i[2]
                self.clubregion = i[3]
                self.clubbadgeID = i[4]
                self.clubtype = i[5]
                self.clubtrophiesneeded = i[6]
                self.clubfriendlyfamily = i[7]
                try:
                    self.notifData = json.loads(i[10])
                except Exception:
                    self.notifData = {}
                self.clubtrophies = 0
                data = json.loads(i[9])
                for ID in data["members"]:
                    if ID != "members":
                        self.plrids.append(int(ID))
                        self.clubmembercount += 1
                        DataBase.GetMemberData(self, int(ID))
                        self.clubtrophies += self.plrtrophies
        conn.close()
        con.close()

    @db_locked
    def AddMember(self, AllianceID, PlayerID, PlayerName, Action):
        conn = _connect(CLUB_DB)
        con = _connect(CHAT_DB)
        cur = conn.cursor()
        chat = con.cursor()
        cur.execute("SELECT * FROM clubs WHERE clubID=?", (AllianceID,))
        fetch = cur.fetchall()
        if len(fetch) > 0:
            data = json.loads(fetch[0][9])
            if Action == 0:
                chat.execute("DELETE FROM chats WHERE clubID=?", (AllianceID,))
                cur.execute("DELETE FROM clubs WHERE clubID=?", (AllianceID,))
                conn.commit()
                con.commit()
            elif Action == 1:
                data["members"][str(PlayerID)] = PlayerName
                cur.execute(
                    "UPDATE clubs SET members=? WHERE clubID=?",
                    (json.dumps(data), AllianceID),
                )
                ol = fetch[0][8]
                cur.execute(
                    "UPDATE clubs SET trophies=? WHERE clubID=?",
                    (ol + self.player.trophies, AllianceID),
                )
                conn.commit()
            elif Action == 2:
                data["members"].pop(str(PlayerID), None)
                cur.execute(
                    "UPDATE clubs SET members=? WHERE clubID=?",
                    (json.dumps(data), AllianceID),
                )
                ol = fetch[0][8]
                cur.execute(
                    "UPDATE clubs SET trophies=? WHERE clubID=?",
                    (ol - self.player.trophies, AllianceID),
                )
                conn.commit()
        conn.close()
        con.close()

    @db_locked
    def GetMemberData(self, Low_id):
        try:
            self.players = DataBase.loadbyID(self, Low_id)
            if self.players is not None and self.players[1] == int(Low_id):
                self.lowplrid = self.players[1]
                self.plrrole = self.players[12]
                self.plrtrophies = self.players[3]
                self.plrname = self.players[2]
                self.plricon = self.players[9]
                self.plrnamecolor = self.players[10]
                self.plrexperience = self.players[21]
                self.plrstatus = self.players[19]
                self.plrvip = self.players[20]
            else:
                raise ValueError("member not found")
        except Exception:
            self.lowplrid = 1
            self.plrrole = 0
            self.plrtrophies = 0
            self.plrname = "Falied to load account!"
            self.plricon = 5
            self.plrnamecolor = 1
            self.plrexperience = 999
            self.plrvip = 0
            self.plrstatus = 0

    @db_locked
    def replaceClubValue(self, target, inf1, inf2, inf3, inf4, inf5):
        conn = _connect(CLUB_DB)
        con = _connect(CHAT_DB)
        cur = conn.cursor()
        chat = con.cursor()
        cur.execute(
            "SELECT * FROM clubs WHERE clubID=?",
            (self.player.club_low_id,),
        )
        fetch = cur.fetchall()
        cur.execute(
            "UPDATE clubs SET desc=? WHERE clubID=?",
            (inf1, self.player.club_low_id),
        )
        cur.execute(
            "UPDATE clubs SET badgeID=? WHERE clubID=?",
            (inf2, self.player.club_low_id),
        )
        cur.execute(
            "UPDATE clubs SET type=? WHERE clubID=?",
            (inf3, self.player.club_low_id),
        )
        cur.execute(
            "UPDATE clubs SET trophiesneeded=? WHERE clubID=?",
            (inf4, self.player.club_low_id),
        )
        cur.execute(
            "UPDATE clubs SET friendlyfamily=? WHERE clubID=?",
            (inf5, self.player.club_low_id),
        )
        conn.commit()
        conn.close()
        con.close()

    @db_locked
    def GetmsgCount(self, clubID):
        con = _connect(CHAT_DB)
        chat = con.cursor()
        chat.execute("SELECT * FROM chats WHERE clubID=?", (clubID,))
        fetch = chat.fetchall()
        if len(fetch) > 0:
            self.MessageCount = len(fetch)
        else:
            self.MessageCount = 1
        con.close()

    @db_locked
    def Addmsg(self, clubID, event, tick, Low_id, name, role, msg):
        con = _connect(CHAT_DB)
        chat = con.cursor()
        chat.execute(
            "SELECT COALESCE(MAX(Tick), 0) + 1 AS ntick FROM chats WHERE clubID=?",
            (clubID,),
        )
        row = chat.fetchone()
        ntick = row[0] if row else 1
        sss = "INSERT INTO chats VALUES (?, ?, ?,?,?,?,?)"
        var = (clubID, event, ntick, Low_id, name, role, msg)
        chat.execute(sss, var)
        con.commit()
        con.close()

    @db_locked
    def DeleteAllMsg(self, clubID):
        con = _connect(CHAT_DB)
        chat = con.cursor()
        chat.execute(
            "SELECT * FROM chats WHERE clubID=?", (clubID,)
        )
        fetch = chat.fetchall()
        if len(fetch) >= 50:
            chat.execute("DELETE FROM chats WHERE clubID=?", (clubID,))
            con.commit()
        con.close()
