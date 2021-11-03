import asyncio
import websockets
import json
import sys
import argparse
import logging
import time


class Manager:
    # class member
    workers = dict()  # id : (websocket,type,max_service_num)
    port = 9876
    clients = dict()  # id : (websocket,type)
    worker_clients = dict()  # worker id : [client id...]
    client_worker = dict()  # client id : worker id

    def __init__(self):
        logging.info("Manager init")

    async def register_worker(self, worker_id, worker, path: str):
        logging.info("register a connected worker")
        if worker_id in self.workers.keys():
            logging.error("register a connected worker that has been registered")
            exit(-1)
        info = path.strip('/').split('/')
        cap = int(info[1])
        logging.info(f"register worker type: {info[0]}, cap: {cap}")
        self.workers[worker_id] = (worker, info[0], cap)
        assert (worker_id not in self.worker_clients.keys())
        self.worker_clients[worker_id] = list()

    def register_client(self,client_id,client,path:str):
        logging.info("register a connected client")
        if client_id in self.clients.keys():
            logging.error("register a connected client that has been registered")
            exit(-1)
        type_name = path.strip('/')
        logging.info(f"register client type: {type_name}")
        self.clients[client_id] = (client,type_name)
        assert (client_id not in self.client_worker.keys())

    def get_worker_type(self, worker_id):
        return self.workers[worker_id][1]

    def get_worker_cap(self, worker_id):
        return self.workers[worker_id][2]

    def get_client_type(self, client_id):
        return self.clients[client_id][1]

    async def assign_worker_to_client(self, client_id:str)->bool:
        """

        :param client_id:
        :return: no return
        """
        logging.info("assign a worker from self.workers to a client")

        for item in self.worker_clients.items():
            worker_id = item[0]
            cur_work_num = len(item[1])
            if self.get_client_type(client_id) == self.get_worker_type(
                    worker_id) and cur_work_num < self.get_worker_cap(worker_id):
                self.worker_clients[worker_id].append(client_id)
                self.client_worker[client_id] = worker_id
                logging.info(f"assign worker {worker_id} to client {client_id}")
                return True
        return False


    def delete_worker(self, worker_id):
        logging.info(f"delete worker {worker_id}")
        self.workers.pop(worker_id)
        self.worker_clients.pop(worker_id)
        for item in self.client_worker.items():
            if item[1] == worker_id:
                self.client_worker.pop(item[0])
                break

    def delete_client(self, client_id):
        logging.info(f"delete client {client_id}")
        if client_id in self.clients:
            self.clients.pop(client_id)
        if client_id in self.client_worker.keys():
            self.client_worker.pop(client_id)
        for item in self.worker_clients.items():
            if client_id in item[1]:
                self.worker_clients[item[0]].remove(client_id)
                break

    def get_worker_by_clientID(self, client_id:str):
        """
        get client id by searching self.worker_clients, if not found return None
        should call this function because worker maybe deleted at runtime
        :param client_id: WebSocket's id
        :return: worker WebSocket's id
        """
        logging.info(f"get worker by client {client_id}")
        for idx in self.client_worker.keys():
            if idx == client_id:
                return self.workers[self.client_worker[idx]][0]
        logging.error(f"not find worker by client id {client_id}")
        return None

    async def listen(self):
        logging.info("Manager::run start")
        async with websockets.serve(self.process, "localhost", self.port,
                                    ping_interval=60,ping_timeout=60):
            await asyncio.Future()

    async def handle_client_connect(self, websocket, path):
        logging.info("Manager::handle_client_connect")
        logging.info(f"client connection id: {websocket.id}")

        try:
            client_id = websocket.id
            self.register_client(client_id, websocket, path)
            if not await self.assign_worker_to_client(client_id):
                await websocket.send("No valid worker")
                await websocket.close()
                self.delete_client(websocket.id)
                return
            worker = self.get_worker_by_clientID(client_id)
            while True:
                client_msg = await websocket.recv()
                logging.info(f"clinet message: {client_msg}")
                await worker.send(client_msg)
                frame = await worker.recv()
                await websocket.send(frame)
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"websocket connection {websocket.id} closed")
        finally:
            self.delete_client(websocket.id)

    async def handle_worker_message(self,websocket):
        logging.info("Manager::handle_worker_message")

    async def handle_worker_connect(self, websocket, path):
        logging.info("Manager::handle_worker_connect")
        logging.info(f"worker connection id: {websocket.id}")
        await self.register_worker(websocket.id,websocket,path)
        await websocket.wait_closed()
        self.delete_worker(websocket.id)

    async def process(self, websocket, path):
        logging.info("Manager::process new connection")
        if path[0:4] == '/rpc':
            logging.info("client connect to manager")
            await self.handle_client_connect(websocket, path[4:])
        elif path[0:7] == '/worker':
            logging.info("worker connect to mananger")
            await self.handle_worker_connect(websocket, path[7:])


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
    logging.info("Program start logging...")

    parser = argparse.ArgumentParser(description="Manager configure options")
    parser.add_argument("--print_string", help="print the supplied argument")
    args = parser.parse_args()
    logging.info(args.print_string)
    manager = Manager()
    asyncio.run(manager.listen())
