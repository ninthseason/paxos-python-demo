# paxos-python-demo

Paxos 共识机制的 python 简易实现

环境需求:

```shell
pip install fastapi[all]
pip install httpx
```

# 这样玩：

```shell
uvicorn main:app --port 8000
uvicorn main:app --port 8001
uvicorn main:app --port 8002
```

开三个节点

```shell
http://127.0.0.1:8000/get 获取value
http://127.0.0.1:8000/set/{value} 发起proposal
```

只有一轮共识过程，所以 value 一经固定无法更改。
