import asyncio
import websockets
import json
import sys
import argparse
import logging
import time
import mpack

class Manager:
    # class member
    workers = dict()  # id : (websocket,type,max_service_num)
    port = 9876
    clients = dict()  # id : (websocket,type)
    req_count = 0
    
    def __init__(self):
        logging.info("Manager init")
        self.lock = asyncio.Lock()
    def register_worker(self, worker_id, worker, path: str):
        logging.info("register a connected worker")
        if worker_id in self.workers.keys():
            logging.error("register a connected worker that has been registered, this will remove old connection!")
            slef.workers.pop(worker_id)
            
        info = path.strip('/').split('/')
        cap = int(info[1])
        logging.info(f"register worker type: {info[0]}, cap: {cap}")
        self.workers[worker_id] = (worker, info[0], cap)


    def register_client(self,client_id,client,path:str):
        logging.info("register a connected client")
        if client_id in self.clients.keys():
            logging.error("register a connected client that has been registered, this will remove old connection!")
            self.clients.pop(clinet_id)
        type_name = path.strip('/')
        logging.info(f"register client type: {type_name}")
        self.clients[client_id] = (client,type_name)
        

    def get_worker_type(self, worker_id):
        return self.workers[worker_id][1]

    def get_worker_cap(self, worker_id):
        return self.workers[worker_id][2]

    def get_client_type(self, client_id):
        return self.clients[client_id][1]

    async def assign_worker(self):
        cur_worker_num = len(self.workers)
        if cur_worker_num == 0:
            return None
        await self.lock.acquire()
        try:
            idx = self.req_count % cur_worker_num
            i = 0
            for id in self.workers.keys():
                if i == idx:
                    return id
                else:
                    i += 1
            self.req_count += 1
        finally:
            self.lock.release()

    def delete_worker(self, worker_id):
        logging.info(f"delete worker {worker_id}")
        if worker_id in self.workers.keys():
            self.workers.pop(worker_id)

    def delete_client(self, client_id):
        logging.info(f"delete client {client_id}")
        if client_id in self.clients.keys():
            self.clients.pop(client_id)

    async def listen(self):
        logging.info("Manager::run start")
        async with websockets.serve(self.process, "0.0.0.0", self.port, ping_interval=60, ping_timeout=60):
            await asyncio.Future()

    async def handle_client_connect(self, websocket, path):
        logging.info("Manager::handle_client_connect")
        logging.info(f"client connection id: {websocket.id}")

        try:
            client_id = websocket.id
            self.register_client(client_id, websocket, path)

            while True:
                logging.info(f"{client_id} start recv client msg")
                client_msg = await websocket.recv()
                client_req = mpack.unpack(client_msg)

                # add client-id in message which send to worker
                client_req["id"]=str(client_id)

                
                logging.info(f"{client_id} send client msg to worker")
                #find a availible worker to process
                worker_id = await self.assign_worker()
                if worker_id == None:
                    logging.info("no availiable worker")
                    await websocket.send(mpack.pack({"error":"no availiable worker"}))
                else:
                    worker = self.workers[worker_id][0]
                    await worker.send(mpack.pack(client_req))
  
                logging.info(f"{client_id} finish one task")

        except websockets.exceptions.ConnectionClosed:
            logging.info(f"client websocket connection {websocket.id} closed")
        finally:
            self.delete_client(websocket.id)

    async def handle_worker_connect(self, websocket, path):
        logging.info("Manager::handle_worker_connect")
        logging.info(f"worker connection id: {websocket.id}")
        
        try:
            self.register_worker(websocket.id,websocket,path)
        
            while True:
                worker_msg = await websocket.recv()
                res = mpack.unpack(worker_msg)
                if "error" in res:
                    logging.error("worker respond error")
                    continue
                msg_id = res["id"]
                for id in self.clients.keys():
                    if str(id) == msg_id:
                        client = self.clients[id][0]
                        await client.send(worker_msg)

        except websockets.exceptions.ConnectionClosed:
            logging.info(f"worker websocket connection {websocket.id} closed")
        finally:
            self.delete_worker(websocket.id)

    async def process(self, websocket, path):
        logging.info("Manager::process new connection")
        if path[0:4] == '/rpc':
            logging.info("client connect to manager")
            await self.handle_client_connect(websocket, path[4:])
        elif path[0:7] == '/worker':
            logging.info("worker connect to mananger")
            await self.handle_worker_connect(websocket, path[7:])
        else:
            logging.error("error url for connection!")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    logging.info("Program start logging...")

    parser = argparse.ArgumentParser(description="Manager configure options")
    parser.add_argument("--print_string", help="print the supplied argument")
    args = parser.parse_args()
    logging.info(args.print_string)
    manager = Manager()
    asyncio.run(manager.listen())
