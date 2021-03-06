import sys
import json
import select
from multiprocessing import Process, Pipe

from asciinema.stdout import Stdout
import asciinema.debug as debug # DEBUG

NEED_INSTALL = True
try:
    import asyncio
    import websockets
    NEED_INSTALL = False
except ImportError:
    pass


class Stream(Stdout):

    def __init__(self, max_wait=None):
        super().__init__(max_wait)
        if NEED_INSTALL:
            print('You need to install asyncio and websockets to stream')
            print('pip3 install asyncio websockets')
            sys.exit(1)
        self.ws_url = 'ws://localhost:5555/ws'
        parent_conn, child_conn = Pipe()
        self.websocket_child = Process(target=start_websocket, args=(child_conn, self.ws_url,))
        self.websocket_child.start()
        self.websocket = parent_conn

    def write(self, data):
        text = self.decoder.decode(data)
        if text:
            delay = round(self._increment_elapsed_time(), 6)
            self.send_frame({
                'frame': {
                    'delay': delay,
                    'text': text
                    }
                })

        return len(data)

    def close(self):
        debug.write(b'\n\nCLOSING\n') # DEBUG
        self.websocket.send('SHUTDOWN')
        self.websocket.close()
        self.websocket_child.join()

    def send_frame(self, frame):
        self.websocket.send(json.dumps(frame, ensure_ascii=False, indent=2))

def start_websocket(child_conn, ws_url):
    async def hello():
        async with websockets.connect(ws_url, origin='localhost') as websocket:
            while True:
                ready = select.select([child_conn], [], [child_conn], 5.0)
                if len(ready[0]) > 0:
                    try:
                        msg = ready[0][0].recv()
                        if msg == 'SHUTDOWN':
                            debug.write(b'GOT SHUTDOWN\n') # DEBUG
                            break
                        else:
                            # debug.write(msg) # DEBUG
                            # debug.write(b'\n') # DEBUG
                            await websocket.send(msg)
                            await websocket.recv()
                    except Exception as e:
                        debug.write(str(e)) # DEBUG
                        break
                elif len(ready[2]) > 0:
                    debug.write(b'SERVER CLOSED WS') # DEBUG
                    break
            debug.write(b'CLOSING CHILD CONN\n') # DEBUG
            child_conn.close()
            debug.write(b'CHILD CONN CLOSED\n') # DEBUG
            debug.write(b'CLOSING WEBSOCKET\n') # DEBUG
            websocket.close()
            debug.write(b'WEBSOCKET CLOSED\n') # DEBUG
        debug.write(b'\nEND OF HELLO\n') # DEBUG

    asyncio.get_event_loop().run_until_complete(hello())
    debug.write(b'\n\nEVENT LOOP COMPLETE\n') # DEBUG
