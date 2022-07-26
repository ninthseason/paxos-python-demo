import asyncio
import time

import pydantic
import httpx
from fastapi import FastAPI

app = FastAPI()


class Node:
    def __init__(self):
        self.proposal = {}  # current accepted proposal
        self.acceptors = ['http://127.0.0.1:8000', 'http://127.0.0.1:8001', 'http://127.0.0.1:8002']  # all acceptors
        # self.acceptors = ['http://127.0.0.1:8000']
        self.last_n: float = 0.0  # the highest index in prepare phase

    async def new_proposal(self, value) -> bool:
        """
        create a proposal

        :param value: the value to consensus
        :return: is action successful
        """
        proposal = {
            'index': time.time(),
            'value': value
        }

        return await self.prepare(proposal)

    async def prepare(self, proposal: dict) -> bool:
        """
        prepare action by proposer in prepare phase

        :param proposal: proposal to prepare
        :return: is action successful
        """
        receives = []
        for acceptor in self.acceptors:
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(acceptor + "/promise", json=proposal, timeout=5)
                except httpx.ReadTimeout:
                    continue
                receives.append(res.json())
        accepted_proposals = []
        for receive in receives:
            if not receive['promised']:
                continue
            else:
                accepted_proposals.append(receive['proposal'])
        if len(accepted_proposals) >= len(self.acceptors) / 2:
            highest_index = 0
            highest_value = ""
            for accepted_proposal in accepted_proposals:
                if accepted_proposal.get('index', -1) > highest_index:
                    highest_index = accepted_proposal.get('index', -1)
                    highest_value = accepted_proposal['value']
            if highest_value != "":
                proposal['value'] = highest_value
            return await self.accept(proposal)
        return False

    async def accept(self, proposal) -> bool:
        """
        accept action by proposer in accept phase

        :param proposal: proposal to accept
        :return: is action successful
        """
        receives = []
        for acceptor in self.acceptors:
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(acceptor + "/accept", json=proposal, timeout=5)
                except httpx.ReadTimeout:
                    continue
                receives.append(res.json())
        accepted_number = 0
        for receive in receives:
            if receive['accepted']:
                accepted_number += 1
        if accepted_number >= len(self.acceptors) / 2:
            self.proposal = proposal
            return True
        return False


node = Node()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/get")
async def getter():
    """
    get finally proposal

    :return:
    """
    return node.proposal


@app.get("/set/{value}")
async def setter(value: str):
    """
    create a proposal

    :param value:
    :return:
    """
    success = False
    wait_time = 1
    while not success:
        success = await node.new_proposal(value)
        wait_time *= 2
        await asyncio.sleep(wait_time)
    return {'msg': 'success!'}


class Proposal(pydantic.BaseModel):
    index: float
    value: str


@app.post("/promise")
async def promise(proposal: Proposal):
    """
    promise action by acceptor in prepare phase

    :param proposal:
    :return:
    """
    index = proposal.index
    if index <= node.last_n:
        return {'promised': False, 'proposal': {}}
    node.last_n = index
    return {'promised': True, 'proposal': node.proposal}


@app.post("/accept")
async def promise(proposal: Proposal):
    """
    accept action by acceptor in accept phase

    :param proposal:
    :return:
    """
    index = proposal.index
    if index < node.last_n:
        return {'accepted': False}
    node.proposal = proposal
    return {'accepted': True}


@app.post("/test")
async def test(proposal: Proposal):
    return proposal
