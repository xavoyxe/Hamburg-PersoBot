import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

class Person:
    def __init__(
        self,
        vollstaendiger_name: str,
        geburtsdatum: str,
        geburtsort_nationalitaet: str,
        groesse: str,
        geschlecht: str,
        status: str,
        nick: Optional[str] = None,
        uuid_str: Optional[str] = None,
        time: Optional[str] = None,
    ):
        self.uuid = uuid_str or str(uuid.uuid4())
        self.nick = nick or self.uuid
        self.vollstaendiger_name = vollstaendiger_name
        self.geburtsdatum = geburtsdatum
        self.geburtsort_nationalitaet = geburtsort_nationalitaet
        self.groesse = groesse
        self.geschlecht = geschlecht
        self.status = status
        self.time = time or str(datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M"))

    def to_dict(self) -> Dict:
        return {
            "uuid": self.uuid,
            "nick": self.nick,
            "vollstaendiger_name": self.vollstaendiger_name,
            "geburtsdatum": self.geburtsdatum,
            "geburtsort_nationalitaet": self.geburtsort_nationalitaet,
            "groesse": self.groesse,
            "geschlecht": self.geschlecht,
            "status": self.status,
            "time": self.time,
        }

    @staticmethod
    def from_dict(data: Dict):
        return Person(
            vollstaendiger_name=data["vollstaendiger_name"],
            geburtsdatum=data["geburtsdatum"],
            geburtsort_nationalitaet=data["geburtsort_nationalitaet"],
            groesse=data["groesse"],
            geschlecht=data["geschlecht"],
            status=data["status"],
            nick=data.get("nick"),
            uuid_str=data.get("uuid"),
            time=data.get("time"),
        )


class PersonenDB:
    def __init__(self, base_path: Path):
        self.path = base_path / "personen.json"
        self.data: Dict[str, List[Dict]] = {}
        if self.path.exists():
            self.load()
        else:
            self.data = {}
            self.save()

    def load(self) -> bool:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"[ERROR] load(): {e}")
            return False

    def save(self) -> bool:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] save(): {e}")
            return False

    def add_perso(self, discord_id: str, person: Person) -> any:
        try:
            if discord_id not in self.data:
                self.data[discord_id] = []
            self.data[discord_id].append(person.to_dict())
            uuid=str(person.uuid)
            self.save()
            return uuid
        except Exception as e:
            print(f"[ERROR] add_perso(): {e}")
            return False

    def delete_perso(self, discord_id: str, uuid_str: str) -> bool:
        try:
            if discord_id in self.data:
                self.data[discord_id] = [
                    p for p in self.data[discord_id] if p["uuid"] != uuid_str
                ]
                return self.save()
            return False
        except Exception as e:
            print(f"[ERROR] delete_perso(): {e}")
            return False

    def update_perso(self, discord_id: str, uuid_str: str, new_data: Dict) -> bool:
        try:
            if discord_id not in self.data:
                return False
            for i, p in enumerate(self.data[discord_id]):
                if p["uuid"] == uuid_str:
                    self.data[discord_id][i].update(new_data)
                    return self.save()
            return False
        except Exception as e:
            print(f"[ERROR] update_perso(): {e}")
            return False

    def get_perso_by_uuid(self, uuid_str: str) -> Optional[Dict]:
        try:
            for persons in self.data.values():
                for p in persons:
                    if p["uuid"] == uuid_str:
                        return p
            return None
        except Exception as e:
            print(f"[ERROR] get_perso_by_uuid(): {e}")
            return None

    def get_persos_by_discordid(self, discord_id: str) -> List[Dict]:
        return self.data.get(discord_id, [])

    def count_persos(self, discord_id: str) -> int:
        return len(self.data.get(discord_id, []))
