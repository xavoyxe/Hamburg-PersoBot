import asyncio
import hashlib
import orjson
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class DBClientError(Exception):
    def __init__(self, message: str, *, code: int = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self):
        parts = [f"[DBClientError] {self.message}"]
        if self.code is not None:
            parts.append(f"(Code {self.code})")
        if self.details:
            parts.append(f"| Details: {self.details}")
        return " ".join(parts)

class AsyncDBClient:
    def __init__(self, host: str, port: int, handshake_key: str):
        self.host = host
        self.port = port
        self.handshake_key = handshake_key
        self.nonce = b"000000000000"
        self.aesgcm = AESGCM(hashlib.sha256(handshake_key.encode()).digest())

    async def send_command(self, command: dict) -> dict:
        writer = None
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)

            auth_payload = orjson.dumps({"auth": self.handshake_key})
            encrypted_auth = self.aesgcm.encrypt(self.nonce, auth_payload, None)
            writer.write(len(encrypted_auth).to_bytes(4, "big") + encrypted_auth)
            await writer.drain()

            hdr = await reader.readexactly(4)
            enc_resp = await reader.readexactly(int.from_bytes(hdr, "big"))
            auth_resp = orjson.loads(self.aesgcm.decrypt(self.nonce, enc_resp, None))

            if auth_resp.get("status") != "OK":
                raise DBClientError(auth_resp.get("msg", "Authentication failed"), code=401, details=auth_resp)

            command_payload = orjson.dumps(command)
            encrypted_command = self.aesgcm.encrypt(self.nonce, command_payload, None)
            writer.write(len(encrypted_command).to_bytes(4, "big") + encrypted_command)
            await writer.drain()

            hdr = await reader.readexactly(4)
            enc_data = await reader.readexactly(int.from_bytes(hdr, "big"))
            return orjson.loads(self.aesgcm.decrypt(self.nonce, enc_data, None))

        except asyncio.IncompleteReadError:
            raise DBClientError("Verbindung unterbrochen oder ungültige Antwort vom Server", code=408)
        except ConnectionRefusedError:
            raise DBClientError("Verbindung zum Server konnte nicht aufgebaut werden", code=503)
        except Exception as e:
            raise DBClientError("Unerwarteter Fehler", details={"exception": str(e)})
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def call(self, modul: str, funktion: str, data: list) -> dict:
        return await self.send_command({
            "action": "call",
            "modul": modul,
            "funktion": funktion,
            "data": data
        })
